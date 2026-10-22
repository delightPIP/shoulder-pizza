"""조각 시각이 된 사용자에게 알림 메일을 보낸다 (SPEC 10장). GitHub Actions에서 5분마다 실행한다.

실행: python -m mailer.send_due            (보내기)
      python -m mailer.send_due --dry-run  (보내지 않고 대상 수만 출력)

공개 저장소의 Actions 로그는 누구나 볼 수 있으므로 메일 주소를 출력하지 않는다.
"""
import argparse
import smtplib
import sys
from datetime import datetime, timedelta
from email.message import EmailMessage
from urllib.parse import urlencode

from core.config import get_secret, local_store_path, service_account_info
from core.progress import EATEN, GAVE_UP, REST, SNOOZED
from core.schedule import TZ, slice_datetimes
from core.store import make_store

GRACE = timedelta(minutes=60)  # 조각 시각에서 이만큼 지나면 보내지 않는다
SNOOZE = timedelta(minutes=30)
SLICE = "slice"


def due_mails(user: dict, logs: list[dict], sent: set, now: datetime) -> list[dict]:
    """지금 보낼 메일 목록. 어제 시작한 시간대(자정 넘김)도 함께 본다."""
    out = []
    uid = user["uid"]
    for day in (now.date() - timedelta(days=1), now.date()):
        iso = day.isoformat()
        dts = slice_datetimes(day, user["window_start"], user["window_end"], int(user["slices"]))
        day_logs = [r for r in logs if r["date"] == iso]
        if any(r["status"] == GAVE_UP for r in day_logs):
            continue  # "오늘은 더 이상 못하겠어요"를 누른 날은 더 보내지 않는다
        done ={int(r["slice_idx"]) for r in day_logs if r["status"] in (EATEN, REST)}
        for i, dt in enumerate(dts):
            if i not in done and dt <= now < dt + GRACE and (uid, iso, str(i), SLICE) not in sent:
                out.append({"day": day, "idx": i, "n": len(dts), "at": dt, "kind": SLICE})
        for r in day_logs:  # "30분 뒤 다시"를 누른 조각
            i = int(r["slice_idx"])
            if r["status"] != SNOOZED or i in done or not r.get("ts"):
                continue
            at = datetime.fromisoformat(r["ts"]) + SNOOZE
            kind = f"snooze@{r['ts']}"
            if at <= now < at + GRACE and (uid, iso, str(i), kind) not in sent:
                out.append({"day": day, "idx": i, "n": len(dts), "at": at, "kind": kind})
    return out


def links(app_url: str, uid: str, idx: int) -> tuple[str, str]:
    base = app_url.rstrip("/")
    return f"{base}/?{urlencode({'u': uid, 'slice': idx})}", f"{base}/?{urlencode({'unsub': uid})}"


def build_message(user: dict, mail: dict, app_url: str, sender: str) -> EmailMessage:
    open_url, unsub_url = links(app_url, user["uid"], mail["idx"])
    n, i = mail["n"], mail["idx"] + 1
    if mail["kind"] == SLICE:
        subject = f"🍕 {i}번째 조각 먹을 시간이에요"
        lead = f"오늘 피자 {n}조각 중 {i}번째 조각이 따끈하게 나왔어요."
    else:
        subject = f"🍕 30분 지났어요, {i}번째 조각 어때요?"
        lead = f"아까 미뤄 둔 {i}번째 조각이 기다리고 있어요."
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = f"어깨PIZZA <{sender}>"
    msg["To"] = user["email"]
    msg["List-Unsubscribe"] = f"<{unsub_url}>"
    msg.set_content(
        f"{lead}\n\n한 조각 먹으러 가기: {open_url}\n\n"
        "의료 조언이 아닙니다. 통증이 있으면 멈추세요.\n"
        f"알림을 그만 받으려면: {unsub_url}\n"
    )
    msg.add_alternative(
        f"""<div style="font-family:sans-serif;max-width:480px;margin:auto;color:#3b2a20">
<h2 style="color:#c2410c">어깨PIZZA</h2>
<p>{lead}</p>
<p><a href="{open_url}" style="display:inline-block;background:#c2410c;color:#fff;padding:12px 22px;
border-radius:999px;text-decoration:none">한 조각 먹으러 가기</a></p>
<p style="font-size:12px;color:#8a7766">의료 조언이 아닙니다. 통증이 있으면 멈추세요.<br>
알림은 몇 분 늦을 수 있어요. <a href="{unsub_url}" style="color:#8a7766">알림 그만 받기</a></p></div>""",
        subtype="html",
    )
    return msg


def _parse(argv):
    parser = argparse.ArgumentParser(description="어깨PIZZA 알림 메일 발송")
    parser.add_argument("--dry-run", action="store_true", help="보내지 않고 대상 수만 출력")
    parser.add_argument("--local", action="store_true", help="Google Sheets 대신 로컬 저장소 사용 (개발용)")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse(argv)
    sheet_id, account = get_secret("GOOGLE_SHEET_ID"), service_account_info()
    sender, password = get_secret("GMAIL_ADDRESS"), get_secret("GMAIL_APP_PASSWORD")
    app_url = get_secret("APP_URL", "http://localhost:8501")
    if not args.local and not (sheet_id and account):
        print("Google Sheets 비밀값이 없어 건너뜁니다 (GOOGLE_SHEET_ID, GOOGLE_SERVICE_ACCOUNT_JSON).")
        return 0
    if not args.dry_run and not (sender and password):
        print("Gmail 비밀값이 없어 건너뜁니다 (GMAIL_ADDRESS, GMAIL_APP_PASSWORD).")
        return 0
    if "localhost" in app_url:
        print("경고: APP_URL이 localhost예요. 메일 링크가 배포 주소를 가리키도록 바꿔 주세요.")

    store = make_store(None if args.local else sheet_id, None if args.local else account, local_store_path())
    now = datetime.now(TZ)
    sent = store.sent_keys()
    targets = []
    for user in store.active_users():
        logs = store.logs(user["uid"], since=now.date() - timedelta(days=1))
        targets += [(user, mail) for mail in due_mails(user, logs, sent, now)]
    print(f"{now:%Y-%m-%d %H:%M} 보낼 메일 {len(targets)}통")
    if args.dry_run or not targets:
        return 0

    failures = 0
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=20) as smtp:
        smtp.login(sender, password)
        for user, mail in targets:
            try:
                smtp.send_message(build_message(user, mail, app_url, sender))
            except smtplib.SMTPException as e:
                failures += 1
                print(f"발송 실패 uid={user['uid'][:6]}… ({type(e).__name__})")
                continue
            store.add_send({"uid": user["uid"], "date": mail["day"].isoformat(), "slice_idx": mail["idx"],
                            "kind": mail["kind"], "sent_at": datetime.now(TZ).isoformat(timespec="seconds")})
    print(f"보냄 {len(targets) - failures}통, 실패 {failures}통")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())

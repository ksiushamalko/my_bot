import threading
from datetime import datetime, timedelta

from database import send, query


def schedule_notify(chat_id, did, deadline_at):
    def job():
        rows = query("SELECT title, category, is_done, deadline_at FROM deadlines WHERE id=?", (did,))
        if not rows:
            return
        title, cat, is_done, dt_s = rows[0]
        if is_done:
            return
        dt = datetime.strptime(dt_s, "%Y-%m-%d %H:%M:%S")
        now = datetime.now()
        if now >= dt:
            send(chat_id, f"Дедлайн наступил!\n\n{title}\n{cat}\n\nНе забудь отметить выполнение")
        elif now >= dt - timedelta(hours=1):
            send(chat_id, f"Срочно!\n\n{title}\nОсталось меньше часа!\nСрок: {dt.strftime('%d.%m.%Y %H:%M')}")
        elif now >= dt - timedelta(hours=24):
            send(chat_id, f"Напоминание!\n\n{title}\n{cat}\nОсталось меньше 24 часов!\nСрок: {dt.strftime('%d.%m.%Y %H:%M')}")

    for sec in (0, 3600, 24 * 3600):
        delay = max(1, (deadline_at - datetime.now()).total_seconds() - sec)
        t = threading.Timer(delay, job)
        t.daemon = True
        t.start()

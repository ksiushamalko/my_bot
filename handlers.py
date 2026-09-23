from datetime import datetime
from database import (
    send,
    edit,
    answer_cb,
    delete_msg,
    get_user,
    query,
    execute,
)
from keyboards import main_kb, cancel_kb, categories_kb, actions_kb
from scheduler import schedule_notify
state = {}
def get_state(tg_id):
    if tg_id not in state:
        state[tg_id] = {"step": None, "data": {}}
    return state[tg_id]


def reset_state(tg_id):
    state[tg_id] = {"step": None, "data": {}}


def handle_message(msg):
    chat_id = msg["chat"]["id"]
    tg_id = msg["from"]["id"]
    username = msg["from"].get("username")
    text = msg.get("text", "").strip()

    get_user(tg_id, username)
    st = get_state(tg_id)

    if text == "/start":
        reset_state(tg_id)
        name = msg["from"].get("first_name", "")
        send(chat_id, f"Привет, {name}!\nЯ бот-напоминалка о дедлайнах.", main_kb)
        return

    if text in ("/help", "Помощь"):
        send(chat_id, help_text(), main_kb)
        return

    if st["step"] == "title":
        handle_title(chat_id, tg_id, text, st)
        return

    if st["step"] == "deadline":
        handle_deadline_input(chat_id, tg_id, text, st)
        return

    if text == "Добавить дедлайн":
        reset_state(tg_id)
        state[tg_id]["step"] = "title"
        send(chat_id, "Введи название задачи:", cancel_kb)
        return

    if text == "Мои дедлайны":
        show_active(chat_id, tg_id)
        return

    if text == "Выполненные":
        show_done(chat_id, tg_id)
        return

    if text == "Статистика":
        show_stats(chat_id, tg_id)
        return

    if text == "Сохранить все":
        show_all(chat_id, tg_id)
        return

    if text == "Очистить все":
        clear_all(chat_id, tg_id)
        return


def help_text():
    return (
        "Как пользоваться:\n\n"
        "Добавить дедлайн - создай новую задачу\n"
        "Мои дедлайны - список активных\n"
        "Выполненные - архив\n"
        "Статистика - сводка\n"
        "Сохранить все - выгрузить задачи\n"
        "Очистить все - удалить задачи\n\n"
        "Формат даты: ДД.ММ.ГГГГ ЧЧ:ММ\n"
        "Пример: 25.12.2025 18:00"
    )


def handle_title(chat_id, tg_id, text, st):
    if text == "Отмена":
        reset_state(tg_id)
        send(chat_id, "Отменено.", main_kb)
        return

    if len(text) > 200:
        send(chat_id, "Слишком длинное название (макс. 200).")
        return

    st["data"]["title"] = text
    st["step"] = "category"
    send(chat_id, "Выбери категорию:", categories_kb)


def handle_deadline_input(chat_id, tg_id, text, st):
    if text == "Отмена":
        reset_state(tg_id)
        send(chat_id, "Отменено.", main_kb)
        return

    try:
        dt = datetime.strptime(text, "%d.%m.%Y %H:%M")
    except ValueError:
        send(chat_id, "Неверный формат. Попробуй так: 25.12.2025 18:00")
        return

    if dt <= datetime.now():
        send(chat_id, "Дата должна быть в будущем.")
        return

    uid = get_user(tg_id)
    did = execute(
        "INSERT INTO deadlines(user_id, title, category, deadline_at) VALUES(?,?,?,?)",
        (
            uid,
            st["data"]["title"],
            st["data"]["category"],
            dt.strftime("%Y-%m-%d %H:%M:%S"),
        ),
    )
    schedule_notify(chat_id, did, dt)
    reset_state(tg_id)

    answer = (
        "Дедлайн добавлен!\n\n"
        f"{st['data']['title']}\n"
        f"{st['data']['category']}\n"
        f"{dt.strftime('%d.%m.%Y %H:%M')}"
    )
    send(chat_id, answer, main_kb)


def show_active(chat_id, tg_id):
    uid = get_user(tg_id)
    rows = query(
        "SELECT id, title, category, deadline_at "
        "FROM deadlines "
        "WHERE user_id=? AND is_done=0 "
        "ORDER BY deadline_at",
        (uid,),
    )

    if not rows:
        send(chat_id, "Активных дедлайнов нет!", main_kb)
        return

    for did, title, cat, dt_s in rows:
        dt = datetime.strptime(dt_s, "%Y-%m-%d %H:%M:%S")
        left = dt - datetime.now()
        text = (
            f"{title}\n"
            f"{cat}\n"
            f"{dt.strftime('%d.%m.%Y %H:%M')}\n"
            f"Осталось: {left.days} д. {left.seconds // 3600} ч."
        )
        send(chat_id, text, actions_kb(did))


def show_done(chat_id, tg_id):
    uid = get_user(tg_id)
    rows = query(
        "SELECT title, deadline_at "
        "FROM deadlines "
        "WHERE user_id=? AND is_done=1 "
        "ORDER BY deadline_at DESC "
        "LIMIT 20",
        (uid,),
    )

    if not rows:
        send(chat_id, "Пока ничего не выполнено.", main_kb)
        return

    lines = ["Выполненные:\n"]
    for title, dt_s in rows:
        lines.append(f"• {title} ({dt_s[:10]})")
    send(chat_id, "\n".join(lines), main_kb)


def show_stats(chat_id, tg_id):
    uid = get_user(tg_id)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    total = query(
        "SELECT COUNT(*) FROM deadlines WHERE user_id=?",
        (uid,),
    )[0][0]

    done = query(
        "SELECT COUNT(*) FROM deadlines WHERE user_id=? AND is_done=1",
        (uid,),
    )[0][0]

    overdue = query(
        "SELECT COUNT(*) FROM deadlines "
        "WHERE user_id=? AND is_done=0 AND deadline_at<?",
        (uid, now),
    )[0][0]

    text = (
        "Статистика:\n\n"
        f"Всего: {total}\n"
        f"Выполнено: {done}\n"
        f"Просрочено: {overdue}\n"
        f"В работе: {total - done - overdue}"
    )
    send(chat_id, text, main_kb)


def show_all(chat_id, tg_id):
    uid = get_user(tg_id)
    rows = query(
        "SELECT title, category, deadline_at, is_done "
        "FROM deadlines "
        "WHERE user_id=? "
        "ORDER BY deadline_at",
        (uid,),
    )

    if not rows:
        send(chat_id, "Нет задач для сохранения.", main_kb)
        return

    lines = ["Все задачи:\n"]
    for title, cat, dt_s, done in rows:
        status = "выполнено" if done else "активно"
        lines.append(f"{title} | {cat} | {dt_s[:16]} | {status}")
    send(chat_id, "\n".join(lines), main_kb)


def clear_all(chat_id, tg_id):
    uid = get_user(tg_id)
    execute("DELETE FROM deadlines WHERE user_id=?", (uid,))
    send(chat_id, "Все задачи удалены.", main_kb)


def handle_callback(cb):
    chat_id = cb["message"]["chat"]["id"]
    message_id = cb["message"]["message_id"]
    tg_id = cb["from"]["id"]
    data = cb["data"]

    st = get_state(tg_id)

    if data.startswith("cat:"):
        on_category(chat_id, message_id, tg_id, data, st, cb)
        return

    if data.startswith("done:"):
        on_done(chat_id, message_id, cb, data)
        return

    if data.startswith("del:"):
        on_delete(chat_id, message_id, cb, data)
        return


def on_category(chat_id, message_id, tg_id, data, st, cb):
    if st["step"] != "category":
        return

    cat = data.split(":", 1)[1]
    st["data"]["category"] = cat
    st["step"] = "deadline"

    edit(chat_id, message_id, f"Категория: {cat}")

    ask = (
        "Введи дату и время дедлайна в формате ДД.ММ.ГГГГ ЧЧ:ММ:\n"
        "Пример: 25.12.2025 18:00"
    )
    send(chat_id, ask, cancel_kb)
    answer_cb(cb["id"])


def on_done(chat_id, message_id, cb, data):
    did = int(data.split(":")[1])
    execute("UPDATE deadlines SET is_done=1 WHERE id=?", (did,))
    old = cb["message"]["text"]
    edit(chat_id, message_id, old + "\n\nВыполнено!")
    answer_cb(cb["id"], "Отмечено")


def on_delete(chat_id, message_id, cb, data):
    did = int(data.split(":")[1])
    execute("DELETE FROM deadlines WHERE id=?", (did,))
    delete_msg(chat_id, message_id)
    answer_cb(cb["id"], "Удалено")

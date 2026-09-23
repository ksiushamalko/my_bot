import json
import urllib.request
import urllib.parse
import sqlite3

from config import API, DB


def api(method, **params):
    data = urllib.parse.urlencode(params).encode()
    url = API + "/" + method
    req = urllib.request.Request(url, data=data)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            answer = r.read().decode()
            return json.loads(answer)
    except Exception as e:
        print("ошибка запроса:", e)
        return None


def send(chat_id, text, keyboard=None):
    params = {"chat_id": chat_id, "text": text}
    if keyboard:
        params["reply_markup"] = json.dumps(keyboard, ensure_ascii=False)
    api("sendMessage", **params)


def edit(chat_id, message_id, text, keyboard=None):
    params = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text,
    }
    if keyboard:
        params["reply_markup"] = json.dumps(keyboard, ensure_ascii=False)
    api("editMessageText", **params)


def answer_cb(cb_id, text=""):
    api("answerCallbackQuery", callback_query_id=cb_id, text=text)


def delete_msg(chat_id, message_id):
    api("deleteMessage", chat_id=chat_id, message_id=message_id)


def init_db():
    con = sqlite3.connect(DB)

    con.execute(
        "CREATE TABLE IF NOT EXISTS users ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, "
        "tg_id INTEGER UNIQUE, "
        "username TEXT)"
    )

    con.execute(
        "CREATE TABLE IF NOT EXISTS deadlines ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, "
        "user_id INTEGER, "
        "title TEXT, "
        "category TEXT, "
        "deadline_at TEXT, "
        "is_done INTEGER DEFAULT 0)"
    )

    con.commit()
    con.close()


def get_user(tg_id, username=None):
    con = sqlite3.connect(DB)
    cur = con.cursor()

    cur.execute("SELECT id FROM users WHERE tg_id=?", (tg_id,))
    row = cur.fetchone()

    if row:
        uid = row[0]
    else:
        cur.execute(
            "INSERT INTO users(tg_id, username) VALUES(?,?)",
            (tg_id, username),
        )
        con.commit()
        uid = cur.lastrowid

    con.close()
    return uid


def query(sql, params=()):
    con = sqlite3.connect(DB)
    cur = con.cursor()
    cur.execute(sql, params)
    rows = cur.fetchall()
    con.close()
    return rows


def execute(sql, params=()):
    con = sqlite3.connect(DB)
    cur = con.cursor()
    cur.execute(sql, params)
    con.commit()
    last = cur.lastrowid
    con.close()
    return last

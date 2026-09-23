import json
import time
import urllib.request
import urllib.parse

from config import API
from database import init_db
from handlers import handle_message, handle_callback


def poll():
    offset = None
    while True:
        params = {"timeout": 30}
        if offset is not None:
            params["offset"] = offset
        try:
            req = urllib.request.Request(f"{API}/getUpdates", data=urllib.parse.urlencode(params).encode())
            with urllib.request.urlopen(req, timeout=60) as r:
                data = json.loads(r.read().decode())
        except Exception as e:
            print("poll error:", e)
            time.sleep(2)
            continue
        if not data.get("ok"):
            time.sleep(1)
            continue
        for upd in data["result"]:
            offset = upd["update_id"] + 1
            try:
                if "message" in upd:
                    handle_message(upd["message"])
                elif "callback_query" in upd:
                    handle_callback(upd["callback_query"])
            except Exception as e:
                print("handler error:", e)


init_db()
print("Бот запущен...")
poll()

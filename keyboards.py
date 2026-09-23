main_kb = {
    "keyboard": [
        [{"text": "Добавить дедлайн"}],
        [{"text": "Мои дедлайны"}, {"text": "Выполненные"}],
        [{"text": "Статистика"}, {"text": "Помощь"}],
        [{"text": "Сохранить все"}, {"text": "Очистить все"}],
    ],
    "resize_keyboard": True,
}

cancel_kb = {
    "keyboard": [[{"text": "Отмена"}]],
    "resize_keyboard": True,
}

categories_kb = {
    "inline_keyboard": [
        [{"text": "Учёба", "callback_data": "cat:Учёба"}],
        [{"text": "Работа", "callback_data": "cat:Работа"}],
        [{"text": "Личное", "callback_data": "cat:Личное"}],
        [{"text": "Покупки", "callback_data": "cat:Покупки"}],
        [{"text": "Другое", "callback_data": "cat:Другое"}],
    ]
}


def actions_kb(did):
    return {"inline_keyboard": [
        [{"text": "Выполнено", "callback_data": f"done:{did}"}],
        [{"text": "Удалить", "callback_data": f"del:{did}"}],
    ]}

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton


main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Добавить дедлайн")],
        [KeyboardButton(text="Мои дедлайны"), KeyboardButton(text="Выполненные")],
        [KeyboardButton(text="Статистика"), KeyboardButton(text="Помощь")],
    ],
    resize_keyboard=True,
)

cancel_kb = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="Отмена")]],
    resize_keyboard=True,
)

categories_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="Учёба", callback_data="cat:Учёба")],
        [InlineKeyboardButton(text="Работа", callback_data="cat:Работа")],
        [InlineKeyboardButton(text="Личное", callback_data="cat:Личное")],
        [InlineKeyboardButton(text="Покупки", callback_data="cat:Покупки")],
        [InlineKeyboardButton(text="Другое", callback_data="cat:Другое")],
    ]
)
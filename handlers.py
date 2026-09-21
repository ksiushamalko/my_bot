from datetime import datetime
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery
from sqlalchemy import select, func
from database import async_session
from models import User, Deadline
from keyboards import main_kb, cancel_kb, categories_kb, deadline_actions
router = Router()
class AddDeadline(StatesGroup):
    title = State()
    category = State()
    deadline = State()
@router.message(Command("start"))
async def cmd_start(message: Message):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == message.from_user.id))
        if not user:
            user = User(tg_id=message.from_user.id, username=message.from_user.username)
            session.add(user)
            await session.commit()

    await message.answer(
        f"Привет, {message.from_user.first_name}!\n"
        "Я бот-напоминалка о дедлайнах.\n"
        "Буду присылать уведомления за 24 часа, за 1 час и в момент срока.\n\n"
        "Выбери действие:",
        reply_markup=main_kb,
    )
@router.message(F.text == "Помощь")
@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "Как пользоваться:\n\n"
        "Добавить дедлайн - создай новую задачу\n"
        "Мои дедлайны - список активных\n"
        "Выполненные - архив\n"
        "Статистика - сколько всего, выполнено, просрочено\n\n"
        "Формат даты: `ДД.ММ.ГГГГ ЧЧ:ММ`\n"
        "Пример: `25.12.2025 18:00`",
        parse_mode="Markdown",
        reply_markup=main_kb,
    )

@router.message(F.text == "Добавить дедлайн")
async def add_start(message: Message, state: FSMContext):
    await state.set_state(AddDeadline.title)
    await message.answer("Введи название задачи:", reply_markup=cancel_kb)


@router.message(AddDeadline.title, F.text == "Отмена")
@router.message(AddDeadline.category, F.text == "Отмена")
@router.message(AddDeadline.deadline, F.text == "Отмена")
async def cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Отменено.", reply_markup=main_kb)


@router.message(AddDeadline.title)
async def add_title(message: Message, state: FSMContext):
    if len(message.text) > 200:
        return await message.answer("Слишком длинное название (макс. 200).")
    await state.update_data(title=message.text)
    await state.set_state(AddDeadline.category)
    await message.answer("Выбери категорию:", reply_markup=categories_kb)

@router.callback_query(AddDeadline.category, F.data.startswith("cat:"))
async def add_category(callback: CallbackQuery, state: FSMContext):
    category = callback.data.split(":", 1)[1]
    await state.update_data(category=category)
    await state.set_state(AddDeadline.deadline)
    await callback.message.edit_text(f"Категория: {category}")
    await callback.message.answer(
        "Введи дату и время дедлайна в формате `ДД.ММ.ГГГГ ЧЧ:ММ`:\n"
        "Пример: `25.12.2025 18:00`",
        parse_mode="Markdown",
        reply_markup=cancel_kb,
    )
    await callback.answer()


@router.message(AddDeadline.deadline)
async def add_deadline(message: Message, state: FSMContext):
    try:
        dt = datetime.strptime(message.text.strip(), "%d.%m.%Y %H:%M")
    except ValueError:
        return await message.answer(
            "Неверный формат. Попробуй так: `25.12.2025 18:00`",
            parse_mode="Markdown",
        )

    if dt <= datetime.now():
        return await message.answer("Дата должна быть в будущем.")

    data = await state.get_data()
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == message.from_user.id))
        deadline = Deadline(
            user_id=user.id,
            title=data["title"],
            category=data["category"],
            deadline_at=dt,
        )
        session.add(deadline)
        await session.commit()

    await state.clear()
    await message.answer(
        f"Дедлайн добавлен!\n\n"
        f"{data['title']}\n"
        f"{data['category']}\n"
        f"{dt.strftime('%d.%m.%Y %H:%M')}",
        reply_markup=main_kb,
    )

@router.message(F.text == "Мои дедлайны")
async def list_active(message: Message):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == message.from_user.id))
        result = await session.scalars(
            select(Deadline)
            .where(Deadline.user_id == user.id, Deadline.is_done == False)
            .order_by(Deadline.deadline_at)
        )
        deadlines = result.all()
    if not deadlines:
        return await message.answer("🎉 Активных дедлайнов нет!", reply_markup=main_kb)
    for d in deadlines:
        left = d.deadline_at - datetime.now()
        days = left.days
        hours = left.seconds // 3600
        text = (
            f"{d.title}\n"
            f"{d.category}\n"
            f"{d.deadline_at.strftime('%d.%m.%Y %H:%M')}\n"
            f"Осталось: {days} д. {hours} ч."
        )
        await message.answer(text, parse_mode="Markdown", reply_markup=deadline_actions(d.id))
@router.message(F.text == "Выполненные")
async def list_done(message: Message):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == message.from_user.id))
        result = await session.scalars(
            select(Deadline)
            .where(Deadline.user_id == user.id, Deadline.is_done == True)
            .order_by(Deadline.deadline_at.desc())
            .limit(20)
        )
        deadlines = result.all()

    if not deadlines:
        return await message.answer("Пока ничего не выполнено.", reply_markup=main_kb)

    text = "Выполненные:\n\n" + "\n".join(
        f"• {d.title} ({d.deadline_at.strftime('%d.%m.%Y')})" for d in deadlines
    )
    await message.answer(text, parse_mode="Markdown", reply_markup=main_kb)

@router.message(F.text == "Статистика")
async def stats(message: Message):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == message.from_user.id))
        total = await session.scalar(
            select(func.count()).select_from(Deadline).where(Deadline.user_id == user.id)
        )
        done = await session.scalar(
            select(func.count()).select_from(Deadline)
            .where(Deadline.user_id == user.id, Deadline.is_done == True)
        )
        overdue = await session.scalar(
            select(func.count()).select_from(Deadline)
            .where(
                Deadline.user_id == user.id,
                Deadline.is_done == False,
                Deadline.deadline_at < datetime.now(),
            )
        )

    await message.answer(
        f"Статистика:\n\n"
        f"Всего: {total}\n"
        f"Выполнено: {done}\n"
        f"Просрочено: {overdue}\n"
        f"В работе: {total - done - overdue}",
        parse_mode="Markdown",
        reply_markup=main_kb,
    )


# ---------- Callback: выполнено / удалить ----------
@router.callback_query(F.data.startswith("done:"))
async def mark_done(callback: CallbackQuery):
    d_id = int(callback.data.split(":")[1])
    async with async_session() as session:
        d = await session.get(Deadline, d_id)
        if d:
            d.is_done = True
            await session.commit()
    await callback.message.edit_text(callback.message.text + "\n\n✅ Выполнено!")
    await callback.answer("Отмечено как выполненное")


@router.callback_query(F.data.startswith("del:"))
async def delete_deadline(callback: CallbackQuery):
    d_id = int(callback.data.split(":")[1])
    async with async_session() as session:
        d = await session.get(Deadline, d_id)
        if d:
            await session.delete(d)
            await session.commit()
    await callback.message.delete()
    await callback.answer("Удалено")
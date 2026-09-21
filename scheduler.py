from datetime import datetime, timedelta
from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import select

from database import async_session
from models import Deadline, User


async def check_deadlines(bot: Bot):
    now = datetime.now()
    async with async_session() as session:
        result = await session.scalars(
            select(Deadline).where(
                Deadline.is_done == False,
                Deadline.notified_24h == False,
                Deadline.deadline_at <= now + timedelta(hours=24),
                Deadline.deadline_at > now + timedelta(hours=1),
            )
        )
        for d in result.all():
            user = await session.get(User, d.user_id)
            try:
                await bot.send_message(
                    user.tg_id,
                    f"Напоминание!\n\n"
                    f"{d.title}\n"
                    f"{d.category}\n"
                    f"Осталось меньше 24 часов!\n"
                    f"Срок: {d.deadline_at.strftime('%d.%m.%Y %H:%M')}",
                    parse_mode="Markdown",
                )
            except Exception as e:
                print(f"Ошибка отправки: {e}")
            d.notified_24h = True
        await session.commit()

        result = await session.scalars(
            select(Deadline).where(
                Deadline.is_done == False,
                Deadline.notified_1h == False,
                Deadline.deadline_at <= now + timedelta(hours=1),
                Deadline.deadline_at > now,
            )
        )
        for d in result.all():
            user = await session.get(User, d.user_id)
            try:
                await bot.send_message(
                    user.tg_id,
                    f"Срочно!\n\n"
                    f"{d.title}\n"
                    f"Осталось меньше часа!\n"
                    f"Срок: {d.deadline_at.strftime('%d.%m.%Y %H:%M')}",
                    parse_mode="Markdown",
                )
            except Exception as e:
                print(f"Ошибка отправки: {e}")
            d.notified_1h = True
        await session.commit()

        result = await session.scalars(
            select(Deadline).where(
                Deadline.is_done == False,
                Deadline.notified_now == False,
                Deadline.deadline_at <= now,
            )
        )
        for d in result.all():
            user = await session.get(User, d.user_id)
            try:
                await bot.send_message(
                    user.tg_id,
                    f"Дедлайн наступил!\n\n"
                    f"{d.title}\n"
                    f"{d.category}\n\n"
                    f"Не забудь отметить выполнение",
                    parse_mode="Markdown",
                )
            except Exception as e:
                print(f"Ошибка отправки: {e}")
            d.notified_now = True
        await session.commit()


def setup_scheduler(bot: Bot) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone="Europe/Moscow")
    scheduler.add_job(check_deadlines, "interval", minutes=1, args=[bot])
    return scheduler
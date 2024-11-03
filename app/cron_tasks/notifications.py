import asyncio
import os

import app.database.orm_query as rq

from datetime import datetime, timedelta
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from dotenv import load_dotenv
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode


load_dotenv()


async def send_message(bot, user_id, message):
    await bot.send_message(user_id, message)


async def check_subscriptions(bot):
    tomorrow = datetime.now().date() + timedelta(days=1)
    subscriptions = await rq.orm_get_subscribers()
    admins = await rq.get_all_admins()

    for subscription in subscriptions:
        if subscription.is_subscribed and subscription.end_subscription_date and subscription.end_subscription_date.date() == tomorrow:
            user = await rq.orm_get_user(subscription.user_id)

            await send_message(bot, subscription.user_id, "У вашої підписки залишився один день.")

            for admin in admins:
                await send_message(bot, admin.tg_id,
                                   f"У користувача {f'@{user.name}' if user.name else '-'} (<code>{subscription.user_id}</code>) залишився один день підписки.")


async def main():
    bot = Bot(token=os.getenv('BOT_TOKEN'), default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await check_subscriptions(bot)
    await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())

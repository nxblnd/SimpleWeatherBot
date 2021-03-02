import os
from typing import Any

from aiogram import Bot, Dispatcher, executor, types
import requests

bot = Bot(os.getenv('BOT_TOKEN'))
dispatcher = Dispatcher(bot)


def main():
    executor.start_polling(dispatcher, skip_updates=True)


@dispatcher.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.message):
    await message.answer("I'm simple weather bot. Powered by OpenWeatherMap data.\n"
                         "Type /help to get this message again.")


@dispatcher.message_handler(lambda message: not message.is_command())
async def not_command(message: types.message):
    await message.answer("I don't understand this, try using some commands")


def get_weather(city: str) -> list[dict[str, Any]]:
    OWM_LINK = 'https://api.openweathermap.org/data/2.5/weather'
    r = requests.get(OWM_LINK, params={'q': city, 'appid': os.getenv('OWM_TOKEN'), 'units': 'metric'})
    return r.json()


if __name__ == '__main__':
    main()

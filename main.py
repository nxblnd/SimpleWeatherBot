import os
import sqlite3
import sys
import time
from typing import Callable

from aiogram import Bot, Dispatcher, executor, types

from OwmExceptions import OwmNoResponse, OwmLocationException
from OwmRequests import get_weather, get_city_coords, get_city_by_coords, JSON

BOT_TOKEN = os.getenv('BOT_TOKEN', 'no_token_found')
if BOT_TOKEN == 'no_token_found':
    sys.exit("No bot token was found in ENV. Set 'BOT_TOKEN' variable to your token from @BotFather")
bot = Bot(BOT_TOKEN)
dispatcher = Dispatcher(bot)
db = sqlite3.connect('/var/database/database.sqlite')


def main():
    executor.start_polling(dispatcher, skip_updates=True)


@dispatcher.message_handler(commands='start')
async def send_hello(message: types.message):
    try:
        db.execute('insert into users (chat_id) values (:chat_id)', {'chat_id': message.chat.id})
    except sqlite3.IntegrityError:
        await message.answer("If you want to get help, use /help command")
    else:
        db.commit()
        await message.answer("I'm simple weather bot. Powered by OpenWeatherMap data.\n"
                             "Type /help to get list of commands")


@dispatcher.message_handler(commands='help')
async def send_help(message: types.message):
    await message.answer("Use /current command with city name to get current weather.\n"
                         "Use /day command with city name to get forecast for a day.\n"
                         "Use /week command with city name to get forecast for a week\n"
                         "Type /help to get this message again.")


@dispatcher.message_handler(commands='current')
async def send_current_weather(message: types.message):
    await process_message(message, build_current_weather_msg)


@dispatcher.message_handler(commands='day')
async def send_day_weather(message: types.message):
    await process_message(message, build_day_weather_msg)


@dispatcher.message_handler(commands='week')
async def send_day_weather(message: types.message):
    await process_message(message, build_week_weather_msg)


async def process_message(message: types.message, answer_builder: Callable[[JSON, str], str]):
    _, city = message.get_full_command()
    try:
        coords = await get_city_coords(city)
        weather = await get_weather(coords['lat'], coords['lon'])
    except OwmLocationException:
        await message.answer('This location could not be found in OpenWeatherMap database')
    except OwmNoResponse:
        await message.answer("No connection to OpenWeatherMap")
    else:
        city = await get_city_by_coords(weather['lat'], weather['lon'])
        await message.answer(answer_builder(weather, city))


def build_current_weather_msg(weather: JSON, city: str) -> str:
    weather = weather['current']
    return f"Current weather in {city} is {weather['weather'][0]['main']}\n" \
           f"Temperature is {round(weather['temp'])}℃ " \
           f"(feels like {round(weather['feels_like'])}℃)\n" \
           f"Atmospheric pressure is {weather['pressure']} kPa\n" \
           f"Air humidity is {weather['humidity']}%\n" \
           f"Wind direction is {weather['wind_deg']}° with {weather['wind_speed']} m/s speed\n" \
           f"Cloudiness is {weather['clouds']}%"


def build_day_weather_msg(weather: JSON, city: str) -> str:
    return f"Weather in {city} in next 24 hours:\n" + \
           ''.join(f"• {time.strftime('%H:00', time.gmtime(hour['dt'] + weather['timezone_offset']))} "
                   f"{hour['weather'][0]['main']},\n"
                   f"  {round(hour['temp'])}℃ (feels like {round(hour['feels_like'])}℃).\n"
                   f"  Probability of precipitation {round(hour['pop'] * 100)}%\n" for hour in weather['hourly'][:24])


def build_week_weather_msg(weather: JSON, city: str) -> str:
    return f"Weather in {city} in next 7 days:\n" + \
           ''.join(f"• {time.strftime('%Y-%m-%d', time.gmtime(day['dt'] + weather['timezone_offset']))} "
                   f"{day['weather'][0]['main']},\n"
                   f"  at day {round(day['temp']['day'])}℃ (feels like {round(day['feels_like']['day'])}℃),\n"
                   f"  at night {round(day['temp']['night'])}℃ (feels like {round(day['feels_like']['night'])}℃),\n"
                   f"  Probability of precipitation {round(day['pop'] * 100)}%\n" for day in weather['daily'])


@dispatcher.message_handler(lambda message: message.is_command())
async def unknown_command(message: types.message):
    await message.answer("This command is incorrect, type /help to get list of commands")


@dispatcher.message_handler(lambda message: not message.is_command())
async def not_command(message: types.message):
    await message.answer("I don't understand this, try using some commands")


if __name__ == '__main__':
    main()

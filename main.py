import os
import sqlite3
import sys
import time
from typing import Callable

from aiogram import Bot, Dispatcher, executor, types

from OwmExceptions import OwmNoResponse, OwmLocationException
from OwmRequests import get_weather, get_city_coords, get_city_by_coords, JSON, get_city_data, OWM_WEATHER_CONDITIONS

BOT_TOKEN = os.getenv('BOT_TOKEN', 'no_token_found')
if BOT_TOKEN == 'no_token_found':
    sys.exit("No bot token was found in ENV. Set 'BOT_TOKEN' variable to your token from @BotFather")
bot = Bot(BOT_TOKEN)
dispatcher = Dispatcher(bot)
db = sqlite3.connect('/var/db/weatherbot/database.sqlite')


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
    await message.answer("I can work in two modes: for your city and for every other: \n"
                         "• Tell me your home city with /set command, and use /current, /day or /week "
                         "commands to get current weather, weather for a day or week respectfully.\n"
                         "• Use /current, /day or /week commands with some city name to get weather for that city.\n"
                         "Type /help to get this message again.")


@dispatcher.message_handler(commands='set')
async def set_default_city(message: types.message):
    _, city = message.get_full_command()
    if not city:
        await message.answer("Please provide city name")
        return

    city_data = await get_city_data(city)

    try:
        cursor = db.cursor()
        cursor.execute('insert into cities (name, lat, lon) values (:name, :lat, :lon)', {'name': city_data['name'],
                                                                                          'lat': city_data['lat'],
                                                                                          'lon': city_data['lon']})
        cursor.execute('update users set default_city_id = :id where chat_id = :chat_id', {'chat_id': message.chat.id,
                                                                                           'id': cursor.lastrowid})
    except sqlite3.IntegrityError:
        db.execute('update users '
                   'set default_city_id = (select id as city_id from cities where name = :city_name) '
                   'where chat_id = :chat_id', {'chat_id': message.chat.id, 'city_name': city_data['name']})

    await message.answer(f"Your city is set to {city_data['name']}")
    db.commit()


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
    # I don't know, how it happened, but this shit exists and i kinda don't know what to do with it.
    # TLDR: if city name is provided, go to OWM, else get coords from DB. Then try to get weather and respond to user.

    _, city = message.get_full_command()
    if city:
        try:
            coords = await get_city_coords(city)
        except OwmLocationException:
            await message.answer('This location could not be found in OpenWeatherMap database')
            return
    else:
        try:
            coords = dict(zip(('name', 'lat', 'lon'),
                              db.execute('select name, lat, lon '
                                         '   from users join cities '
                                         '   where chat_id = :chat_id and '
                                         '         cities.id = default_city_id;',
                                         {'chat_id': message.chat.id}).fetchone()))
        except TypeError:
            await message.answer('To use this command like this you should tell me your city first with /set command.\n'
                                 'Or try using this command with some city name')
            return

    try:
        weather = await get_weather(coords['lat'], coords['lon'])
    except OwmNoResponse:
        await message.answer("No connection to OpenWeatherMap")
    else:
        city = await get_city_by_coords(weather['lat'], weather['lon'])
        await message.answer(answer_builder(weather, city))


def build_current_weather_msg(weather: JSON, city: str) -> str:
    weather = weather['current']
    wind_deg = weather['wind_deg']
    if 315 + 22.5 <= wind_deg or 0 <= wind_deg < 22.5:
        wind = 'N'
    elif 0 + 22.5 <= wind_deg < 45 + 22.5:
        wind = 'NE'
    elif 45 + 22.5 <= wind_deg < 90 + 22.5:
        wind = 'E'
    elif 90 + 22.5 <= wind_deg < 135 + 22.5:
        wind = 'SE'
    elif 135 + 22.5 <= wind_deg < 180 + 22.5:
        wind = 'S'
    elif 180 + 22.5 <= wind_deg < 225 + 22.5:
        wind = 'SW'
    elif 225 + 22.5 <= wind_deg < 270 + 22.5:
        wind = 'W'
    elif 270 + 22.5 <= wind_deg < 315 + 22.5:
        wind = 'NW'
    else:
        wind = '***COMPASS IS BROKEN***'
    return f"Current weather in {city} is {weather['weather'][0]['main']} " \
           f"{OWM_WEATHER_CONDITIONS[weather['weather'][0]['icon']]}\n" \
           f"🌡 Temperature is {round(weather['temp'])}℃ " \
           f"(feels like {round(weather['feels_like'])}℃)\n" \
           f"🌀 Atmospheric pressure is {weather['pressure']} kPa\n" \
           f"💧 Air humidity is {weather['humidity']}%\n" \
           f"🧭 Wind direction is {wind} with 🌬 {weather['wind_speed']} m/s speed\n" \
           f"☁ Cloudiness is {weather['clouds']}%"


def build_day_weather_msg(weather: JSON, city: str) -> str:
    hours = []
    for hour in weather['hourly'][:24]:
        pop = round(hour['pop'] * 100)
        if 0 <= pop < 33:
            pop_sign = '🌂'
        elif 33 <= pop < 66:
            pop_sign = '☂'
        else:
            pop_sign = '☔'
        hours.append(f"• {time.strftime('%H:00', time.gmtime(hour['dt'] + weather['timezone_offset']))} "
                     f"{hour['weather'][0]['main']} {OWM_WEATHER_CONDITIONS[hour['weather'][0]['icon']]}, "
                     f" 🌡 {round(hour['temp'])}℃ (feels like {round(hour['feels_like'])}℃)."
                     f" {pop_sign}{round(hour['pop'] * 100)}%\n")
    return f"Weather in {city} in next 24 hours:\n" + ''.join(hours)


def build_week_weather_msg(weather: JSON, city: str) -> str:
    days = []
    for day in weather['daily']:
        pop = round(day['pop'] * 100)
        if 0 <= pop < 33:
            pop_sign = '🌂'
        elif 33 <= pop < 66:
            pop_sign = '☂'
        else:
            pop_sign = '☔'
        days.append(f"• {time.strftime('%Y-%m-%d, %a,', time.gmtime(day['dt'] + weather['timezone_offset']))} "
                    f"{day['weather'][0]['main']} {OWM_WEATHER_CONDITIONS[day['weather'][0]['icon']]},\n"
                    f" 🌞 at day 🌡 {round(day['temp']['day'])}℃ (feels like {round(day['feels_like']['day'])}℃),\n"
                    f" 🌜 at night 🌡 {round(day['temp']['night'])}℃ (feels like {round(day['feels_like']['night'])}℃),\n"
                    f" {pop_sign} {round(day['pop'] * 100)}%\n\n")
    return f"Weather in {city} in next 7 days:\n" + ''.join(days)


@dispatcher.message_handler(lambda message: message.is_command())
async def unknown_command(message: types.message):
    await message.answer("This command is incorrect, type /help to get list of commands")


@dispatcher.message_handler(lambda message: not message.is_command())
async def not_command(message: types.message):
    await message.answer("I don't understand this, try using some commands")


if __name__ == '__main__':
    main()

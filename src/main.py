import asyncio
import os
import sqlite3
import sys
import time

from aiogram import Bot, Dispatcher, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import StatesGroup, State

from OwmRequests import JSON, OWM_WEATHER_CONDITIONS

from bot import commands

BOT_TOKEN = os.getenv('BOT_TOKEN', 'no_token_found')
if not BOT_TOKEN:
    sys.exit("No bot token was found in ENV. Set 'BOT_TOKEN' variable to your token from @BotFather")
aiogram_bot = Bot(BOT_TOKEN)

db = sqlite3.connect('/var/db/weatherbot/database.sqlite')
with open('DatabaseSetup.sql', 'r') as setup_script:
    database_setup = setup_script.read()
    db.executescript(database_setup)
    db.commit()


async def main():
    dispatcher = Dispatcher(aiogram_bot, storage=MemoryStorage())
    commands.register_handlers(dispatcher)
    await commands.set_commands(aiogram_bot)
    await dispatcher.skip_updates()
    await dispatcher.start_polling()


class CitySetter(StatesGroup):
    city_name = State()


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
        hours.append(f"{time.strftime('%H:00', time.gmtime(hour['dt'] + weather['timezone_offset']))} "
                     f"{hour['weather'][0]['main']} {OWM_WEATHER_CONDITIONS[hour['weather'][0]['icon']]},\n"
                     f" 🌡 {round(hour['temp'])}℃ (feels like {round(hour['feels_like'])}℃)."
                     f" {pop_sign}{round(hour['pop'] * 100)}%\n\n")
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


if __name__ == '__main__':
    asyncio.run(main())

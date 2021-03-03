import os
import time
from typing import Any

from aiogram import Bot, Dispatcher, executor, types

from OwmExceptions import OwmNoResponse, OwmLocationException
from OwmRequests import get_weather, get_city_coords, get_all_weather, get_city_by_coords

bot = Bot(os.getenv('BOT_TOKEN'))
dispatcher = Dispatcher(bot)

def main():
    executor.start_polling(dispatcher, skip_updates=True)


@dispatcher.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.message):
    await message.answer("I'm simple weather bot. Powered by OpenWeatherMap data.\n\n"
                         "Use /current command with city name to get current weather.\n"
                         "Type /help to get this message again.")


@dispatcher.message_handler(commands='current')
async def send_current_weather(message: types.message):
    _, city = message.get_full_command()
    try:
        coords = await get_city_coords(city)
        weather = await get_weather(coords['lat'], coords['lon'])
    except OwmLocationException:
        await message.answer('This location could not be found in OpenWeatherMap database')
    except OwmNoResponse:
        await message.answer("No connection to OpenWeatherMap")
    else:
        await message.answer(build_current_weather_msg(weather))


@dispatcher.message_handler(commands='day')
async def send_day_weather(message: types.message):
    _, city = message.get_full_command()
    try:
        coords = await get_city_coords(city)
        weather = await get_all_weather(coords['lat'], coords['lon'])
    except OwmLocationException:
        await message.answer('This location could not be found in OpenWeatherMap database')
    except OwmNoResponse:
        await message.answer("No connection to OpenWeatherMap")
    else:
        city = await get_city_by_coords(weather['lat'], weather['lon'])
        await message.answer(build_day_weather_msg(weather, city))


def build_current_weather_msg(weather: dict[str, Any]) -> str:
    return f"Current weather in {weather['name']} is {weather['weather'][0]['main']}\n" \
           f"Temperature is {round(weather['main']['temp'])}℃ " \
           f"(feels like {round(weather['main']['feels_like'])}℃)\n" \
           f"Atmospheric pressure is {weather['main']['pressure']} kPa\n" \
           f"Air humidity is {weather['main']['humidity']}%\n" \
           f"Wind direction is {weather['wind']['deg']}° with {weather['wind']['speed']} m/s speed\n" \
           f"Cloudiness is {weather['clouds']['all']}%"


def build_day_weather_msg(weather: dict[str, Any], city: str) -> str:
    return ''.join(f"• {time.strftime('%H:00', time.gmtime(hour['dt'] + weather['timezone_offset']))} "
                   f"{hour['weather'][0]['main']},\n"
                   f"  {round(hour['temp'])}℃ (feels like {round(hour['feels_like'])}℃).\n"
                   f"  Probability of precipitation {round(hour['pop'] * 100)}%\n" for hour in weather['hourly'][:24])


@dispatcher.message_handler(lambda message: message.is_command())
async def unknown_command(message: types.message):
    await message.answer("This command is incorrect, type /help to get list of commands")


@dispatcher.message_handler(lambda message: not message.is_command())
async def not_command(message: types.message):
    await message.answer("I don't understand this, try using some commands")


if __name__ == '__main__':
    main()

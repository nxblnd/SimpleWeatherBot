import os
from typing import Any

from aiogram import Bot, Dispatcher, executor, types
import requests

bot = Bot(os.getenv('BOT_TOKEN'))
dispatcher = Dispatcher(bot)

OWM_links = {'current': 'https://api.openweathermap.org/data/2.5/weather',
             'geocoding': 'http://api.openweathermap.org/geo/1.0/direct'}


def main():
    executor.start_polling(dispatcher, skip_updates=True)


@dispatcher.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.message):
    await message.answer("I'm simple weather bot. Powered by OpenWeatherMap data.\n"
                         "Type /help to get this message again.")


@dispatcher.message_handler(commands='current')
async def send_current_weather(message: types.message):
    _, city = message.get_full_command()
    coords = get_city_coords(city)
    weather = get_weather(coords['lat'], coords['lon'])
    await message.answer(build_current_weather_msg(weather))


def build_current_weather_msg(weather: dict[str, Any]) -> str:
    return f"Current weather in {weather['name']} is {weather['weather'][0]['main']}\n" \
           f"Temperature is {round(weather['main']['temp'])}℃ (feels like {round(weather['main']['feels_like'])}℃)\n" \
           f"Atmospheric pressure is {weather['main']['pressure']} kPa\n" \
           f"Air humidity is {weather['main']['humidity']}%\n" \
           f"Wind direction is {weather['wind']['deg']}° with {weather['wind']['speed']} m/s speed\n" \
           f"Cloudiness is {weather['clouds']['all']}%"


def get_city_coords(city: str) -> dict[str, float]:
    r = requests.get(OWM_links['geocoding'], params={'q': city,
                                                     'appid': os.getenv('OWM_TOKEN'),
                                                     'limit': 1})
    geodata = r.json()
    return {'lat': geodata[0]['lat'], 'lon': geodata[0]['lon']}


@dispatcher.message_handler(lambda message: not message.is_command())
async def not_command(message: types.message):
    await message.answer("I don't understand this, try using some commands")


def get_weather(lat: float, lon: float) -> dict[str, Any]:
    r = requests.get(OWM_links['current'], params={'lat': lat,
                                                   'lon': lon,
                                                   'appid': os.getenv('OWM_TOKEN'),
                                                   'units': 'metric'})
    return r.json()


if __name__ == '__main__':
    main()

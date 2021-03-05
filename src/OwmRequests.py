import os
import sys
from typing import NewType, Any

import requests

from OwmExceptions import OwmNoResponse, OwmLocationException

OWM_links = {'current': 'https://api.openweathermap.org/data/2.5/weather',
             'geocoding': 'http://api.openweathermap.org/geo/1.0/direct',
             'reverse_geocoding': 'http://api.openweathermap.org/geo/1.0/reverse',
             'onecall': 'https://api.openweathermap.org/data/2.5/onecall'}

JSON = NewType('JSON', dict[str, Any])

OWM_TOKEN = os.getenv('OWM_TOKEN', 'no_token_found')
if OWM_TOKEN == 'no_token_found':
    sys.exit("No OpenWeatherMap token was found in ENV. "
             "Set 'OWM_TOKEN' variable to your token from OpenWeatherMap account")

OWM_WEATHER_CONDITIONS = {
    '01d': '☀', '01n': '🌙',
    '02d': '🌤', '02n': '🌤',
    '03d': '🌥', '03n': '🌥',
    '04d': '☁', '04n': '☁',
    '09d': '🌧', '09n': '🌧',
    '10d': '🌧', '10n': '🌧',
    '11d': '⛈', '11n': '⛈',
    '13d': '❄', '13n': '❄',
    '50d': '🌫', '50n': '🌫',
}


async def get_city_coords(city: str) -> dict[str, float]:
    geodata = await get_city_data(city)
    return {'lat': geodata['lat'], 'lon': geodata['lon']}


async def get_city_data(city: str) -> JSON:
    r = requests.get(OWM_links['geocoding'], params={'q': city,
                                                     'appid': OWM_TOKEN,
                                                     'limit': 1})
    if r.status_code != requests.codes.OK:
        raise OwmNoResponse
    geodata = r.json()
    if not geodata:
        raise OwmLocationException('City not found')
    return geodata[0]


async def get_city_by_coords(lat: float, lon: float) -> str:
    r = requests.get(OWM_links['reverse_geocoding'], params={'lat': lat,
                                                             'lon': lon,
                                                             'appid': OWM_TOKEN,
                                                             'limit': 1})
    if r.status_code != requests.codes.OK:
        raise OwmNoResponse
    return r.json()[0]['name']


async def get_weather(lat: float, lon: float) -> JSON:
    r = requests.get(OWM_links['onecall'], params={'lat': lat,
                                                   'lon': lon,
                                                   'appid': OWM_TOKEN,
                                                   'units': 'metric',
                                                   'exclude': ['minutely', 'alerts']})
    if r.status_code != requests.codes.OK:
        raise OwmNoResponse
    return r.json()

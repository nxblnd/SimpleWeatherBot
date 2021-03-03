import os
from typing import Any

import requests

from OwmExceptions import OwmNoResponse, OwmLocationException

OWM_links = {'current': 'https://api.openweathermap.org/data/2.5/weather',
             'geocoding': 'http://api.openweathermap.org/geo/1.0/direct'}


async def get_weather(lat: float, lon: float) -> dict[str, Any]:
    r = requests.get(OWM_links['current'], params={'lat': lat,
                                                   'lon': lon,
                                                   'appid': os.getenv('OWM_TOKEN'),
                                                   'units': 'metric'})
    if r.status_code != requests.codes.OK:
        raise OwmNoResponse
    return r.json()


async def get_city_coords(city: str) -> dict[str, float]:
    r = requests.get(OWM_links['geocoding'], params={'q': city,
                                                     'appid': os.getenv('OWM_TOKEN'),
                                                     'limit': 1})
    if r.status_code != requests.codes.OK:
        raise OwmNoResponse
    geodata = r.json()
    if not geodata:
        raise OwmLocationException('City not found')
    return {'lat': geodata[0]['lat'], 'lon': geodata[0]['lon']}

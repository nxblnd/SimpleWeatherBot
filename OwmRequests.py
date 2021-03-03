import os

import requests

from OwmExceptions import OwmNoResponse, OwmLocationException

OWM_links = {'current': 'https://api.openweathermap.org/data/2.5/weather',
             'geocoding': 'http://api.openweathermap.org/geo/1.0/direct',
             'reverse_geocoding': 'http://api.openweathermap.org/geo/1.0/reverse',
             'onecall': 'https://api.openweathermap.org/data/2.5/onecall'}


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


async def get_city_by_coords(lat: float, lon: float) -> str:
    r = requests.get(OWM_links['reverse_geocoding'], params={'lat': lat,
                                                             'lon': lon,
                                                             'appid': os.getenv('OWM_TOKEN'),
                                                             'limit': 1})
    if r.status_code != requests.codes.OK:
        raise OwmNoResponse
    return r.json()[0]['name']


async def get_weather(lat: float, lon: float) -> dict[str, float]:
    r = requests.get(OWM_links['onecall'], params={'lat': lat,
                                                   'lon': lon,
                                                   'appid': os.getenv('OWM_TOKEN'),
                                                   'units': 'metric',
                                                   'exclude': ['minutely', 'alerts']})
    if r.status_code != requests.codes.OK:
        raise OwmNoResponse
    return r.json()

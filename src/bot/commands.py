import sqlite3
from typing import Callable

from aiogram import types, Dispatcher, Bot
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import CommandStart, CommandHelp
from aiogram.types import BotCommand, base, fields

from src.OwmExceptions import OwmLocationException, OwmNoResponse
from src.OwmRequests import get_city_data, JSON, get_city_coords, get_weather, get_city_by_coords

from src.main import CitySetter, db, build_current_weather_msg, build_day_weather_msg, \
    build_week_weather_msg


# @dispatcher.message_handler(commands='start')
async def send_hello(message: types.message):
    await message.answer("I'm simple weather bot. Powered by OpenWeatherMap data.\n"
                         "Type /help to get list of commands")


# @dispatcher.message_handler(commands='help')
async def send_help(message: types.message):
    await message.answer("I can work in two modes: for your city and for every other: \n"
                         "• Tell me your home city with /set command, and use /current, /day or /week "
                         "commands to get current weather, weather for a day or week respectfully.\n"
                         "• Use /current, /day or /week commands with some city name to get weather for that city.\n"
                         "Type /help to get this message again.")


# @dispatcher.message_handler(commands='set')
async def set_default_city(message: types.message):
    await CitySetter.city_name.set()
    await message.answer('What is your city?')


# @dispatcher.message_handler(state=CitySetter.city_name)
async def process_city_name(message: types.Message, state: FSMContext):
    try:
        city_data = await get_city_data(message.text)
    except OwmLocationException:
        await message.answer('This location could not be found in OpenWeatherMap database')
        return
    try:
        db.execute('insert into users (user_id) values (:user_id)', {'user_id': message.from_user.id})
    except sqlite3.IntegrityError:
        pass
    try:
        cursor = db.cursor()
        cursor.execute('insert into cities (name, lat, lon) values (:name, :lat, :lon)', {'name': city_data['name'],
                                                                                          'lat': city_data['lat'],
                                                                                          'lon': city_data['lon']})
        cursor.execute('update users '
                       'set default_city_id = :id '
                       'where user_id = :user_id', {'user_id': message.from_user.id, 'id': cursor.lastrowid})
    except sqlite3.IntegrityError:
        db.execute('update users '
                   'set default_city_id = (select id as city_id from cities where name = :city_name) '
                   'where user_id = :user_id', {'user_id': message.from_user.id, 'city_name': city_data['name']})

    await message.answer(f"Your city is set to {city_data['name']}")
    db.commit()
    await state.finish()


# @dispatcher.message_handler(commands='cancel', state='*')
async def cancel_handler(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return
    await state.finish()
    await message.answer('Action cancelled')


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
                                         '   where user_id = :user_id and '
                                         '         cities.id = default_city_id;',
                                         {'user_id': message.from_user.id}).fetchone()))
        except TypeError:
            await message.answer('To use this command like this you should tell me your city first with /set command.\n'
                                 'Or try using this command with some city name.\n'
                                 'If you are using bot in group chat, do not forget to initialize bot with /start.')
            return

    try:
        weather = await get_weather(coords['lat'], coords['lon'])
    except OwmNoResponse:
        await message.answer("No connection to OpenWeatherMap")
    else:
        city = await get_city_by_coords(weather['lat'], weather['lon'])
        await message.answer(answer_builder(weather, city))


# @dispatcher.message_handler(lambda message: message.is_command())
async def unknown_command(message: types.message):
    await message.answer("This command is incorrect, type /help to get list of commands")


# @dispatcher.message_handler(lambda message: not message.is_command())
async def not_command(message: types.message):
    if message.reply_to_message:
        return
    await message.answer("I don't understand this, try using some commands")


# @dispatcher.message_handler(commands='current')
async def send_current_weather(message: types.message):
    await process_message(message, build_current_weather_msg)


# @dispatcher.message_handler(commands='day')
async def send_day_weather(message: types.message):
    await process_message(message, build_day_weather_msg)


# @dispatcher.message_handler(commands='week')
async def send_week_weather(message: types.message):
    await process_message(message, build_week_weather_msg)


def register_handlers(dispatcher: Dispatcher):
    dispatcher.register_message_handler(send_hello, CommandStart())
    dispatcher.register_message_handler(send_help, CommandHelp())


async def set_commands(bot: Bot):
    en_commands = [
        BotCommand(command="/current", description="Get current weather"),
    ]
    await bot.set_my_commands(en_commands)

    ru_commands = [
        BotCommand(command="/current", description="Получить погоду сейчас"),
    ]
    await bot.set_my_commands(ru_commands, language_code="ru")

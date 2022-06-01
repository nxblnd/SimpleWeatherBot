from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup


class LocationDialog(StatesGroup):
    location = State()


async def set_location(message: types.Message):
    await LocationDialog.next()
    await message.answer('Send me your location (you can share location on mobile, send city name or coordinates)')


async def parse_location(message: types.Message, state: FSMContext):
    if message.text:
        await message.answer(f'Your location is {message.text}')
    elif message.location:
        await message.answer(f'Your location is {message.location.latitude}, {message.location.longitude}')
    else:
        await message.answer("Can't understand your location. Try again or /cancel")
        return
    await state.finish()


def register_location_handler(dispatcher: Dispatcher):
    dispatcher.register_message_handler(set_location, commands=['location'])
    dispatcher.register_message_handler(parse_location, state=LocationDialog.location,
                                        content_types=[types.ContentType.TEXT, types.ContentType.LOCATION])

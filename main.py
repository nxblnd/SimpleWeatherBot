import os
from aiogram import Bot, Dispatcher, executor, types

bot = Bot(os.getenv('BOT_TOKEN'))
dispatcher = Dispatcher(bot)


def main():
    executor.start_polling(dispatcher, skip_updates=True)


@dispatcher.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.message):
    await message.answer("I'm simple weather bot. Powered by OpenWeatherMap data.\n"
                         "Type /help to get this message again.")


@dispatcher.message_handler(lambda message: not message.is_command())
async def get_city(message: types.message):
    await message.answer(f"Your city is {message.text}")


if __name__ == '__main__':
    main()

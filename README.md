# Weather bot for Telegram

This is simple bot that gets weather data from OpenWeatherMap and sends it to you in Telegram. 
It is rather training thing. The main aim of this little project was to get familiar with aiogram lib, and as a bonus requests lib.

## How to launch

Provide two ENV variables:
`BOT_TOKEN` with token from @BotFather bot from Telegram and
`OWM_TOKEN` with token from [OpenWeatherMap](https://home.openweathermap.org/api_keys) (bot works with free tier).

Use docker-compose for easy launch (put variables in `.env` file in project root).

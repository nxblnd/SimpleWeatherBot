FROM python:3

WORKDIR /usr/weatherbot/
VOLUME /var/db/weatherbot

RUN pip install pipenv
COPY *.py Pipfile Pipfile.lock *.sql ./
RUN pipenv install --system --deploy --ignore-pipfile

CMD python main.py
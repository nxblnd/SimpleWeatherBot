FROM python:3

WORKDIR /usr/weatherbot/

RUN pip install pipenv
COPY *.py Pipfile Pipfile.lock ./
RUN pipenv install --system --deploy --ignore-pipfile

CMD python main.py
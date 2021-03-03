FROM python:3

WORKDIR /usr/weatherbot/

COPY *.py Pipfile Pipfile.lock ./

RUN pip install pipenv
RUN pipenv install --system --deploy --ignore-pipfile

CMD python main.py
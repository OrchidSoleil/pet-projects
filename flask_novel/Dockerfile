FROM python:3.11.3-slim-buster

WORKDIR /usr/src/app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update && apt-get install -y netcat  &&\
    apt-get install -y libpq-dev gcc

RUN pip install --upgrade pip
COPY ./requirements.txt /usr/src/app/requirements.txt
RUN pip install -r requirements.txt
RUN flake8 /usr/src/app --ignore=E501,F401 --exclude=/usr/src/app/venv

COPY . /usr/src/app/

ENTRYPOINT [ "/usr/src/app/entrypoint.sh" ]

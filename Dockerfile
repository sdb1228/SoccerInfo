FROM python:2.7

RUN pip install beautifulsoup4

RUN pip install psycopg2

RUN pip install requests

RUN apt-get update \
  && apt-get install qt5-default libqt5webkit5-dev build-essential python-lxml python-pip xvfb -y

RUN pip install dryscrape

RUN apt-get install vim -y

COPY ./*.py /scrapers/

WORKDIR scrapers

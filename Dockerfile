FROM ubuntu:24.04
LABEL maintainer="Paulo Pereira, Vinicius Santos"

RUN mkdir -p /home/trading-bot

EXPOSE 8000

RUN apt-get update \
    && apt-get install -y python3.12 \
    && apt-get install -y python3-pip \
    && apt-get install -y python3-venv \
    && apt-get install -y libpq-dev \
    && apt-get install -y tzdata

COPY ./requirements.txt /home/requirements.txt

RUN python3 -m venv /home/venv \
    && . /home/venv/bin/activate \
    && pip install pip --upgrade \
    && pip install -r /home/requirements.txt \
    && echo "source /home/venv/bin/activate" >> ~/.bashrc

WORKDIR /home/trading-bot


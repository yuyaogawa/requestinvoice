# syntax=docker/dockerfile:1

FROM python:3.8-slim-buster

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .

USER 1000:1000

EXPOSE 8809

CMD [ "python3", "requestinvoice.py"]
FROM python:3.11

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /usr/src/app

RUN apt update
RUN apt install -y netcat-openbsd

COPY requirements.txt /usr/src/app
RUN python3 -m pip install -r requirements.txt
EXPOSE 8000

COPY . .

ENTRYPOINT ["bash", "/usr/src/app/docker-entrypoint.sh"]

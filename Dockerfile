FROM python:3.9-alpine3.13
LABEL maintainer = "http://apellesgroupintl.netlify.app"

ENV PYTHONUNBUFFERED 1

COPY ./requirements.txt /tmp/requirements.txt
COPY ./tqo /tqo
#COPY ./payments /payments
#COPY ./users /users
WORKDIR /tqo
EXPOSE 8000


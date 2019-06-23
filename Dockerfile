FROM python:3.7-alpine
ENV PYTHONUNBUFFERED=1

RUN apk add --update --no-cache postgresql-client
RUN apk add --update --no-cache --virtual .tmp-build-deps \ 
    gcc libc-dev linux-headers postgresql-dev

COPY Pipfile /
COPY Pipfile.lock /
RUN pip install pipenv
RUN pip install flake8
RUN pipenv install --deploy --system

RUN apk del .tmp-build-deps

RUN mkdir /app
WORKDIR /app
COPY ./app/ /app/
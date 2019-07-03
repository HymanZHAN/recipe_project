FROM python:3.7-alpine
ENV PYTHONUNBUFFERED=1

RUN apk add --update --no-cache postgresql-client jpeg-dev
RUN apk add --update --no-cache --virtual .tmp-build-deps \ 
    gcc libc-dev linux-headers postgresql-dev musl-dev zlib zlib-dev

COPY Pipfile /
COPY Pipfile.lock /
RUN pip install pipenv
RUN pip install flake8
RUN pipenv install --deploy --system

RUN apk del .tmp-build-deps

RUN mkdir /app/
WORKDIR /app/
COPY ./app/ /app/

RUN mkdir -p /vol/web/media/
RUN mkdir -p /vol/web/static/
RUN adduser -D user
RUN chown -R user:user /vol/
RUN chown -R user:user /app/
RUN chmod -R 755 /vol/web

USER user
FROM python:3.7-alpine
ENV PYTHONUNBUFFERED=1
COPY Pipfile /
COPY Pipfile.lock / 
RUN pip install pipenv
RUN pip install flake8
RUN pipenv install --deploy --system

RUN mkdir /app
WORKDIR /app
COPY ./app/ /app/
FROM python:3.6-alpine

WORKDIR /app

COPY requirements.txt /app/requirements.txt

# this app needs psycopg2 and it needs to be built from source by pip, these packages are required
RUN apk update && apk add postgresql-dev gcc python3-dev musl-dev

RUN pip install --upgrade pip \
    && pip install -r requirements.txt

EXPOSE 8000
CMD ["python","manage.py","runserver","0.0.0.0:8000"]
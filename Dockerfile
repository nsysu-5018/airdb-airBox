FROM python:3.11.12@sha256:a3e280261e448b95d49423532ccd6e5329c39d171c10df1457891ff7c5e2301b

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./app /code/app

CMD ["fastapi", "run", "app/main.py"]

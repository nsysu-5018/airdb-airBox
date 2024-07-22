FROM python:3.11.9@sha256:a46ef4ef9f9d4fee62ad368f9526552a0a99e90882d246cdefe50d356e3a74dd

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./app /code/app

CMD ["fastapi", "run", "app/main.py"]

FROM python:3.11.9@sha256:16987d51aac9033d29e9a6df0293a90b95c05c68561b48283f6fb68d61452f1a

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./app /code/app

CMD ["fastapi", "run", "app/main.py"]

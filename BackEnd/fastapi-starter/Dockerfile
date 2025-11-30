FROM python:3.10

WORKDIR /code


RUN apt-get update \
    && apt-get install -y netcat-openbsd \
    && rm -rf /var/lib/apt/lists/*


RUN pip install poetry

COPY ./pyproject.toml ./poetry.lock /code/

RUN poetry install

# RUN poetry export -f requirements.txt --output requirements.txt --without-hashes

COPY . /code/

EXPOSE 11325

CMD ["poetry", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "11325"]
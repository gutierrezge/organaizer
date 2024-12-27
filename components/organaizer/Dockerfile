FROM python:3.12-slim

WORKDIR /app

RUN pip install poetry
COPY pyproject.toml poetry.lock ./
RUN poetry install

COPY . .

EXPOSE 5000
CMD ["poetry", "run", "python", "app.py"]
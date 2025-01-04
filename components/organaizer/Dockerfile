FROM python:3.12-slim

WORKDIR /app

# Update OS
RUN apt update && apt -y upgrade && apt -y autoremove

# Install dependencies
RUN apt install -y libglib2.0-0 libsm6 libxext6 libxrender-dev libgl1-mesa-glx

# Update pip
RUN pip install --upgrade pip

# Install poetry
RUN pip install poetry

# Install application dependencies
COPY pyproject.toml poetry.lock ./
RUN poetry install

# Copy ode
# COPY . .

CMD ["poetry", "run", "python", "app.py"]
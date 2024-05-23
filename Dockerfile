FROM python:3.10.7-slim-buster AS base

ENV PYROOT /pyroot
ENV PYTHONUSERBASE $PYROOT
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

RUN groupadd flstock
RUN useradd -g flstock flstock
RUN chown -R flstock:flstock /app

FROM base AS builder

WORKDIR /app

FROM python:3.10.7-slim-buster AS base

ENV PYROOT /pyroot
ENV PYTHONUSERBASE $PYROOT
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

RUN groupadd flstock
RUN useradd -g flstock flstock
RUN chown -R flstock:flstock /app

FROM base AS builder

WORKDIR /app

# Установка зависимостей, необходимых для wkhtmltopdf
RUN apt-get update && apt-get install -y \
    git \
    gcc \
    python3-dev \
    musl-dev \
    libpq-dev \
    cmake \
    build-essential \
    wkhtmltopdf \
    libxrender1 \
    libfontconfig1 \
    libxtst6 \
    libx11-6 \
    libjpeg62-turbo \
    libxext6

COPY Pipfile .
COPY Pipfile.lock .
RUN pip install --upgrade pip
RUN pip install --upgrade setuptools
RUN pip install pipenv
RUN PIP_USER=1 PIP_IGNORE_INSTALLED=1 pipenv install --system --deploy --ignore-pipfile

FROM base
COPY --from=builder $PYROOT/lib/ $PYROOT/lib/
RUN pip install certifi

# Установка wkhtmltopdf в финальном образе
RUN apt-get update && apt-get install -y \
    wkhtmltopdf \
    libxrender1 \
    libfontconfig1 \
    libxtst6 \
    libx11-6 \
    libjpeg62-turbo \
    libxext6

FROM apache/airflow:2.7.2-python3.10 AS base

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH "/opt/airflow/app"
ENV PATH="${PATH}:${PYTHONPATH}"

COPY Pipfile .
COPY Pipfile.lock .

USER root
RUN  apt-get update \
  && apt-get install -y wget libgomp1 \
  && rm -rf /var/lib/apt/lists/*
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
RUN sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list'
RUN apt-get -y update
RUN apt-get install -y google-chrome-stable
RUN groupadd -r airflow && usermod -a -G airflow airflow
RUN mkdir -p /home/airflow/.local/share/undetected_chromedriver
RUN chown -R airflow:airflow /home/airflow/

USER airflow

RUN pip install --upgrade pip
RUN pip install --upgrade setuptools
RUN pip install pipenv
RUN PIP_USER=1 PIP_IGNORE_INSTALLED=1 pipenv install --system --deploy --ignore-pipfile
RUN pip install twisted[tls]

COPY ./parser/entrypoint.sh /entrypoint.sh

ENTRYPOINT ["/usr/bin/dumb-init", "--", "/entrypoint.sh"]

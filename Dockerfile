FROM python:3.6

# se a shell for 'pipenv shell'
ENV SHELL /bin/bash
# set virtual env in project directory
ENV PIPENV_VENV_IN_PROJECT true

WORKDIR /data
VOLUME ["/data"]

# install necessary software
# install pipenv for virtual environments
RUN apt-get update \
    && apt-get install -y vim \
    && apt-get install -y python3-pip python3-dev libpq-dev \
    && apt-get autoremove -y --purge \
    && apt-get autoclean \
    && rm -rf /var/tmp/* /tmp/* /var/lib/apt/lists/* \
    && pip install --upgrade pip \
    && pip install --upgrade pipenv \
    && useradd -u 1000 -U -ms /bin/bash -p '*' -d /data faucet_user

# switch user
USER faucet_user

ENV FAUCET_PORT 8000
EXPOSE 8000

CMD []

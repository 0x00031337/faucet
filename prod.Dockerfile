FROM python:3.6-alpine
# set virtual env in project directory
ENV PIPENV_VENV_IN_PROJECT true

# install necessary software
# install pipenv for virtual environments
RUN apk add --no-cache gcc linux-headers python3-dev postgresql-dev musl-dev \
    && pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir --upgrade pipenv \
    && adduser -u 1000 -s /bin/false -D faucet \
    && mkdir -p /data/tmp \
    && chown -R faucet:faucet /data/tmp && ls -l /data

WORKDIR /data

COPY ./faucet /data
RUN chown -R faucet:faucet /data

ENV FAUCET_PORT 8000
EXPOSE $FAUCET_PORT
# collectstatic requires SECRET_KEY
ARG SECRET_KEY
ENV SECRET_KEY=$SECRET_KEY

RUN pipenv --three \
    && pipenv update

RUN apk del python3-dev gcc linux-headers \
    && rm -rf /var/cache/apk/*


# switch user
USER faucet

RUN pipenv run sh -c "python manage.py collectstatic --noinput -i rest_framework -i admin"

CMD pipenv run sh -c "python manage.py migrate && ./start_uwsgi_server.sh"

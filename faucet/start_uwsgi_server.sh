#!/bin/sh

uwsgi --http 0.0.0.0:"$FAUCET_PORT" --static-map /static/=/data/static/ --module faucet.wsgi

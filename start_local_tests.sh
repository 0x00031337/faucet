#!/bin/bash

docker-compose -f docker-compose-testing.yml rm -s -f \
  && docker-compose -f docker-compose-testing.yml up -d --build \
  && docker-compose -f docker-compose-testing.yml logs  -f

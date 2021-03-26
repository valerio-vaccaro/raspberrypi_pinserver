#!/bin/sh

cd /opt
docker run -v $PWD/server_private_key.key:/server_private_key.key -v $PWD/pinsdir:/pins -p 8096:8096 dockerized_pinserver

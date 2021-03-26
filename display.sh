#!/bin/sh

cd /opt/raspberrypi_pinserver
while true
do
  python3 display.py
  sleep 60
done

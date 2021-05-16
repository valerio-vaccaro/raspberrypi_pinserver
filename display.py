#!/usr/bin/env python
# -*- coding:utf-8 -*-
import sys
import os
from waveshare_epd import epd2in13
import time
from PIL import Image,ImageDraw,ImageFont
import traceback
import struct
import smbus
import RPi.GPIO as GPIO
import psutil
import qrcode
import socket
import datetime
import socket


def readVoltage(bus):
        "This function returns as float the voltage from the Raspi UPS Hat via the provided SMBus object"
        address = 0x36
        read = bus.read_word_data(address, 0X02)
        swapped = struct.unpack("<H", struct.pack(">H", read))[0]
        voltage = swapped * 1.25 /1000/16
        return voltage

def readCapacity(bus):
        "This function returns as a float the remaining capacity of the battery connected to the Raspi UPS Hat via the provided SMBus object"
        address = 0x36
        read = bus.read_word_data(address, 0X04)
        swapped = struct.unpack("<H", struct.pack(">H", read))[0]
        capacity = swapped/256
        return capacity

def QuickStart(bus):
        address = 0x36
        bus.write_word_data(address, 0x06,0x4000)

def PowerOnReset(bus):
        address = 0x36
        try:
            bus.write_word_data(address, 0xfe,0x0054)
        except:
            print("err")

def main():
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(4,GPIO.IN)
    bus = smbus.SMBus(1)  # 0 = /dev/i2c-0 (port I2C0), 1 = /dev/i2c-1 (port I2C1)
    PowerOnReset(bus)
    QuickStart(bus)

    font15 = ImageFont.truetype('./Font.ttc', 15)
    font24 = ImageFont.truetype('./Font.ttc', 24)

    try:
        epd = epd2in13.EPD()
        epd.init(epd.lut_full_update)
        epd.Clear(0xFF)

        image = Image.new('1', (epd.height, epd.width), 255)  # 255: clear the frame
        draw = ImageDraw.Draw(image)

        draw.text((5,  0), 'Pinserver', font = font24, fill = 0)

        batt = 'BAT: '+str(round(readVoltage(bus), 2))+'V '+str(round(readCapacity(bus)))+'%'
        if (GPIO.input(4) == GPIO.HIGH):
            batt = batt + ' *'
        draw.text((5, 25), batt, font = font15, fill = 0)

        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        ip = 'IP: '+local_ip
        draw.text((5, 45), ip, font = font15, fill = 0)

        cpu = 'CPU: '+str(psutil.cpu_percent())+'% used'
        draw.text((5, 65), cpu, font = font15, fill = 0)

        mem = 'MEM: '+str(round(psutil.virtual_memory().available * 100 / psutil.virtual_memory().total))+'% free'
        draw.text((5, 85), mem, font = font15, fill = 0)

        time = str(datetime.datetime.now()).split('.')[0]
        draw.text((5, 105), time, font = font15, fill = 0)

        f = open('/var/lib/tor/hidden_service/hostname', 'r')
        tor = f.read()
        f.close()
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=3,
            border=1,
        )
        qr.add_data(tor)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        img.save('/var/www/html/tor.png')
        image.paste(img, (140,10))
        epd.display(epd.getbuffer(image))
        epd.sleep()

    except IOError as e:
        print(e)

    except KeyboardInterrupt:
        epd2in13.epdconfig.module_exit()
        exit()

if __name__ == "__main__":
    main()

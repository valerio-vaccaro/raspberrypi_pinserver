# Raspberrypi Pinserver

Blockstream Blind Pin Server installation for Raspberry Pi Zero.

## Hardware needed
- Raspberry Pi Zero WH
- UPS Lite V1.2 UPS
- Waveshare 2.9inch e-Paper Module

## Install Docker

Install Docker on your board.

```
curl -sSL https://get.docker.com | sh
sudo usermod -aG docker pi
sudo apt-get install -y libffi-dev libssl-dev
sudo apt-get install -y python3 python3-pip
sudo apt-get remove python-configparser
sudo pip3 -v install docker-compose
```

## Install Pinserver

Create the image for the pin server and create the server keys.

```
git clone https://github.com/valerio-vaccaro/blind_pin_server.git pinserver
cd pinserver
git checkout raspberry_pi_zero
cd -

python -m venv -p python3 venv
. venv/bin/activate
pip install --require-hashes -r pinserver/requirements.txt
python -m pinserver.generateserverkey
docker build -f pinserver/Dockerfile pinserver/ -t dockerized_pinserver
mkdir pinsdir
```

(Optional) Start the docker that contain pin server.

```
cd /opt
docker run -v $PWD/server_private_key.key:/server_private_key.key -v $PWD/pinsdir:/pins -p 8096:8096 dockerized_pinserver
```

## Install tor

Install tor and configure on port 8096.

```
sudo apt install tor
sudo sed -i -r 's/#HiddenServiceDir \/var\/lib\/tor\/hidden_service\//HiddenServiceDir \/var\/lib\/tor\/hidden_service\//' /etc/tor/torrc
sudo sed -i -r 's/#HiddenServicePort 80 127.0.0.1:80/HiddenServicePort 8096 127.0.0.1:8096/' /etc/tor/torrc
sudo /etc/init.d/tor restart

```

## Install Power

Enable I2C interface from raspi-config and test using the following program.

```
git clone https://github.com/linshuqin329/UPS-Lite
sudo pip3 install smbus

```

(Optional) Check functionalities

```
cd /opt/UPS-Lite
python3 UPS_Lite.py
```

## Install e-ink display

Enable SPI interface from raspi-config and install drivers.

```
wget http://www.airspayce.com/mikem/bcm2835/bcm2835-1.60.tar.gz
tar zxvf bcm2835-1.60.tar.gz
cd bcm2835-1.60/
./configure
make
make check
sudo make install

sudo apt-get update
sudo apt-get install python3-pip python3-pil python3-numpy
sudo pip3 install RPi.GPIO spidev qrcode psutil

git clone https://github.com/waveshare/e-Paper
cd e-Paper/RaspberryPi_JetsonNano/python
sudo pip3 install .
```

Optionally test the display with examples.

```
cd examples
python3 epd_2in13_test.py
```

## Start

```
sudo apt install nodejs npm
sudo npm install -g pm2
sudo pm2 start /opt/raspberrypi_pinserver/docker.sh
sudo pm2 start /opt/raspberrypi_pinserver/display.sh
sudo pm2 save
sudo pm2 startup
```

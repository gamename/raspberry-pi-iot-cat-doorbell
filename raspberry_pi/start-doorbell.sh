#!/bin/sh
python3 ${HOME}/raspberry-pi-iot-cat-doorbell/raspberry_pi/doorbell.py \
  --endpoint a3u37c52vq0b6j-ats.iot.us-east-1.amazonaws.com \
  --rootCA ${HOME}/root-CA.crt \
  --cert ${HOME}/cat-doorbell.cert.pem \
  --key ${HOME}/cat-doorbell.private.key \
  --model ${HOME}/raspberry-pi-iot-cat-doorbell/raspberry_pi/yamnet.tflite

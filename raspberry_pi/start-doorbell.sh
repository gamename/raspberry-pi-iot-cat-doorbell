#!/bin/sh
nohup python3 "${HOME}/raspberry-pi-iot-cat-doorbell/raspberry_pi/doorbell.py" \
  --endpoint a3u37c52vq0b6j-ats.iot.us-east-1.amazonaws.com                    \
  --root_ca "${HOME}/root-CA.crt"                                              \
  --cert "${HOME}/cat-doorbell.cert.pem"                                       \
  --key "${HOME}/cat-doorbell.private.key"                                     \
  --topic "tns/bot/cat-doorbell"                                               \
  --client_id doorbell                                                         \
  --message 'MSG002 Milo at the door!'                                         \
  --model "${HOME}/raspberry-pi-iot-cat-doorbell/raspberry_pi/yamnet.tflite" > /tmp/doorbell.log 2>&1 &

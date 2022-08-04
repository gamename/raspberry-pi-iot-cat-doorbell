Files and their usage

`doorbell.py` - Listens for a Cat sound using Tensorflow and sends a notification of it using AWS IoT via MQTT
`start-doorbell.sh` - Invokes the doorbell.py script. Use this in `/etc/rc.local` to start at boot time.
`yamnet.tflite` - The Tensorflow library used to identify the cat meow

`test/doorbell-test.py` - A simplified version of the doorbell script used to test the SMS functionality
`test/drive-doorbell-test.sh` - Script that invokes the test doorbell script


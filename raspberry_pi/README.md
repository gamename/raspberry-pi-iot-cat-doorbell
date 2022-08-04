Files and their usage
<br>
`doorbell.py` - Listens for a Cat sound using Tensorflow and sends a notification of it using AWS IoT via MQTT<br>
`start-doorbell.sh` - Invokes the doorbell.py script. Use this in `/etc/rc.local` to start at boot time.<br>
`yamnet.tflite` - The Tensorflow library used to identify the cat meow<br>
`requirements.txt` - The requirements for the doorbell.py script<br>
<br><br>
`test/doorbell-test.py` - A simplified version of the doorbell script used to test the SMS functionality<br>
`test/drive-doorbell-test.sh` - Script that invokes the test doorbell script<br>



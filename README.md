# raspberry-pi-iot-cat-doorbell

<br><br>
This is a setup to alert me when our cat is meowing at the door and wants to be let in. If the door is closed, and the
cat goes 'meow' while outside, then I get text message on my cell phone.
<br><br>

# Technical Description

This is an Amazon Web Services (AWS) Internet of Things (IoT) application. A single Raspberry Pi is defined as a "thing" 
on AWS in the IoT Core service. AWS software is loaded on the Raspberry Pi which has an attached microphone. Onboard the 
Raspberry Pi is a small Machine Learning (ML) application called Tensorflow Lite. Along with Tensorflow, there is a 
small database of sounds it is able to identify. WHen the correct sound (in this case a cat meowing) is detected, 
the Tensorflow recognizes it and forwards a message to AWS. AWS IoT intercepts the message and sends the message to 
an AWS Lambda function for formatting. The Lambda function then forwards the message to an SNS (Simple Notification Service) 
topic which then sends it as an SMS text message to my cell phone.
<br><br>

# High Level Design<br>

![](.README_images/diagram.png)
<br><br>

# Prerequisites<br>

1. An AWS (Amazon Web
   Services) [account](https://aws.amazon.com/premiumsupport/knowledge-center/create-and-activate-aws-account/)
2. [A Raspberry Pi 4](https://www.amazon.com/dp/B08Q8L3B9D?ref_=cm_sw_r_cp_ud_dp_70VG7MF3JGCHTGZKZGG4) (see hardware
   parts listed below)
3. [Raspberry Pi imaging software](https://www.raspberrypi.com/software/)
   <br><br>

# STEP 1: Raspberry Pi (RPi) Initial Configuration

1. Load the operating system. See the procedure [here](https://youtu.be/u8bbp79haN4)<br>
   NOTE: Install the new *64-bit* version of the operating system.<br>

2. SSH to your Raspberry Pi once you have it configured

3. Clone a copy of this repository

```bash
    git clone https://github.com/gamename/raspberry-pi-iot-cat-doorbell.git
```

4. Using Python, install the required packages

```bash
    cd ~/raspberry-pi-iot-cat-doorbell/raspberry_pi
    pip install -r requirements.txt
```

5. Install the AWS CLI (Command Line Interface)

```bash
    pip install awscli
```

6. Using your AWS account, create and install the access and secret keys as
   described [here](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-quickstart.html)

```bash
    aws configure
```

7. Verify you have everything configured by issuing this command (below). If you do not get any errors, you are
   configured correctly.

```bash
    aws s3 ls
```

<br><br>

# STEP 2: AWS Configuration

1. Create the "thing" on AWS
2. Download the thing configuration zip file
3. Update the security policy
4. Create message routing rule
5. Configure Rule SQL statement
6. Point rule to Lambda function
7. Create Lambda function
8. Create the SNS topic
9. Create the SMS subscription (i.e. define the telephone number)
10. Subscribe to the SNS topic with the SMS subscription
11. Update IAM role policy with correct permissions
    <br><br>

# Hardware Parts List <br>

1. Raspberry Pi 4
2. Micro SD Card
3. RPi Chassis
4. Microphone
5. RJ45 ethernet cable (to extend the USB connection)
6. Raspberry Pi 4 power supply
7. Hobby box (to house the microphone)
8. silicone caulking
9. Drill
10. 1/4" drill bit
11. RJ45-to-USB adapters 
12. 2 wood screws
13. cable wire clips
14. double-sided tape
15. micro SD card reader
16. RJ45 crimping tool

<br><br>

# FAQ

Q. How much will this cost?<br>
A. ????
<br><br>
Q. How long does this take to set up?<br>
A. Once you have all the parts, you could probably do it in an afternoon
<br><br>
Q. Could this be used for a dog?<br>
A. Yes. Change the FIXME FIXME
<br><br>
Q. Why didn't you do this using Terraform?<br>
A. Terraform is an excellent tool, but not everyone knows how to use it.  So, I opted for a manual approach to be 
accessible to a wider audience.
<br><br>

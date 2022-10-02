"""
A combination of IOT and Tensorflow that implements a cat doorbell. When a 'meow' is detected,
an IOT message is sent.
"""
import argparse
import json
import logging
import time
import sys

from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
from tflite_support.task import audio, core, processor

AllowedActions = ['both', 'publish', 'subscribe']


def custom_callback(client, userdata, message):
    """
    Custom callback function to be called when a payload is sent from AWS
    :param client: client to send payload
    :param userdata: userdata to send
    :param message: message to be sent
    :return: Nothing
    """
    print("Received a new message: ")
    print(message.payload)
    print("from topic: ")
    print(message.topic)
    print("--------------\n\n")


def tensor_setup(args):
    """
    Set up the Tensorflow server

    :param args: The command line arguments
    :return: data structure containing the tensor data
    """
    flow_data = {}
    base_options = core.BaseOptions(file_name=str(args.model),
                                    use_coral=bool(args.enableEdgeTPU),
                                    num_threads=int(args.numThreads))
    classification_options = processor.ClassificationOptions(max_results=int(args.maxResults),
                                                             score_threshold=float(
                                                                 args.scoreThreshold))
    options = audio.AudioClassifierOptions(base_options=base_options,
                                           classification_options=classification_options)

    classifier = audio.AudioClassifier.create_from_options(options)

    audio_record = classifier.create_audio_record()
    tensor_audio = classifier.create_input_tensor_audio()

    input_length_in_second = float(len(tensor_audio.buffer)) / tensor_audio.format.sample_rate
    interval_between_inference = input_length_in_second * (1 - float(args.overlappingFactor))
    pause_time = interval_between_inference * 0.1
    last_inference_time = time.time()

    # audio_record.start_recording()
    flow_data['classifier'] = classifier
    flow_data['tensor_audio'] = tensor_audio
    flow_data['audio_record'] = audio_record
    flow_data['pause_time'] = pause_time
    flow_data['last_inference_time'] = last_inference_time
    return flow_data


def iot_setup(args):
    """
    Sets up the AWS IOT connection
    """
    host = args.host
    root_ca_path = args.root_ca_path
    certificate_path = args.certificate_path
    private_key_path = args.private_key_path
    port = args.port
    use_web_socket = args.use_web_socket
    client_id = args.client_id

    # Port defaults
    # When no port override for WebSocket, default to 443
    if args.use_web_socket and not args.port:
        port = 443

    # When no port override for non-WebSocket, default to 8883
    if not args.use_web_socket and not args.port:
        port = 8883

    # Configure logging
    logger = logging.getLogger("AWSIoTPythonSDK.core")
    logger.setLevel(logging.CRITICAL)
    stream_handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    if use_web_socket:
        print("websocket!")
        iot_client = AWSIoTMQTTClient(client_id, use_web_socket=True)
        iot_client.configureEndpoint(host, port)
        iot_client.configureCredentials(root_ca_path)
    else:
        print("NON-websocket!")
        iot_client = AWSIoTMQTTClient(client_id)
        iot_client.configureEndpoint(host, port)
        iot_client.configureCredentials(root_ca_path, private_key_path, certificate_path)

    # AWSIoTMQTTClient connection configuration
    iot_client.configureAutoReconnectBackoffTime(1, 32, 20)
    iot_client.configureOfflinePublishQueueing(-1)  # Infinite offline Publish queueing
    iot_client.configureDrainingFrequency(2)  # Draining: 2 Hz
    iot_client.configureConnectDisconnectTimeout(10)  # 10 sec
    iot_client.configureMQTTOperationTimeout(5)  # 5 sec

    return iot_client


def connect_client(iot_client):
    """
    Connects to AWS IoTMQTTClient
    :param iot_client: The client to connect to Amazon
    :return: Nothing
    """
    retry_flag = True
    retry_count = 0

    while retry_flag and retry_count < 5:
        try:
            # Connect and subscribe to AWS IoT
            iot_client.connect()
            print("Connection successful!")
            retry_flag = False
        except Exception as err:
            print(err)
            print("Connection unsuccessful! Retry after 5 sec")
            retry_count = retry_count + 1
            time.sleep(5)

    if retry_count == 5:
        print("Connection retries exceeded!")
        raise Exception("Could not connect to host!")
    time.sleep(2)


def message_handler(client, topic, msg, tensor):
    """
    Sends a message to the MQTT topic
    :param client: The MQTT client
    :param topic: The topic to send the message to
    :param msg: The message to send
    :param tensor: The tensor to send
    :return: Nothing
    """
    tensor_audio = tensor['tensor_audio']
    audio_record = tensor['audio_record']
    classifier = tensor['classifier']
    last_inference_time = tensor['last_inference_time']
    interval_between_inference = tensor['interval_between_inference']

    while True:
        now = time.time()
        diff = now - last_inference_time
        if diff < interval_between_inference:
            time.sleep(tensor['pause_time'])
            continue
        last_inference_time = now

        # Load the input audio and run classify.
        tensor_audio.load_from_audio_record(audio_record)
        result = classifier.classify(tensor_audio)
        classification = result.classifications[0]
        label_list = [category.class_name for category in classification.classes]
        noise = label_list[0]

        if noise == 'Cat':
            print("Cat detected!")
            client.publish(topic, msg, 1)
            time.sleep(120)


def run(args) -> None:
    """
    The main runner function which sets up both Tensorflow and IoT/MQTT clients. The `while`
    loop runs forever waiting for a cat sound (a meow) to trigger the IoT scripts on AWS and
    thereby drive the SMS notifications.

    :param args: The various arguments passed to the function from the command line
    """

    tensor_data = tensor_setup(args)
    iot_client = iot_setup(args)
    connect_client(iot_client)

    if args.mode in ('both', 'subscribe'):
        iot_client.subscribe(args.topic, 1, custom_callback)

    message = dict(message=args.message)
    message_json = json.dumps(message)

    message_handler(iot_client, args.topic, tensor_data, message_json)


def main():
    """
    The main function
    """
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    # Tensorflow Parameters
    parser.add_argument('--model',
                        help='Name of the audio classification model.',
                        required=False,
                        default='yamnet.tflite')
    parser.add_argument('--maxResults',
                        help='Maximum number of results to show.',
                        required=False,
                        default=5)
    parser.add_argument('--overlappingFactor',
                        help='Target overlapping adjacent inferences. Value must be in (0, 1)',
                        required=False,
                        default=0.5)
    parser.add_argument('--scoreThreshold',
                        help='The score threshold of classification results.',
                        required=False,
                        default=0.0)
    parser.add_argument('--numThreads',
                        help='Number of CPU threads to run the model.',
                        required=False,
                        default=4)
    parser.add_argument('--enableEdgeTPU',
                        help='Whether to run the model on EdgeTPU.',
                        action='store_true',
                        required=False,
                        default=False)
    # IOT Parameters
    parser.add_argument("--endpoint",
                        action="store",
                        required=True,
                        dest="host",
                        help="Your AWS IoT custom endpoint")
    parser.add_argument("--rootCA",
                        action="store",
                        required=True,
                        dest="root_ca_path",
                        help="Root CA file path")
    parser.add_argument("--cert",
                        action="store",
                        dest="certificate_path",
                        help="Certificate file path")
    parser.add_argument("--key",
                        action="store",
                        dest="private_key_path",
                        help="Private key file path")
    parser.add_argument("--port",
                        action="store",
                        dest="port",
                        type=int,
                        help="Port number override")
    parser.add_argument("--websocket",
                        action="store_true",
                        dest="use_web_socket",
                        default=False,
                        help="Use MQTT over WebSocket")
    parser.add_argument("--client_id",
                        action="store",
                        dest="client_id",
                        default="basicPubSub",
                        help="Targeted client id")
    parser.add_argument("--topic",
                        action="store",
                        dest="topic",
                        default="tns/bot/cat-doorbell",
                        help="Targeted topic")
    parser.add_argument("--mode",
                        action="store",
                        dest="mode",
                        default="both",
                        help="Operation modes: " + str(AllowedActions))
    parser.add_argument("--message",
                        action="store",
                        dest="message",
                        help="Message to publish")

    args = parser.parse_args()

    if (args.overlappingFactor <= 0) or (args.overlappingFactor >= 1.0):
        parser.error('Overlapping factor must be between 0 and 1.')
        sys.exit(2)

    if (args.scoreThreshold < 0) or (args.scoreThreshold > 1.0):
        parser.error('Score threshold must be between (inclusive) 0 and 1.')
        sys.exit(2)

    if args.mode not in AllowedActions:
        parser.error("Unknown --mode option " + args.mode +
                     ". Must be one of " + str(AllowedActions))
        sys.exit(2)

    if args.use_web_socket and args.certificate_path and args.private_key_path:
        parser.error("X.509 cert authentication and WebSocket are mutually exclusive.")
        sys.exit(2)

    if not args.use_web_socket and (not args.certificate_path or not args.private_key_path):
        parser.error("Missing credentials for authentication.")
        sys.exit(2)

    run(args)


if __name__ == '__main__':
    main()

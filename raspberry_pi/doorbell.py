import argparse
import json
import logging
import time

from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
from tflite_support.task import audio, core, processor

AllowedActions = ['both', 'publish', 'subscribe']


# Custom MQTT message callback
def customCallback(client, userdata, message):
    print("Received a new message: ")
    print(message.payload)
    print("from topic: ")
    print(message.topic)
    print("--------------\n\n")


def run(args) -> None:
    """
    The main runner function which sets up both Tensorflow and IoT/MQTT clients. The `while` loop runs forever
    waiting for a cat sound (a meow) to trigger the IoT scripts on AWS and thereby drive the SMS notifications.

    :param args: The various arguments passed to the function from the command line
    """
    # Tensorflow setup
    model = str(args.model)
    max_results = int(args.maxResults)
    score_threshold = float(args.scoreThreshold)
    overlapping_factor = float(args.overlappingFactor)
    num_threads = int(args.numThreads)
    enable_edgetpu = bool(args.enableEdgeTPU)

    base_options = core.BaseOptions(file_name=model, use_coral=enable_edgetpu, num_threads=num_threads)
    classification_options = processor.ClassificationOptions(max_results=max_results, score_threshold=score_threshold)
    options = audio.AudioClassifierOptions(base_options=base_options, classification_options=classification_options)

    classifier = audio.AudioClassifier.create_from_options(options)

    audio_record = classifier.create_audio_record()
    tensor_audio = classifier.create_input_tensor_audio()

    input_length_in_second = float(len(tensor_audio.buffer)) / tensor_audio.format.sample_rate
    interval_between_inference = input_length_in_second * (1 - overlapping_factor)
    pause_time = interval_between_inference * 0.1
    last_inference_time = time.time()

    audio_record.start_recording()

    # IOT Setup
    host = args.host
    rootCAPath = args.rootCAPath
    certificatePath = args.certificatePath
    privateKeyPath = args.privateKeyPath
    port = args.port
    useWebsocket = args.useWebsocket
    clientId = args.clientId
    topic = args.topic

    # Port defaults
    if args.useWebsocket and not args.port:  # When no port override for WebSocket, default to 443
        port = 443
    if not args.useWebsocket and not args.port:  # When no port override for non-WebSocket, default to 8883
        port = 8883

    # Configure logging
    logger = logging.getLogger("AWSIoTPythonSDK.core")
    logger.setLevel(logging.CRITICAL)
    streamHandler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    streamHandler.setFormatter(formatter)
    logger.addHandler(streamHandler)

    # Init AWSIoTMQTTClient
    iotClient = None
    if useWebsocket:
        print("websocket!")
        iotClient = AWSIoTMQTTClient(clientId, useWebsocket=True)
        iotClient.configureEndpoint(host, port)
        iotClient.configureCredentials(rootCAPath)
    else:
        print("NON-websocket!")
        iotClient = AWSIoTMQTTClient(clientId)
        iotClient.configureEndpoint(host, port)
        iotClient.configureCredentials(rootCAPath, privateKeyPath, certificatePath)

    # AWSIoTMQTTClient connection configuration
    iotClient.configureAutoReconnectBackoffTime(1, 32, 20)
    iotClient.configureOfflinePublishQueueing(-1)  # Infinite offline Publish queueing
    iotClient.configureDrainingFrequency(2)  # Draining: 2 Hz
    iotClient.configureConnectDisconnectTimeout(10)  # 10 sec
    iotClient.configureMQTTOperationTimeout(5)  # 5 sec

    retry_flag = True
    retry_count = 0

    while retry_flag and retry_count < 5:
        try:
            # Connect and subscribe to AWS IoT
            iotClient.connect()
            print("Connection successful!")
            retry_flag = False
        except Exception as e:
            print(e)
            print("Connection unsuccessful! Retry after 5 sec")
            retry_count = retry_count + 1
            time.sleep(5)

    if retry_count == 5:
        print("Connection retries exceeded!")
        raise Exception("Could not connect to host!")

    if args.mode == 'both' or args.mode == 'subscribe':
        iotClient.subscribe(topic, 1, customCallback)
    time.sleep(2)

    message = dict(message=args.message)
    messageJson = json.dumps(message)

    while True:
        now = time.time()
        diff = now - last_inference_time
        if diff < interval_between_inference:
            time.sleep(pause_time)
            continue
        last_inference_time = now

        # Load the input audio and run classify.
        tensor_audio.load_from_audio_record(audio_record)
        result = classifier.classify(tensor_audio)

        classification = result.classifications[0]
        label_list = [category.class_name for category in classification.classes]
        noise = label_list[0]
        # print(noise)
        if noise == 'Cat':
            iotClient.publish(topic, messageJson, 1)
            if args.mode == 'publish':
                print('Published topic %s: %s\n' % (topic, messageJson))
            time.sleep(600)


def main():
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
                        help='Target overlapping between adjacent inferences. Value must be in (0, 1)',
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
                        dest="rootCAPath",
                        help="Root CA file path")
    parser.add_argument("--cert",
                        action="store",
                        dest="certificatePath",
                        help="Certificate file path")
    parser.add_argument("--key",
                        action="store",
                        dest="privateKeyPath",
                        help="Private key file path")
    parser.add_argument("--port",
                        action="store",
                        dest="port",
                        type=int,
                        help="Port number override")
    parser.add_argument("--websocket",
                        action="store_true",
                        dest="useWebsocket",
                        default=False,
                        help="Use MQTT over WebSocket")
    parser.add_argument("--clientId",
                        action="store",
                        dest="clientId",
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
                        help="Operation modes: %s" % str(AllowedActions))
    parser.add_argument("--message",
                        action="store",
                        dest="message",
                        default="MSG002 Milo at the door!",
                        help="Message to publish")

    args = parser.parse_args()

    if (args.overlappingFactor <= 0) or (args.overlappingFactor >= 1.0):
        parser.error('Overlapping factor must be between 0 and 1.')
        exit(2)

    if (args.scoreThreshold < 0) or (args.scoreThreshold > 1.0):
        parser.error('Score threshold must be between (inclusive) 0 and 1.')
        exit(2)

    if args.mode not in AllowedActions:
        parser.error("Unknown --mode option %s. Must be one of %s" % (args.mode, str(AllowedActions)))
        exit(2)

    if args.useWebsocket and args.certificatePath and args.privateKeyPath:
        parser.error("X.509 cert authentication and WebSocket are mutual exclusive. Please pick one.")
        exit(2)

    if not args.useWebsocket and (not args.certificatePath or not args.privateKeyPath):
        parser.error("Missing credentials for authentication.")
        exit(2)

    run(args)


if __name__ == '__main__':
    main()

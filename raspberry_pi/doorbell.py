import argparse
import time

from tflite_support.task import audio
from tflite_support.task import core
from tflite_support.task import processor


def run(model: str, max_results: int, score_threshold: float,
        overlapping_factor: float, num_threads: int,
        enable_edgetpu: bool) -> None:
    if (overlapping_factor <= 0) or (overlapping_factor >= 1.0):
        raise ValueError('Overlapping factor must be between 0 and 1.')

    if (score_threshold < 0) or (score_threshold > 1.0):
        raise ValueError('Score threshold must be between (inclusive) 0 and 1.')

    # Initialize the audio classification model.
    base_options = core.BaseOptions(file_name=model, use_coral=enable_edgetpu, num_threads=num_threads)
    classification_options = processor.ClassificationOptions(max_results=max_results, score_threshold=score_threshold)
    options = audio.AudioClassifierOptions(base_options=base_options, classification_options=classification_options)

    classifier = audio.AudioClassifier.create_from_options(options)

    # Initialize the audio recorder and a tensor to store the audio input.
    audio_record = classifier.create_audio_record()
    tensor_audio = classifier.create_input_tensor_audio()

    # We'll try to run inference every interval_between_inference seconds.
    # This is usually half of the model's input length to create an overlapping
    # between incoming audio segments to improve classification accuracy.
    input_length_in_second = float(len(tensor_audio.buffer)) / tensor_audio.format.sample_rate
    interval_between_inference = input_length_in_second * (1 - overlapping_factor)
    pause_time = interval_between_inference * 0.1
    last_inference_time = time.time()

    # Start audio recording in the background.
    audio_record.start_recording()

    # Loop until the user close the classification results plot.
    while True:
        # Wait until at least interval_between_inference seconds has passed since
        # the last inference.
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
        print(label_list[0])


def main():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        '--model',
        help='Name of the audio classification model.',
        required=False,
        default='yamnet.tflite')
    parser.add_argument(
        '--maxResults',
        help='Maximum number of results to show.',
        required=False,
        default=5)
    parser.add_argument(
        '--overlappingFactor',
        help='Target overlapping between adjacent inferences. Value must be in (0, 1)',
        required=False,
        default=0.5)
    parser.add_argument(
        '--scoreThreshold',
        help='The score threshold of classification results.',
        required=False,
        default=0.0)
    parser.add_argument(
        '--numThreads',
        help='Number of CPU threads to run the model.',
        required=False,
        default=4)
    parser.add_argument(
        '--enableEdgeTPU',
        help='Whether to run the model on EdgeTPU.',
        action='store_true',
        required=False,
        default=False)
    args = parser.parse_args()

    run(args.model, int(args.maxResults), float(args.scoreThreshold),
        float(args.overlappingFactor), int(args.numThreads),
        bool(args.enableEdgeTPU))


if __name__ == '__main__':
    main()

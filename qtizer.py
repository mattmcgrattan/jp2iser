from multiprocessing import Pool
import qtizer_settings as settings
from boto import sqs
from boto.sqs.message import Message
import json
import requests

output_queue = None


def main():
    input_queue = get_input_queue()

    # TODO : check queues not None

    pool = Pool(5, initializer=init_pool, initargs=())

    while True:
        messages = input_queue.get_messages(num_messages=10, visibility_timeout=120, wait_time_seconds=20)
        if len(messages) > 0:
            pool.map(process_message, messages)


def process_message(message):
    try:
        message_payload = json.loads(str(message.get_body()))

        # payload may be encoded in standard message format
        if '_type' in message_payload and 'message' in message_payload \
                and message_payload['message'] == "event::image-ingest-more":
            message_payload = convert_message_format(message_payload)

        call_tizer(message_payload)

    except Exception:
        # TODO : log
        pass

    message.delete()


def call_tizer(payload):

    r = requests.post(settings.TIZER_SERVICE, json=payload)
    if r.status_code == 200:
        pass
    pass


def send_message(payload):
    msg = Message()
    msg.set_body(payload)
    output_queue.write(msg)


def convert_message_format(message_payload):
    if 'params' in message_payload:
        message_payload = message_payload['params']
        if 'thumbSizes' in message_payload:
            message_payload['thumbSizes'] = map(int, message_payload['thumbSizes'][1: -1].split(','))
            return message_payload
    return None


def init_pool():
    global output_queue
    output_queue = get_output_queue()


def get_input_queue():
    conn = sqs.connect_to_region(settings.SQS_REGION)
    queue = conn.get_queue(settings.INPUT_QUEUE)
    return queue


def get_output_queue():
    conn = sqs.connect_to_region(settings.SQS_REGION)
    queue = conn.get_queue(settings.OUTPUT_QUEUE)
    return queue


if __name__ == "__main__":
    main()
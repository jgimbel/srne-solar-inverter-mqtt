import json
import logging
import os
import paho.mqtt.client as paho
from paho.mqtt.enums import CallbackAPIVersion


def get_logger(verbose=False):
    # log_format = '%(asctime)s %(levelname)-6s [%(filename)s:%(lineno)d] %(message)s'
    log_format = '%(asctime)s %(levelname)s [%(module)s] %(message)s'
    if verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO

    logging.basicConfig(level=level, format=log_format, datefmt='%H:%M:%S')
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)

    return logger

logger = get_logger()

class dotdict(dict):
    def __getattr__(self, attr):
        try:
            return self[attr]
        except KeyError as e:
            raise AttributeError(e)

    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__
    # __hasattr__ = dict.__contains__


def load_user_config():
    try:
        with open('/data/options.json') as f:
            conf = dotdict(json.load(f))
    except Exception as e:
        logger.warning('Did not find options in the normal location. Checking the root directory')
        #try the other location where home assistant would put the options
        with open('options.json') as f:
            conf = dotdict(json.load(f))
    return conf


def get_mqtt_client():
    user_config = load_user_config()
    for k, en in dict(mqtt_broker='MQTT_HOST', mqtt_user='MQTT_USER', mqtt_password='MQTT_PASSWORD').items():
        if not user_config.get(k) and os.environ.get(en):
            user_config[k] = os.environ[en]

    if user_config.get('mqtt_broker'):
        port_idx = user_config.mqtt_broker.rfind(':')
        if port_idx > 0:
            user_config.mqtt_port = user_config.get('mqtt_port', int(user_config.mqtt_broker[(port_idx + 1):]))
            user_config.mqtt_broker = user_config.mqtt_broker[:port_idx]

        logger.info('connecting mqtt %s@%s', user_config.mqtt_user, user_config.mqtt_broker)
        # paho_monkey_patch()
        mqtt_client = paho.mqtt.client.Client(CallbackAPIVersion.VERSION2)
        mqtt_client.enable_logger(logger)
        if user_config.get('mqtt_user', None):
            mqtt_client.username_pw_set(user_config.mqtt_user, user_config.mqtt_password)

        try:
            mqtt_client.connect(user_config.mqtt_broker, port=user_config.get('mqtt_port', 1883))
            mqtt_client.loop_start()
        except Exception as ex:
            logger.error('mqtt connection error %s', ex)
    else:
        mqtt_client = None
    return mqtt_client

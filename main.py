#!/usr/bin/python3
from time import sleep
import minimalmodbus
import json
import traceback
from utl import load_user_config, get_mqtt_client, get_logger
from commands import cmds

logger = get_logger()

config = load_user_config()
shutdown = False

instr = minimalmodbus.Instrument(config.device, config.device_id)
instr.serial.baudrate = 9600
instr.serial.timeout = 1
#instr.debug = True




def main():
    global shutdown

    config = load_user_config()

    mqtt_client = get_mqtt_client()
    
    def fetch():
        for name, vals in cmds.items():
            logger.info(name)
            value = instr.read_register(*vals['cmd'])
            logger.info(value)
            topic = f'homeassistant/sensor/snre-{name}/state'
            mqtt_client.publish(f'homeassistant/sensor/snre-{name}/config', json.dumps({
                'state_topic': topic,
                'uniq_id': f'modbus-{config.device_id}-{name}',
                **{key: vals[key] for key in vals if key != 'cmd'}
            }))
            sleep(.1)
            mqtt_client.publish(topic, value, retain=False)
            sleep(.1)
        return True
    fetch_loop(fetch, config.sample_period, 1)


def fetch_loop(fn, period, max_errors):
    global shutdown
    num_errors_row = 0
    while not shutdown:
        try:
            if fn():
                num_errors_row = 0
        except Exception as e:
            num_errors_row += 1
            logger.error('Error (num %d, max %d) reading SRNE: %s', num_errors_row, max_errors, e)
            logger.error('Stack: %s', traceback.format_exc())
            if max_errors and num_errors_row >= max_errors:
                logger.warning('too many errors, abort')
                break
        sleep(period)
    logger.info("fetch_loop %s ends", fn)


try:
    main()
except Exception as e:
    logger.error("Main loop exception: %s", e)
    logger.error("Stack: %s", traceback.format_exc())


import sys
sys.exit(1)
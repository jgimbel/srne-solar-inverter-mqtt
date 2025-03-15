#!/usr/bin/python3
from time import sleep
import minimalmodbus
import json
import traceback
import asyncio
from utl import load_user_config, get_mqtt_client, get_logger

logger = get_logger()

config = load_user_config()

instr = minimalmodbus.Instrument(config.device, config.device_id)
instr.serial.baudrate = 9600
instr.serial.timeout = 1
#instr.debug = True

cmds = {
    'battery_voltage': {
        'cmd': (0x0101, 1, 3,True),
        'name': 'Battery Voltage',
        'unit_of_measurement': 'V',
        'device_class': 'voltage'
    },
    'battery_amps': {
        'cmd': (0x0102, 1, 3,True),
        'name': 'Battery Amps',
        'unit_of_measurement': 'A',
        'device_class': 'current',
        'value_template': '{{value | float * -1}}'
    },
    'shore_power_watts': {
        'cmd': (0x010e, 0, 3,True),
        'name': 'Power In',
        'unit_of_measurement': 'W',
        'device_class': 'power'
    },
    'solar_voltage': {
        'cmd': (0x0107, 1, 3,True),
        'name': 'Solar Voltage',
        'unit_of_measurement': 'V',
        'device_class': 'voltage'
    },
    'solar_amps': {
        'cmd': (0x0108, 1, 3,True),
        'name': 'Solar Amps',
        'unit_of_measurement': 'A',
        'device_class': 'current',
    },
    'solar_watts': {
        'cmd': (0x0109, 0, 3,True),
        'name': 'Solar Power',
        'unit_of_measurement': 'W',
        'device_class': 'power'
    },
    'charger_status': {
        'cmd': (0x0204, 0, 3, False),
        'name': 'Charger Status Code'
    },
    'temp_dc': {
        'cmd':(0x0221, 1, 3, True),
        'name': 'Temperature DC',
        'unit_of_measurement': 'C',
        'device_class': 'temperature'
    },
    'temp_ac': {
        'cmd':(0x0222, 1, 3, True),
        'name': 'Temperature AC',
        'unit_of_measurement': 'C',
        'device_class': 'temperature'
    },
    'temp_tr': {
        'cmd':(0x0223, 1, 3, True),
        'name': 'Temperature TR',
        'unit_of_measurement': 'C',
        'device_class': 'temperature'
    }

}

def main():
    global shutdown

    config = load_user_config()

    mqtt_client = get_mqtt_client()
    
    def fetch():
        for name, vals in cmds.items():
            logger.log(name)
            value = instr.read_register(*vals['cmd'])
            logger.log(value)
            topic = f'homeassistant/sensor/snre-{name}/state'
            mqtt_client.publish(f'homeassistant/sensor/snre-{name}/config', json.dumps({
                'state_topic': topic,
                'uniq_id': f'modbus-{config.device_id}-{name}',
                **{key: vals[key] for key in vals if key != 'cmd'}
            }))
        asyncio.sleep(.1)
        mqtt_client.publish(topic, value, retain=False)
        asyncio.sleep(.1)
    fetch_loop(fetch, config.sample_period, 100)


async def fetch_loop(fn, period, max_errors):
    global shutdown
    num_errors_row = 0
    while not shutdown:
        try:
            if await fn():
                num_errors_row = 0
        except Exception as e:
            num_errors_row += 1
            logger.error('Error (num %d, max %d) reading BMS: %s', num_errors_row, max_errors, e)
            logger.error('Stack: %s', traceback.format_exc())
            if max_errors and num_errors_row > max_errors:
                logger.warning('too many errors, abort')
                break
        await asyncio.sleep(period)
    logger.info("fetch_loop %s ends", fn)


try:
    asyncio.run(main())
except Exception as e:
    logger.error("Main loop exception: %s", e)
    logger.error("Stack: %s", traceback.format_exc())


import sys
sys.exit(1)
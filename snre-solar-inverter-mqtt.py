#!/usr/bin/python3
from time import sleep
import minimalmodbus
import argparse
import json
import asyncio
import paho.mqtt.client as paho

parser = argparse.ArgumentParser()

parser.add_argument('--dev', help='Device Path [default /dev/ttyUSB0]', type=str, default='/dev/ttyUSB0')
parser.add_argument('--device-id', help='RS485 Device ID [default 1]', type=int, default=1)

args = parser.parse_args()
instr = minimalmodbus.Instrument(args.dev, args.device_id)
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

mqtt_client = paho.Client()
mqtt_client.connect('homeassistant.local', 1883)
for name, vals in cmds.items():
    print(name)
    value = instr.read_register(*vals['cmd'])
    print(value)
    print('publishing topic')
    topic = f'homeassistant/sensor/snre-{name}/state'
    mqtt_client.publish(f'homeassistant/sensor/snre-{name}/config', json.dumps({
        'state_topic': topic,
        'uniq_id': f'modbus-{args.device_id}-{name}',
        **{key: vals[key] for key in vals if key != 'cmd'}
    }))
    sleep(.1)
    mqtt_client.publish(topic, value, retain=False)
    sleep(.1)


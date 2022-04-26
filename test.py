from time import sleep
import minimalmodbus

instr = minimalmodbus.Instrument('/dev/ttyUSB1', 1)
instr.serial.baudrate = 9600
instr.serial.timeout = 1
#instr.debug = True

commands = {
    'bci': (0x0101,14,3),
    'unkown1': (0x0204, 0x1f,3),
    'unkown2': (0xF02F,0x0d,3),
    'unkown3': (0xE004,0x01,3),
    'unkown4': (0xDF29,0x10,3),
    'unkown5': (0xE204,0x01,3)
}


vals = instr.read_registers(*commands['bci'], True)
battery_voltage = vals[1] * .1
battery_amps = (vals[2]) * .1
battery_charge_watts = vals[13]


sleep(1)
for name, command in commands.items():
   print(name)
   print(instr.read_registers(*command, True))
   sleep(1)

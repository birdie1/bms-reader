#!/usr/bin/env python3

import serial
import time


def hex2string(hex_value):
    return hex_value.decode('utf-8')


def hex2float(hex_value, cmd):
    raw = hex_value[0:cmd[3]]
    rvalue = int.from_bytes(raw, byteorder="big", signed=cmd[5]) * cmd[4]
    return f'{rvalue:.3f}'


def hex2int(hex_value, cmd):
    raw = hex_value[0:cmd[3]]
    rvalue = int.from_bytes(raw, byteorder="big", signed=cmd[5]) * cmd[4]
    return f'{rvalue:.0f}'


def hex2temperature(hex_value, cmd):
    raw = hex_value[0:cmd[3]]
    rvalue = (int.from_bytes(raw, byteorder="big", signed=cmd[5]) * cmd[4]) - 273.1
    return f'{rvalue:.1f}'


def hex2binary(hex_value, cmd):
    raw = hex_value[0:cmd[3]]
    rvalue = bin(int.from_bytes(raw, byteorder='big'))[2:].zfill(cmd[3]*8)
    return rvalue


"""
Communication Protocol:
Send: STARTFLAG + ADDRESS + COMMAND + DATA-LENGTH (0x08) + DATA (8* 0x00) + CHECKSUM (1-Byte)
"""
STARTFLAG = b'\xa5'
ADDRESS = b'\x80'
#ADDRESS = b'\x40'


"""
other bits not set?

VDQ, Valid Discharge Qualified: the current or next discharge cycle is valid for an update of the Full Charge Capacity.
FC, Fully Charged: if set, means that the battery has detected a primary charge termination or an Overcharge condition.
FD, Fully Discharged: if set, means that the Relative State of Charge has reached the "Battery Low" level, programmed at 8%. Reaching this level makes the LEDs flash when the LED button is pressed.


AFE-SC, Short-Circuit: if set, means that a short circuit in charge direction has been detected and the related safety protections is activated.
OTD: if set, this indicates a safety overtemperature in discharge occurred.
OTC: if set, this indicates a safety overtemperature in charge occurred.

# description, original_shortname
"""

PACK_STATUS = {
    0: ('???', 'CAL'),
    5: ('Valid Discharge Qualified', 'VDQ'),
    6: ('Fully Discharged', 'FD'),
    7: ('Fully Charged', 'FC'),
    9: ('Fast Discharging', 'FAST_DSG'),
    10: ('Medium Discharging', 'MID_DSG'),
    11: ('Slow Discharging', 'SLOW_DSG'),
    12: ('Discharging', 'DSGING'),
    13: ('Charging', 'CHGING'),
    14: ('Discharging enabled', 'DSGMOS'),
    15: ('Charging enabled', 'CHGMOS'),
}

BATTERY_STATUS = {
    1: ('???', 'CTO'),
    2: ('Short Circuit in AFE (Analog Front End)', 'AFE_SC'),
    3: ('Over Voltage in AFE (Analog Front End)', 'AFE_OV'),
    4: ('Under Voltage in Discharge', 'UTD'),
    5: ('Under Voltage in Charge', 'UTC'),
    6: ('Over Voltage in Discharge', 'OTD'),
    7: ('Over Voltage in Charge', 'OTC'),
    12: ('???', 'OCD'),
    13: ('???', 'OCC'),
    14: ('??? Undervoltage?', 'UV'),
    15: ('??? Overvoltage?', 'OV'),
}


# description, unit, datalength, signed?/Subtable, scale
COMMANDS = [
    (b'\x01\x02', 'Cell 1 Voltage', 'V', 2, 0.001, False, hex2float),
    (b'\x02\x02', 'Cell 2 Voltage', 'V', 2, 0.001, False, hex2float),
    (b'\x03\x02', 'Cell 3 Voltage', 'V', 2, 0.001, False, hex2float),
    (b'\x04\x02', 'Cell 4 Voltage', 'V', 2, 0.001, False, hex2float),
    (b'\x0b\x02', 'Total Voltage', 'V', 2, 0.001, False, hex2float),
    (b'\x0c\x02', 'Temperature 1', '°C', 2, 0.1, False, hex2temperature),
    (b'\x10\x04', 'Current (CADC)', 'A', 4, 0.001, True, hex2float),
    (b'\x11\x04', 'Capacity full)', 'Ah', 4, 0.001, False, hex2float),
    (b'\x12\x04', 'Capacity remaining', 'Ah', 4, 0.001, False, hex2float),
    (b'\x13\x02', 'State of Charge (RSOC)', '%', 2, 1, False, hex2int),
    (b'\x14\x02', 'Cycle count', '', 2, 1, False, hex2int),
    (b'\x15\x02', 'Pack Status', '', 2, 0, PACK_STATUS, hex2binary),
    (b'\x16\x02', 'Battery Status', '', 2, 0, BATTERY_STATUS, hex2binary),
]


def print_binary_data(bin_value, subtable):
    for key, val in subtable.items():
        print(f'    {True if int(bin_value[key]) == 1 else False}: {val[0]} | {val[1]}')



def calculate_checksum(cdata):
    result = 0
    #for number in cdata:
    #    result += number

    #return bytes.fromhex(format((result % 256), 'x'))
    result = int(cdata[0:2].hex(), 16)
    return result % 256


def connect():
    return serial.Serial(
        '/dev/ttyUSB0',
        9600,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        bytesize=serial.EIGHTBITS,
        timeout=0
    )


command = b'\x90'
#command = b'\x63'

data = STARTFLAG
data += ADDRESS
data += command
data += b'\x08'
data += b'\x00' * 8

#data += calculate_checksum(data)


for command in COMMANDS:
    data = b'\x0a' + command[0]

    ser = connect()
    ser.write(data)
    time.sleep(0.1)
    response = ser.read(6)
    value = command[6](response, command)
    print(f'{command[1]}: {value}{command[2]} | Response was: {response.hex()} | CRC: (should:{response[2]}) (is:{calculate_checksum(response[0:command[3]])})')
    if command[4] == 0:
        print_binary_data(value, command[5])




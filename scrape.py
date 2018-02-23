#!/bin/python

"""
This module reads the status updates from ImmersionRC timing device(s) and sends
the data via 900Mhz data radios (XBee).

Example:
        $ python scrape.py

Todo:
    # Make the script also work by directly calling MQTT over ethernet, use config
    # variable to choose ethernet vs XBee

"""

import time
import os.path
import serial
from xbee import ZigBee

# TODO
# Make the script also work by directly calling MQTT over ethernet, use config
# variable to choose etherent vs XBee

# Variable Setup
# XBee
XBEE_PORT = '/dev/ttyUSB0'
XBEE_BAUD = 115200
DATA_ADDRESS_LONG = '\x00\x00\x00\x00\x00\x00\xFF\xFF'
DATA_ADDRESS = '\xFF\xFF'

# Timer
FIRST_TIMER_PORT = '/dev/ttyACM5'
TIMER_PORTS = ['/dev/ttyACM3', '/dev/ttyACM4', '/dev/ttyACM5', '/dev/ttyACM6', '/dev/ttyACM7']
TIMER_BAUD = 115200
# Set a trigger threshold for the first pass over as the LapRF doesn't indicate
# a lap has started.
TRIGGER_THRESHOLD = 1200

# Have we seen the XBee & LapRF and then set them up?
SETUP_COMPLETED = False

# These will be set to False once we see a quad trigger a channel for the first
# time.
CHANNEL_1_FIRST_PASS = True
CHANNEL_2_FIRST_PASS = True
CHANNEL_3_FIRST_PASS = True
CHANNEL_4_FIRST_PASS = True
CHANNEL_5_FIRST_PASS = True
CHANNEL_6_FIRST_PASS = True
CHANNEL_7_FIRST_PASS = True
CHANNEL_8_FIRST_PASS = True


def process_laptime(line_from_serial, channel):
    """
    Take the laptime serial string, hacks it up and send it over the
    XBee.
    """
    channel_time = line_from_serial.strip('\r\n').split(':').pop()
    laptime_status = "C" + str(channel) + ":" + str(int(time.time())) + ":" + \
        str(round(float(channel_time), 3))
    print laptime_status
    xbee_send(laptime_status)
    return False


def process_status_triggered(channel):
    """
    Send a status over XBee that a channel has been triggered (based upon
    seeing a signal over noise threshold).
    """
    triggered_status = "C" + str(channel) + ":!"
    print triggered_status
    xbee_send(triggered_status)
    return False


def process_status_voltage(line_list_from_serial):
    """Send a battery status over XBee."""
    voltage = line_list_from_serial[0].split(' ').pop()
    voltage_status = "V:" + str(round(float(voltage), 2))
    print voltage_status
    xbee_send(voltage_status)


def xbee_send(data):
    """Function for sending data over XBee."""
    XBEE.send("tx", data=data, dest_addr_long=DATA_ADDRESS_LONG,
              dest_addr=DATA_ADDRESS)


def minimal_devices_present():
    """
    Check that the LapRF and the XBee are plugged in, otherwise the script
    crashes because they don't exist and this code will run headless.
    """
    return os.path.exists(FIRST_TIMER_PORT) and os.path.exists(XBEE_PORT)


while True:
    try:
        # Once our devices are plugged in, check if setup has been completed,
        # if not, run setup.
        # Once setup has been run, kick off the rest of the code.
        if minimal_devices_present():
            if not SETUP_COMPLETED:
                # XBee Setup
                print "[+] Devices detected, performing Setup"
                XBEE_SERIAL = serial.Serial(XBEE_PORT, XBEE_BAUD)
                XBEE = ZigBee(XBEE_SERIAL)
                LAPTIMER_LIST = []
                for DEVICE in TIMER_PORTS:
                    try:
                        LAPTIMER_LIST.append(serial.Serial(DEVICE, TIMER_BAUD, timeout=1))
                    except IOError:
                        pass
                SETUP_COMPLETED = True

            # Read status update from LapRF as a single string as well as
            # creating a list.
            for DEVICE_LINE in LAPTIMER_LIST:
                LINE = DEVICE_LINE.readline()
                LINE_LIST = LINE.split('\t')

                # Check if status update is a laptime update, this needs to happen
                # first so that if the LapRF has already been triggered and is
                # timing laps, you don't simultaneously get triggered and a lap
                # time (happens if code below runs first).
                if "T0" in LINE:
                    CHANNEL_1_FIRST_PASS = process_laptime(LINE, 1)
                if "T1" in LINE:
                    CHANNEL_2_FIRST_PASS = process_laptime(LINE, 2)
                if "T2" in LINE:
                    CHANNEL_3_FIRST_PASS = process_laptime(LINE, 3)
                if "T3" in LINE:
                    CHANNEL_4_FIRST_PASS = process_laptime(LINE, 4)
                if "T4" in LINE:
                    CHANNEL_5_FIRST_PASS = process_laptime(LINE, 5)
                if "T5" in LINE:
                    CHANNEL_6_FIRST_PASS = process_laptime(LINE, 6)
                if "T6" in LINE:
                    CHANNEL_7_FIRST_PASS = process_laptime(LINE, 7)
                if "T7" in LINE:
                    CHANNEL_8_FIRST_PASS = process_laptime(LINE, 8)

                # Check to see if any channels have been triggered (first pass over
                # lap timer).
                if "noise" in LINE:
                    if int(LINE_LIST[2].split('.')[0]) > TRIGGER_THRESHOLD and \
                            CHANNEL_1_FIRST_PASS:
                        CHANNEL_1_FIRST_PASS = process_status_triggered(1)
                    if int(LINE_LIST[3].split('.')[0]) > TRIGGER_THRESHOLD and \
                            CHANNEL_2_FIRST_PASS:
                        CHANNEL_2_FIRST_PASS = process_status_triggered(2)
                    if int(LINE_LIST[4].split('.')[0]) > TRIGGER_THRESHOLD and \
                            CHANNEL_3_FIRST_PASS:
                        CHANNEL_3_FIRST_PASS = process_status_triggered(3)
                    if int(LINE_LIST[5].split('.')[0]) > TRIGGER_THRESHOLD and \
                            CHANNEL_4_FIRST_PASS:
                        CHANNEL_4_FIRST_PASS = process_status_triggered(4)
                    if int(LINE_LIST[6].split('.')[0]) > TRIGGER_THRESHOLD and \
                            CHANNEL_5_FIRST_PASS:
                        CHANNEL_5_FIRST_PASS = process_status_triggered(5)
                    if int(LINE_LIST[7].split('.')[0]) > TRIGGER_THRESHOLD and \
                            CHANNEL_6_FIRST_PASS:
                        CHANNEL_6_FIRST_PASS = process_status_triggered(6)
                    if int(LINE_LIST[8].split('.')[0]) > TRIGGER_THRESHOLD and \
                            CHANNEL_7_FIRST_PASS:
                        CHANNEL_7_FIRST_PASS = process_status_triggered(7)
                    if int(LINE_LIST[9].split('.')[0]) > TRIGGER_THRESHOLD and \
                            CHANNEL_8_FIRST_PASS:
                        CHANNEL_8_FIRST_PASS = process_status_triggered(8)
                    else:
                        process_status_voltage(LINE_LIST)
        else:
            print "[-] Waiting for devices to activate"
            time.sleep(5)
    except KeyboardInterrupt:
        break

if SETUP_COMPLETED:
    XBEE_SERIAL.close()
    for DEVICE in LAPTIMER_LIST:
        DEVICE.close()

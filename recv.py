#!/bin/python

"""
This module receives the status updates from the scrape script via the XBee's
and publishes the information to the MQTT broker.

Example:
        $ python recv.py

"""

import sys
import serial
from xbee import ZigBee
import paho.mqtt.client as mqtt

# Variable Setup
XBEE_PORT = '/dev/ttyUSB1'
XBEE_BAUD = 115200
BROKER_ADDRESS = '127.0.0.1'

# XBee Setup
try:
    XBEE_SERIAL = serial.Serial(XBEE_PORT, XBEE_BAUD)
    XBEE = ZigBee(XBEE_SERIAL)
except IOError:
    print "[!] Can't connect to XBee, is it plugged in or on a different port?"
    sys.exit(0)


# MQTT Setup
MQTTC = mqtt.Client()
try:
    MQTTC.connect(BROKER_ADDRESS)
except IOError:
    print "[!] Can't connect to MQTT broker, is it running?"
    sys.exit(0)


def process_triggered(channel):
    """Send True to a triggered channel topic"""
    topic = "laprf/C" + channel + "_triggered"
    MQTTC.publish(topic, "True")


def process_laptime(channel, timestamp, laptime):
    """Send a epoch timestamp and laptime to a channel topic"""
    topic = "laprf/C" + channel + "_laptime"
    MQTTC.publish(topic, "C" + channel + ":" + timestamp + ":" + laptime)


while True:
    try:
        RESPONSE = XBEE.wait_read_frame()
        print RESPONSE["rf_data"]
        STATUS = RESPONSE["rf_data"].split(':')
        if STATUS[0] == "V":
            MQTTC.publish("laprf/battery_STATUS", STATUS[1])
        if STATUS[1] == "!":
            process_triggered(STATUS[0][1])
        if STATUS[0][0] == "C" and STATUS[1] != \
                "!":
            process_laptime(STATUS[0][1], STATUS[1], STATUS[2])
            print STATUS
    except KeyboardInterrupt:
        break

XBEE_SERIAL.close()
MQTTC.disconnect()

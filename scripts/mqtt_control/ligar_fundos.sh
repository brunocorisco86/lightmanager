#!/bin/bash
mosquitto_pub -h 192.168.1.7 -u bruno -P blurbang -t "home/outdoor/fundos/set" -m "ON"

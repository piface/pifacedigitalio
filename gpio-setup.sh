#!/bin/bash
#: Description: Sets up permissions for the gpio devices
#:      Author: Thomas Preston

udev_rules_file='/etc/udev/rules.d/51-gpio.rules'
rule="SUBSYSTEM==\"gpio*\", PROGRAM=\"/bin/sh -c 'chown -R root:gpio /sys/class/gpio && chmod -R 770 /sys/class/gpio; chown -R root:gpio /sys/devices/virtual/gpio && chmod -R 770 /sys/devices/virtual/gpio'\""

# check if the script is being run as root
if [[ $EUID -ne 0 ]]
then
	printf 'This script must be run as root.\nExiting..\n'
	exit 1
fi

# check that the rules file doesn't already exist
if [ -f $udev_rules_file ]
then
	printf 'The gpio rules file already exists.\nExiting...\n'
	exit 0
fi

# create the rule
printf 'Creating udev rule\n'
echo  $rule > $udev_rules_file
groupadd gpio
gpasswd -a pi gpio

printf 'User "pi" can now access the virtual gpio devices.\n'
printf 'Please REBOOT for the changes to take effect.\n'

#!/bin/bash
#: Description: Sets up permissions for the spi devices
#:      Author: Thomas Preston

udev_rules_file='/etc/udev/rules.d/50-spi.rules'

# check if the script is being run as root
if [[ $EUID -ne 0 ]]
then
	printf 'This script must be run as root.\nExiting..\n'
	exit 1
fi

# check that the rules file doesn't already exist
if [ -f $udev_rules_file ]
then
	printf 'The spi rules file already exists.\nExiting...\n'
	exit 1
fi


# create the rules file
printf 'Creating udev rule\n'
echo 'KERNEL=="spidev*", GROUP="spiuser", MODE="0660"' > $udev_rules_file

groupadd spiuser # create the spiuser group
gpasswd -a pi spiuser # add pi to the spiuser group
gpasswd -a www-data spiuser # add the webserver user to the spiuser group

printf 'User "pi" can now access the /dev/spidev* devices\n'
printf 'Please REBOOT for the changes to take effect\n'

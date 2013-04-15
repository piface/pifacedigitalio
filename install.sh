#!/bin/bash
#: Description: Installs pifacedigitalio and its dependecies

# check if the script is being run as root
if [[ $EUID -ne 0 ]]
then
	printf 'This script must be run as root.\nExiting..\n'
	exit 1
fi

# depends on gpio-admin (no point re-inventing the wheel)
type gpio-admin > /dev/null 2>&1 # is it installed?
if [ $? -ne 0 ]
then
    # install gpio-admin
    printf "Installing gpio-admin...\n"
    git clone https://github.com/quick2wire/quick2wire-gpio-admin.git
    cd quick2wire-gpio-admin
    make
    make install
    gpasswd -a pi gpio
    cd -
    printf "\n"
fi

# set up spidev permissions
./spidev-setup.sh
if [ $? -ne 0 ]
then
    printf "Failed to setup spidev.\nExiting...\n"
    exit 1
fi

# install python library
printf "Installing pifacedigitalio...\n"
python3 setup.py install
printf "Done!\n"

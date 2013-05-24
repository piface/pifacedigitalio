#!/bin/bash
#: Description: Installs pifacedigitalio and its dependecies

# check if the script is being run as root
if [[ $EUID -ne 0 ]]
then
	printf 'This script must be run as root.\nExiting..\n'
	exit 1
fi

# depends on pifacecommon
python3 -c "import pifacecommon" # is it installed?
if [ $? -ne 0 ]
then
    # install pifacecommon
    printf "Downloading pifacecommon...\n"
    git clone https://github.com/piface/pifacecommon.git
    cd pifacecommon
    #python3 setup.py install
    ./install.sh
    cd -
    printf "\n"
fi

# set up gpio permissions
./gpio-setup.sh
if [ $? -ne 0 ]
then
    printf "Failed to setup gpio.\nExiting...\n"
    exit 1
fi

# install python library
printf "Installing pifacedigitalio...\n"
python3 setup.py install
printf "Done!\n"

#!/bin/bash
#: Description: Installs pifacedigitalio and its dependecies

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

printf "Installing pifacedigitalio...\n"
python3 setup.py install
printf "Done!\n"

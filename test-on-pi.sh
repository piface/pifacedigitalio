#!/bin/bash
#: Decription: Tests module on a Raspberry Pi.

RPI_USER='pi'
RPI_HOST=$1
RPI_PROJECT_DIR='/home/pi/project_test'
PROJECT_NAME='pifacedigitalio'  # no spaces, please
TEST='python3 tests.testrig.py'

if [ -n "$RPI_HOST" ]; then
    echo "Running '$TEST' on $RPI_USER@$RPI_HOST."
else
    echo "Usage: $0 IP_ADDRESS"
    exit 1
fi

# make the project directory
ssh $RPI_USER@$RPI_HOST "mkdir -p $RPI_PROJECT_DIR/$PROJECT_NAME" &&

# copy this whole directory to a Raspberry Pi
rsync -ar * $RPI_USER@$RPI_HOST:$RPI_PROJECT_DIR/$PROJECT_NAME/ &&

# run the tests
ssh $RPI_USER@$RPI_HOST "cd $RPI_PROJECT_DIR/$PROJECT_NAME && $TEST"

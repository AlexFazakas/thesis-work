#!/bin/bash
set -e

if [ $# -ne 1 ] ; then
    echo "This should be run with one argument: the URL which the reports \
should be sent to (including the /add_report part)"
    exit 1
fi

sudo apt-get update
sudo apt-get install python3-pip -y
pip3 install --user pyinotify

sudo apt-get install apport -y
sudo apt-get install apport-retrace -y

sudo mkdir /etc/report_monitor
sudo echo ${1} > target.txt
sudo cp target.txt /etc/report_monitor/
sudo cp monitor.py /etc/report_monitor
sudo cp report_monitor.service /etc/systemd/system/report_monitor.service
sudo systemctl enable report_monitor
sudo systemctl start report_monitor

rm -f target.txt
rm -f monitor.py
rm -f report_monitor.service
#!/bin/bash

if [ ! -f "./moneykeeper.py" ] && [ ! -f "./moneykeeper.desktop" ];
then
    echo "please run this file from the base directory"
    exit 1
fi

if [ "$(id -u)" -eq 0 ];
then
    echo "please execute do NOT run as root"
    exit 1
fi

sudo cp ./moneykeeper.py /usr/local/bin/moneykeeper

if [ -d ~/.config/autostart ];
then
    cp ./moneykeeper.desktop ~/.config/autostart
else
    echo "skipping startup unable to locate ~/.config/autostart"
fi
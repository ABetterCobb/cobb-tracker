#!/usr/bin/env bash
cd scripts/
pip install cobb-tracker*.tar.gz 
mkdir -p /root/.config/cobb_tracker
cp config.ini /root/.config/cobb_tracker/config.ini

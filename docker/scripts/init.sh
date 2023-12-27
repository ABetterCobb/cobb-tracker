#!/usr/bin/env bash
cd scripts/

pip install cobb-tracker*.tar.gz 
apt-get update
apt-get install tesseract-ocr -y

mkdir -p /root/.config/cobb_tracker
cp config.ini /root/.config/cobb_tracker/config.ini

mkdir -p /var/db/
cd .. && rm -rf /scripts/

#!/usr/bin/env bash
cd $(git rev-parse --show-toplevel)
python -m build --outdir docker/scripts
cd docker/
sudo docker build . --tag abettercobb/cobb-tracker 

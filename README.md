# Cobb Tracker

Tool that pulls meeting minutes for the local governments in Cobb County

```
usage: main.py [-h] -m MUNICIPALITY

options:
  -h, --help            show this help message and exit
  -m MUNICIPALITY, --municipality MUNICIPALITY
```
## Installation

``` 
git clone https://github.com/ABetterCobb/cobb-tracker.git
cd cobb-tracker
pip install .
```
## Running From Docker

```
git clone https://github.com/ABetterCobb/cobb-tracker.git
cd cobb-tracker
docker build . --tag abettercobb/cobb-tracker
mkdir minutes
docker run -v $(pwd)/minutes:/minutes -it abettercobb/cobb-tracker cobb-tracker -m <municipality>
```

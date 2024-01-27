# Cobb Tracker
Tool that pulls meeting minutes for the local governments in Cobb County.

## The Problem

Each city in Cobb County, and the county itself, stores the minutes they hold for meetings
in different ways and the data is also presented very differently. Almost every city in the
county uses a different provider for the websites where they present this information to the 
public.

This makes it hard for average citizens and journalists to look through all of this info. 
There's no way to search for things you care about or follow up on events that took place
without just flat out remembering or manually searching by looking through a bunch of 
PDFs that may or may not have searchable text.

## A Solution

This tool allows us to take a bunch of PDF file links, feed them into a "downloader" 
and then convert those PDFs into text that are put into an sqlite3 database. The design allows websites to be pluggable.

Take for example Marietta's website and Smyrna's website. They both are run on completely different
platforms, but if we can get all of the links to all of the minutes files they have available we
can treat them like the same site. 

The PDFs are then converted into plain text with Tesseract OCR, and stored in an SQLite database. You can then search through this database with key terms that appear in the minutes text, filter for certain dates, municipalities and types of meetings.

We're currently using [Datasette](https://datasette.io/) to present this information, you can see it [here](https://data.wastebit.org/)

## Requirements
- Python 3.11
- Tesseract
- Linux or MacOS (May work in WSL).
- Docker

## Installation

``` 
git clone https://github.com/ABetterCobb/cobb-tracker.git
cd cobb-tracker
poetry install && poetry shell
```

## Usage 

```
usage: cobb-tracker [-h] [-m MUNICIPALITY] [-p] [-a] [-f] [-v]

options:
  -h, --help            show this help message and exit
  -m MUNICIPALITY, --municipality MUNICIPALITY
                        The city that you want to download minutes for. This
                        includes Cobb.
  -p, --push-to-database
                        The existing minutes that you have will be converted
                        to text and pushed to a database
  -a, --pull-all-cities
                        All cities will have their minutes downloaded
  -f, --force           Force rewriting of minutes files that already exist
  -v, --verbose         More information will be printed

```

## Current Limitations
This program is in early stages, there are a few things that are not yet implemented or may never be.

### Laserfische WebLink
Laserfische WebLink doesn't have permanent links to files, and instead download links are generated upon user request. In order for Laserfische to be scraped we essentially need to implemented a way to "walk down" the psuedo file system they have with a persistent user session. 

### PDFs need to have proper metadata associated with them
If for a given PDF and there is no date data, no meeting data, etc, you will have to make up data or the PDFs will not be unique when they are written to the filesystem.

## Authors
- Sam Foster
- Tyler Bigler

## License
cobb-tracker is licensed under GPL 3.0.

## Acknowledgments
Philip James for presenting the core idea in [this video](https://www.youtube.com/watch?v=fHsMZ3cuMhU)
import sys
import argparse
import municipalities.marietta
import municipalities.cobb

def choose_muni(municipality: str):
    muni = municipality.lower()

    if muni == "marietta":
        municipalities.marietta.get_minutes_docs()
    if muni == "cobb":
        municipalities.cobb.get_minutes_docs()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
            "-m",
            "--municipality",
            type=str,
            required=True
            )
    args = parser.parse_args()
    choose_muni(args.municipality)

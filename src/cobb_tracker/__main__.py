import sys
import argparse
from cobb_tracker.municipalities import marietta
from cobb_tracker.municipalities import cobb
from cobb_tracker.pdf_parse import pdf_to_database
from cobb_tracker.cobb_config import cobb_config

def choose_muni(municipality: str, config: cobb_config):
    """Chooses what module to run base on the municipality that is entered
    Args:
        municipality (str): Where are you?    
    """
    muni = municipality.lower()

    if muni == "marietta":
        marietta.get_minutes_docs()
    elif muni == "cobb":
        cobb.get_minutes_docs(config=config)

def main():
    parser =  argparse.ArgumentParser()
    parser.add_argument(
            "-m",
            "--municipality",
            type=str,
            )
    parser.add_argument(
            "-p",
            "--push-to-database",
            action="store_true",
            )
    args = parser.parse_args()
    if args.push_to_database is False and args.municipality is None:
        print("You must specify -m/--municipality if -p/--push-to-database is not selected")
        sys.exit()

    config = cobb_config()
    if args.municipality is not None:
        choose_muni(args.municipality, config)

    if args.push_to_database:
        pdf_to_database(config)

if __name__ == "__main__":
    main()

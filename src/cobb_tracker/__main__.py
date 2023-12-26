import sys
import os
import argparse
from cobb_tracker.municipalities import marietta, cobb, smyrna
from cobb_tracker.pdf_parse import DatabaseOps
from cobb_tracker.cobb_config import CobbConfig

def choose_muni(municipality: str, config: CobbConfig):
    """Chooses what module to run base on the municipality that is entered
    Args:
        municipality (str): Where are you?    
    """
    muni = municipality.lower()
    if muni == "marietta":
        marietta.get_minutes_docs(config=config)

    elif muni == "cobb":
        cobb.get_minutes_docs(config=config)

    elif muni == "smyrna":
        smyrna.get_minutes_docs(config=config)
    else:
        print("Municipality not recognized")
def main():
    if os.name != "posix":
        print("Error: cobb-tracker will only work Unix-like systems")
        sys.exit()
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
        print("error: You must specify -m/--municipality if -p/--push-to-database is not selected")
        sys.exit()

    config = CobbConfig()
    if args.municipality is not None:
        choose_muni(args.municipality, config)

    if args.push_to_database:
        pdf_to_db = DatabaseOps(config)
        pdf_to_db.pdf_to_database()

if __name__ == "__main__":
    main()

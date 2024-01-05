import sys
import os
import argparse
from cobb_tracker.municipalities import (marietta,
                                         civicplus,
                                         smyrna,
                                         acworth,
                                         powdersprings,
                                         austell,
                                         novusagenda
                                         )
from cobb_tracker.pdf_parse import DatabaseOps
from cobb_tracker.cobb_config import CobbConfig

def choose_muni(municipality: str, config: CobbConfig):
    """Chooses what module to run base on the municipality that is entered
    Args:
        municipality (str): Where are you?    
    """
    muni = municipality.lower()
    if muni == "marietta" or config.args.pull_all_cities:
        marietta.get_minutes_docs(config=config)

    if muni == "cobb" or config.args.pull_all_cities:
        cobb_civic = civicplus.CivicPlus(base_url="https://cobbcoga.api.civicclerk.com/v1", muni="Cobb")
        cobb_civic.get_minutes_docs(config=config)

    if muni == "austell" or config.args.pull_all_cities:
        austell.get_minutes_docs(config=config)

    if muni == "acworth" or config.args.pull_all_cities:
        acworth.get_minutes_docs(config=config)
    
    if muni == "powdersprings" or config.args.pull_all_cities:
        powdersprings.get_minutes_docs(config=config) 

    if muni == "kennesaw" or config.args.pull_all_cities:
        kennesaw_civic = civicplus.CivicPlus(base_url="https://kennesawga.api.civicclerk.com/v1", muni="Kennesaw")
        kennesaw_civic.get_minutes_docs(config=config)
        novusagenda.get_minutes_docs(config=config)

    if muni == "smyrna" or config.args.pull_all_cities:
        smyrna.get_minutes_docs(config=config)

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
    parser.add_argument(
            "-a",
            "--pull-all-cities",
            action="store_true",
            )
    parser.add_argument(
            "-f",
            "--force",
            action="store_true",
            )
    args = parser.parse_args()
    if args.push_to_database is False and args.municipality is None and args.pull_all_cities is None:
        print("error: You must specify -m/--municipality if -p/--push-to-database is not selected")
        sys.exit()

    if args.pull_all_cities is True and args.municipality is not None:
        print("error: -m/--municipality and -a/--pull-all-cities are mutually exclusive")
        sys.exit()


    config = CobbConfig(flags=args)
    if args.municipality is not None:
        choose_muni(args.municipality, config)
    if args.municipality is None:
        choose_muni("all", config)

    if args.push_to_database:
        pdf_to_db = DatabaseOps(config)
        pdf_to_db.pdf_to_database()

if __name__ == "__main__":
    main()

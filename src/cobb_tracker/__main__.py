"""
Entry point for cobb-tracker
"""
import sys
import logging
import os
import argparse
from cobb_tracker.municipalities import (
    marietta,
    civicplus,
    smyrna,
    acworth,
    powdersprings,
    austell,
    novusagenda,
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
        cobb_civic = civicplus.CivicPlus(
            base_url="https://cobbcoga.api.civicclerk.com/v1", muni="Cobb"
        )
        cobb_civic.get_minutes_docs(config=config)

    if muni == "austell" or config.args.pull_all_cities:
        austell.get_minutes_docs(config=config)

    if muni == "acworth" or config.args.pull_all_cities:
        acworth.get_minutes_docs(config=config)

    if muni == "powdersprings" or config.args.pull_all_cities:
        powdersprings.get_minutes_docs(config=config)

    if muni == "kennesaw" or config.args.pull_all_cities:
        kennesaw_civic = civicplus.CivicPlus(
            base_url="https://kennesawga.api.civicclerk.com/v1",
            muni="Kennesaw"
        )
        kennesaw_civic.get_minutes_docs(config=config)
        novusagenda.get_minutes_docs(config=config)

    if muni == "smyrna" or config.args.pull_all_cities:
        smyrna.get_minutes_docs(config=config)


def main():
    """Start point of the program
    """
    if os.name != "posix":
        logging.error("cobb-tracker will only work Unix-like systems")
        sys.exit()
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-m",
        "--municipality",
        type=str,
        help="The city that you want to download minutes for" +
             ". This includes Cobb."
    )
    parser.add_argument(
        "-p",
        "--push-to-database",
        action="store_true",
        help="The existing minutes that you have will be converted " +
             "to text and pushed to a database"
    )
    parser.add_argument(
        "-a",
        "--pull-all-cities",
        action="store_true",
        help="All cities will have their minutes downloaded"
    )
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Force rewriting of minutes files that already exist"
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="More information will be printed"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(
            format="%(levelname)s: %(message)s",
            encoding="utf-8", level=logging.INFO
        )
    else:
        logging.basicConfig(
            format="%(levelname)s: %(message)s",
            encoding="utf-8", level=logging.WARNING
        )

    if (
        args.push_to_database is False
        and args.municipality is None
        and args.pull_all_cities is None
    ):
        logging.error(
            "You must specify -m/--municipality" +
            "if -p/--push-to-database is not selected"
        )
        sys.exit()

    if args.pull_all_cities is True and args.municipality is not None:
        logging.error(
            "-m/--municipality and -a/--pull-all-cities are mutually exclusive"
        )
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

import sys
import argparse
from cobb_tracker.municipalities import marietta
from cobb_tracker.municipalities import cobb
import pdf_parse
from cobb_config import cobb_config

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
    parser.add_argument(
            "-m",
            "--municipality",
            type=str,
            required=True
            )
    parser.add_argument(
            "-p",
            "--push-to-database",
            action="store_true",
            )
    args = parser.parse_args()
    config = cobb_config()
    print(config.get_config("directories","minutes_dir"))
    choose_muni(args.municipality, config)

    if args.push_to_database:
        pdf_parse.write_to_database(
                minutes_dir=config.get_config("directories","minutes_dir"),
                database_dir=config.get_config("directories","database_dir")
                )

if __name__ == "__main__":
    main()

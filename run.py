import argparse
import inspect
import os
import yaml
import logging

from pippin.manager import Manager

if __name__ == "__main__":
    # Set up command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("config", help="the name of the yml config file to run. For example: configs/default.yml")
    args = parser.parse_args()

    # Initialise logging
    logging.basicConfig(level=logging.DEBUG, format="[%(levelname)7s |%(filename)20s:%(lineno)3d |%(funcName)20s]   %(message)s")

    # Get base filename
    config_filename = os.path.basename(args.config).split(".")[0].upper()

    # Load YAML config file
    config_path = os.path.dirname(inspect.stack()[0][1]) + args.config
    assert os.path.exists(config_path), f"File {config_path} cannot be found."
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    manager = Manager(config_filename, config)
    manager.execute()


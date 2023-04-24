"""sottovuoto: a tight variable packing tool for solidity.

sottovuoto analyzes the struct and storage packing of a single
or list of contracts from the filesystem and provides an
optimized order which uses less storage slots.

Typical usage example:
    sottovuoto --folder ./ [--debug]

"""

import argparse
import logging
from pathlib import Path
import sys
from sottovuoto.sottovuoto import Sottovuoto

log = logging.getLogger("sottovuoto")
log.setLevel(logging.INFO)

def main():
    """Entrypoint for the sottovuoto cli tool"""

    parser = argparse.ArgumentParser(
        description="sottovuoto: a tight variable packing tool for solidity")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--contract",
                        help="the contract to analyze",
                        default=None)
    group.add_argument("--folder",
                    help="the contracts folder: it will handle all .sol files",
                    default=None)
    parser.add_argument("-d", "--debug", help="enable debug logs",
                        action="store_true")

    args = parser.parse_args()

    if args.debug:
        log.setLevel(logging.DEBUG)

    if args.contract:
        files_to_analyze = [args.contract]
    elif args.folder:
        files_to_analyze = [
            str(file) for file in Path(args.folder).rglob('*.sol')
            ]
    else:
        parser.print_help()
        sys.exit(1)

    log.debug(f"we are going to analyze these files: {files_to_analyze}")

    for file in files_to_analyze:
        sottovuoto = Sottovuoto(file)
        sottovuoto.output(sottovuoto.analyze_packing(), "stdout")

if __name__ == "__main__":
    main()

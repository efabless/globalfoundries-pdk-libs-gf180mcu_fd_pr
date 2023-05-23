# Copyright 2023 GlobalFoundries PDK Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Usage:
  convert_foundry_csv.py --excel_path=<path> --device_type=<device_type>

  --excel_path=<path>             The input excel file for measured data you need to extract
  --device_type=<device_type>     Name of device need to extracted its data
  -h, --help                      Show help text.
  -v, --version                   Show version.
"""

from docopt import docopt
import pandas as pd
import numpy as np
import os
import logging
from fets_iv_extraction import fet_iv_meas_extraction
from fets_cv_extraction import fet_cv_meas_extraction
from cap_cv_extraction import cap_meas_extraction


def main(args):
    """
    main function to extract measurement data for GF180MCU models.

    Parameters
    ----------
    arguments : dict
        Dictionary that holds the arguments used by user in the run command. This is generated by docopt library.
    Returns
    -------
        None
    """

    # Assign some args to variables to be used later
    excel_path = args["--excel_path"]
    dev_type = args["--device_type"]

    # Verify the measurement data file is exist or no
    if not os.path.exists(excel_path) or not os.path.isfile(excel_path):
        logging.error(
            f"Provided {excel_path} excel sheet doesn't exist, please recheck"
        )
        exit(1)

    # Checking that selected device is supported.
    if "fet" in dev_type:
        df = pd.read_excel(excel_path)
        logging.info(f"Starting data extraction from {excel_path} sheet for {dev_type} device")

        if 'iv' in excel_path:
            # Extracting data for FETs-IV measurement
            fet_iv_meas_extraction(df, dev_type)
        else:
            # Extracting data for FETs-CV measurement
            fet_cv_meas_extraction(df, dev_type)

    elif "cap_mos" in dev_type or "cap_mim" in dev_type:
        df = pd.read_excel(excel_path)
        logging.info(f"Starting data extraction from {excel_path} sheet for {dev_type} device")
        # Extracting data for MOSCAP/MIMCAP devices for CV measurement
        cap_meas_extraction(df, dev_type)

    else:
        logging.error("Suported devices are: Fets, MOSCAP")
        exit(1)


if __name__ == "__main__":

    # Args
    arguments = docopt(__doc__, version="DATA EXTRACTOR: 0.1")

    # logging setup
    logging.basicConfig(
        level=logging.DEBUG,
        handlers=[logging.StreamHandler(), ],
        format="%(asctime)s | %(levelname)-7s | %(message)s",
        datefmt="%d-%b-%Y %H:%M:%S",
    )

    # Calling main function
    main(arguments)

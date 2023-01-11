# Copyright 2022 GlobalFoundries PDK Authors
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
  models_regression.py [--num_cores=<num>]

  -h, --help             Show help text.
  -v, --version          Show version.
  --num_cores=<num>      Number of cores to be used by simulator
"""

from unittest.mock import DEFAULT
from docopt import docopt
import pandas as pd
import numpy as np
import os
from jinja2 import Template
import concurrent.futures
import shutil
import multiprocessing as mp
import logging

import subprocess
import glob

pd.options.mode.chained_assignment = None  # default='warn'
# constants
PASS_THRESH = 2.0
MOS = [0, -0.825, -1.65, -2.48, -3.3]
PMOS3P3_VPS = [0, 0.825, 1.65, 2.48, 3.3]
NMOS6P0_VPS = [0, -0.75, -1.5, -2.25, -3]
PMOS6P0_VPS = [0, 0.75, 1.5, 2.25, 3]
# nmos6p0_nat_vbs = [0, -0.75, -1.5, -2.25, -3]
# #######################


def ext_measured(dev_data_path, device):
    """Extracting the measured data of  devices from excel sheet

    Args:
         dev_data_path(str): path to the data sheet
         devices(str):  undertest device

    Returns:
         dfs(pd.DataFrame): A data frame contains all extracted data

    """

    # Read Data
    read_file = pd.read_excel(dev_data_path)
    read_file.to_csv(f"mos_iv_regr/{device}/{device}.csv", index=False, header=True)
    df = pd.read_csv(f"mos_iv_regr/{device}/{device}.csv")
    loops = df["L (um)"].count()
    all_dfs = []

    if device == "pfet_03v3_iv" or device == "pfet_03v3_dss_iv":
        mos = PMOS3P3_VPS
    elif device == "pfet_06v0_iv" or device == "pfet_06v0_dss_iv":
        mos = PMOS6P0_VPS
    elif device == "nfet_06v0_iv" or device == "nfet_06v0_nvt_iv" or device == "nfet_06v0_dss_iv":
        mos = NMOS6P0_VPS
    else:
        mos = MOS

    width = df["W (um)"].iloc[0]
    length = df["L (um)"].iloc[0]
    # for pmos
    if device in ["pfet_03v3_iv", "pfet_06v0_iv","pfet_03v3_dss_iv", "pfet_06v0_dss_iv"]:
        idf = df[
            [
                "-Id (A)",
                "-vgs ",
                "vbs =0",
                f"vbs ={mos[1]}",
                f"vbs ={mos[2]}",
                f"vbs ={mos[3]}",
                f"vbs ={mos[4]}",
            ]
        ].copy()
        idf.rename(
            columns={
                "-vgs ": "vgs",
                "vbs =0": "measured_vbs0 =0",
                f"vbs ={mos[1]}": f"measured_vbs0 ={mos[1]}",
                f"vbs ={mos[2]}": f"measured_vbs0 ={mos[2]}",
                f"vbs ={mos[3]}": f"measured_vbs0 ={mos[3]}",
                f"vbs ={mos[4]}": f"measured_vbs0 ={mos[4]}",
            },
            inplace=True,
        )
    else:
        # for nmos
        idf = df[
            [
                "Id (A)",
                "vgs ",
                "vbs =0",
                f"vbs ={mos[1]}",
                f"vbs ={mos[2]}",
                f"vbs ={mos[3]}",
                f"vbs ={mos[4]}",
            ]
        ].copy()
        idf.rename(
            columns={
                "vgs ": "vgs",
                "vbs =0": "measured_vbs0 =0",
                f"vbs ={mos[1]}": f"measured_vbs0 ={mos[1]}",
                f"vbs ={mos[2]}": f"measured_vbs0 ={mos[2]}",
                f"vbs ={mos[3]}": f"measured_vbs0 ={mos[3]}",
                f"vbs ={mos[4]}": f"measured_vbs0 ={mos[4]}",
            },
            inplace=True,
        )

    idf.dropna(inplace=True)
    idf["W (um)"] = width
    idf["L (um)"] = length
    idf["temp"] = 25

    all_dfs.append(idf)
    # temperature

    temp_range = int(2 * loops / 3)
    for i in range(loops * 2 - 1):
        width = df["W (um)"].iloc[int(0.5 * i)]
        length = df["L (um)"].iloc[int(0.5 * i)]
        if i in range(0, temp_range):
            temp = 25
        elif i in range(temp_range, 2 * temp_range):
            temp = -40
        else:
            temp = 125

        if device in ["pfet_03v3_iv", "pfet_06v0_iv","pfet_03v3_dss_iv", "pfet_06v0_dss_iv"]:
            if i == 0:
                idf = df[
                    [
                        "-vgs (V)",
                        f"vbs =0.{i+1}",
                        f"vbs ={mos[1]}.{i+1}",
                        f"vbs ={mos[2]}.{i+1}",
                        f"vbs ={mos[3]}.{i+1}",
                        f"vbs ={mos[4]}.{i+1}",
                    ]
                ].copy()

                idf.rename(
                    columns={
                        "-vgs (V)": "vgs",
                        f"vbs =0.{i+1}": f"measured_vbs{i+1} =0",
                        f"vbs ={mos[1]}.{i+1}": f"measured_vbs{i+1} ={mos[1]}",
                        f"vbs ={mos[2]}.{i+1}": f"measured_vbs{i+1} ={mos[2]}",
                        f"vbs ={mos[3]}.{i+1}": f"measured_vbs{i+1} ={mos[3]}",
                        f"vbs ={mos[4]}.{i+1}": f"measured_vbs{i+1} ={mos[4]}",
                    },
                    inplace=True,
                )
            else:
                idf = df[
                    [
                        f"-vgs (V).{i}",
                        f"vbs =0.{i+1}",
                        f"vbs ={mos[1]}.{i+1}",
                        f"vbs ={mos[2]}.{i+1}",
                        f"vbs ={mos[3]}.{i+1}",
                        f"vbs ={mos[4]}.{i+1}",
                    ]
                ].copy()

                idf.rename(
                    columns={
                        f"-vgs (V).{i}": "vgs",
                        f"vbs =0.{i+1}": f"measured_vbs{i+1} =0",
                        f"vbs ={mos[1]}.{i+1}": f"measured_vbs{i+1} ={mos[1]}",
                        f"vbs ={mos[2]}.{i+1}": f"measured_vbs{i+1} ={mos[2]}",
                        f"vbs ={mos[3]}.{i+1}": f"measured_vbs{i+1} ={mos[3]}",
                        f"vbs ={mos[4]}.{i+1}": f"measured_vbs{i+1} ={mos[4]}",
                    },
                    inplace=True,
                )
        else:
            if i == 0:
                idf = df[
                    [
                        "vgs (V)",
                        f"vbs =0.{i+1}",
                        f"vbs ={mos[1]}.{i+1}",
                        f"vbs ={mos[2]}.{i+1}",
                        f"vbs ={mos[3]}.{i+1}",
                        f"vbs ={mos[4]}.{i+1}",
                    ]
                ].copy()

                idf.rename(
                    columns={
                        "vgs (V)": "vgs",
                        f"vbs =0.{i+1}": f"measured_vbs{i+1} =0",
                        f"vbs ={mos[1]}.{i+1}": f"measured_vbs{i+1} ={mos[1]}",
                        f"vbs ={mos[2]}.{i+1}": f"measured_vbs{i+1} ={mos[2]}",
                        f"vbs ={mos[3]}.{i+1}": f"measured_vbs{i+1} ={mos[3]}",
                        f"vbs ={mos[4]}.{i+1}": f"measured_vbs{i+1} ={mos[4]}",
                    },
                    inplace=True,
                )
            else:
                idf = df[
                    [
                        f"vgs (V).{i}",
                        f"vbs =0.{i+1}",
                        f"vbs ={mos[1]}.{i+1}",
                        f"vbs ={mos[2]}.{i+1}",
                        f"vbs ={mos[3]}.{i+1}",
                        f"vbs ={mos[4]}.{i+1}",
                    ]
                ].copy()

                idf.rename(
                    columns={
                        f"vgs (V).{i}": "vgs",
                        f"vbs =0.{i+1}": f"measured_vbs{i+1} =0",
                        f"vbs ={mos[1]}.{i+1}": f"measured_vbs{i+1} ={mos[1]}",
                        f"vbs ={mos[2]}.{i+1}": f"measured_vbs{i+1} ={mos[2]}",
                        f"vbs ={mos[3]}.{i+1}": f"measured_vbs{i+1} ={mos[3]}",
                        f"vbs ={mos[4]}.{i+1}": f"measured_vbs{i+1} ={mos[4]}",
                    },
                    inplace=True,
                )
        idf["W (um)"] = width
        idf["L (um)"] = length
        idf["temp"] = temp

        idf.dropna(inplace=True)
        all_dfs.append(idf)

    dfs = pd.concat(all_dfs, axis=1)
    dfs.drop_duplicates(inplace=True)
    return dfs


def call_simulator(file_name):
    """Call simulation commands to perform simulation.
    Args:
        file_name (str): Netlist file name.
    """
    return os.system(f"ngspice -b -a {file_name} -o {file_name}.log > {file_name}.log")


def run_sim(dirpath, device, width, length, temp=25):
    """Run simulation at specific information and corner
    Args:
        dirpath(str): path to the file where we write data
        device(str): the device instance will be simulated
        temp(float): a specific temp for simulation
        width(float): a specific width for simulation
        length(float): a specific length for simulation

    Returns:
        info(dict): results are stored in,
        and passed to the run_sims function to extract data
    """
    netlist_tmp = f"device_netlists_Id/{device}.spice"

    info = {}
    info["device"] = device
    info["temp"] = temp
    info["length"] = length
    info["width"] = width

    width_str = width
    length_str = length
    temp_str = temp

    netlist_path = f"{dirpath}/{device}_netlists/netlist_w{width_str}_l{length_str}_t{temp_str}.spice"
    result_path = (
        f"{dirpath}/simulated_Id/T{temp}_simulated_L{length_str}_W{width_str}.csv"
    )
    os.makedirs(f"{dirpath}/simulated_Id", exist_ok=True)

    with open(netlist_tmp) as f:
        tmpl = Template(f.read())
        os.makedirs(f"{dirpath}/{device}_netlists", exist_ok=True)
        with open(netlist_path, "w") as netlist:
            netlist.write(
                tmpl.render(
                    device=device,
                    width=width_str,
                    length=length_str,
                    temp=temp_str,
                    AD=float(width_str) * 0.24,
                    PD=2 * (float(width_str) + 0.24),
                    AS=float(width_str) * 0.24,
                    PS=2 * (float(width_str) + 0.24),
                )
            )

    # Running ngspice for each netlist
    try:
        call_simulator(netlist_path)

        if os.path.exists(result_path):
            mos_iv = result_path
        else:
            mos_iv = "None"

    except Exception:
        mos_iv = "None"

    info["mos_iv_simulated"] = mos_iv

    return info


def run_sims(df, dirpath, device, num_workers=mp.cpu_count()):
    """passing netlists to run_sim function
        and storing the results csv files into dataframes

    Args:
        df(pd.DataFrame): dataframe passed from the ext_measured function
        dirpath(str): the path to the file where we write data
        num_workers=mp.cpu_count() (int): num of cpu used
        device(str): name of the device
    Returns:
        df(pd.DataFrame): dataframe contains simulated results
    """
    loops = df["L (um)"].count()
    temp_range = int(loops / 3)
    df["temp"] = 25
    df["temp"][temp_range : 2 * temp_range] = -40
    df["temp"][2 * temp_range : 3 * temp_range] = 125

    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures_list = []
        for j, row in df.iterrows():
            futures_list.append(
                executor.submit(
                    run_sim, dirpath, device, row["W (um)"], row["L (um)"], row["temp"]
                )
            )

        for future in concurrent.futures.as_completed(futures_list):
            try:
                data = future.result()
                results.append(data)
            except Exception as exc:
                logging.info(f"Test case generated an exception: {exc}")

    sf = glob.glob(f"{dirpath}/simulated_Id/*.csv")

    # sweeping on all generated cvs files
    for i in range(len(sf)):
        sdf = pd.read_csv(
            sf[i],
            header=None,
            delimiter=r"\s+",
        )
        sweep = int(sdf[0].count() / len(MOS))
        new_array = np.empty((sweep, 1 + int(sdf.shape[0] / sweep)))

        new_array[:, 0] = sdf.iloc[:sweep, 0]
        times = int(sdf.shape[0] / sweep)

        for j in range(times):
            new_array[:, (j + 1)] = sdf.iloc[j * sweep : (j + 1) * sweep, 1]

        # Writing final simulated data 1
        sdf = pd.DataFrame(new_array)
        sdf.rename(
            columns={
                0: "vgs",
                1: "vb1",
                2: "vb2",
                3: "vb3",
                4: "vb4",
                5: "vb5",
            },
            inplace=True,
        )
        sdf.to_csv(sf[i], index=False)

    df = pd.DataFrame(results)
    return df


def error_cal(
    df: pd.DataFrame, sim_df: pd.DataFrame, meas_df: pd.DataFrame, dev_path: str, device
) -> None:
    """error function calculates the error between measured, simulated data

    Args:
        merged_df(pd.DataFrame): Dataframe contains devices and csv files
          which represent measured, simulated data
        dev_path(str): The path in which we write data
    """

    # adding error columns to the merged dataframe
    merged_dfs = list()
    loops = df["L (um)"].count()
    temp_range = int(loops / 3)
    df["temp"] = 25
    df["temp"][temp_range : 2 * temp_range] = -40
    df["temp"][2 * temp_range : 3 * temp_range] = 125
    if device == "pfet_03v3_iv" or device == "pfet_03v3_dss_iv":
        mos = PMOS3P3_VPS
    elif device == "pfet_06v0_iv" or device == "pfet_06v0_dss_iv":
        mos = PMOS6P0_VPS
    elif device == "nfet_06v0_iv" or device == "nfet_06v0_nvt_iv" or device == "nfet_06v0_dss_iv":
        mos = NMOS6P0_VPS
    else:
        mos = MOS

    for i in range(len(sim_df)):
        length = df["L (um)"].iloc[int(i)]
        w = df["W (um)"].iloc[int(i)]
        t = df["temp"].iloc[int(i)]

        sim_path = f"mos_iv_regr/{device}/simulated_Id/T{t}_simulated_L{length}_W{w}.csv"

        simulated_data = pd.read_csv(sim_path)

        measured_data = meas_df[
            [
                f"measured_vbs{2*i} =0",
                f"measured_vbs{2*i} ={mos[1]}",
                f"measured_vbs{2*i} ={mos[2]}",
                f"measured_vbs{2*i} ={mos[3]}",
                f"measured_vbs{2*i} ={mos[4]}",
            ]
        ].copy()
        measured_data.rename(
            columns={
                f"measured_vbs{2*i} =0": "measured_vbs1",
                f"measured_vbs{2*i} ={mos[1]}": "measured_vbs2",
                f"measured_vbs{2*i} ={mos[2]}": "measured_vbs3",
                f"measured_vbs{2*i} ={mos[3]}": "measured_vbs4",
                f"measured_vbs{2*i} ={mos[4]}": "measured_vbs5",
            },
            inplace=True,
        )
        measured_data["vgs"] = simulated_data["vgs"]

        result_data = simulated_data.merge(measured_data, how="left")

        result_data["step1_error"] = (
            np.abs(result_data["measured_vbs1"] - result_data["vb1"])
            * 100.0
            / (result_data["measured_vbs1"])
        )
        result_data["step2_error"] = (
            np.abs(result_data["measured_vbs2"] - result_data["vb2"])
            * 100.0
            / (result_data["measured_vbs2"])
        )
        result_data["step3_error"] = (
            np.abs(result_data["measured_vbs3"] - result_data["vb3"])
            * 100.0
            / (result_data["measured_vbs3"])
        )
        result_data["step4_error"] = (
            np.abs(result_data["measured_vbs4"] - result_data["vb4"])
            * 100.0
            / (result_data["measured_vbs4"])
        )
        result_data["step5_error"] = (
            np.abs(result_data["measured_vbs5"] - result_data["vb5"])
            * 100.0
            / (result_data["measured_vbs5"])
        )
        result_data["error"] = (
            np.abs(
                result_data["step1_error"]
                + result_data["step2_error"]
                + result_data["step3_error"]
                + result_data["step4_error"]
                + result_data["step5_error"]
            )
            / 5
        )

        merged_dfs.append(result_data)
        merged_out = pd.concat(merged_dfs)
        merged_out.to_csv(f"{dev_path}/error_analysis.csv", index=False)
    return None


def main():
    """Main function applies all regression steps"""
    # ======= Checking ngspice  =======
    ngspice_v_ = os.popen("ngspice -v").read()
    if ngspice_v_ == "":
        logging.error("ngspice is not found. Please make sure ngspice is installed.")
        exit(1)
    # pandas setup
    pd.set_option("display.max_columns", None)
    pd.set_option("display.max_rows", None)
    pd.set_option("max_colwidth", None)
    pd.set_option("display.width", 1000)

    main_regr_dir = "mos_iv_regr"

    devices = [
        "nfet_03v3_iv",
        "pfet_03v3_iv",
        "nfet_06v0_iv",
        "pfet_06v0_iv",
        "nfet_06v0_nvt_iv",
        "nfet_03v3_dss_iv",
        "pfet_03v3_dss_iv",
        "nfet_06v0_dss_iv",
        "pfet_06v0_dss_iv",
    ]

    for i, dev in enumerate(devices):
        dev_path = f"{main_regr_dir}/{dev}"

        if os.path.exists(dev_path) and os.path.isdir(dev_path):
            shutil.rmtree(dev_path)

        os.makedirs(f"{dev_path}", exist_ok=False)

        logging.info("######" * 10)
        logging.info(f"# Checking Device {dev}")

        data_files = glob.glob(f"../../180MCU_SPICE_DATA/MOS/{dev}.nl_out.xlsx")
        if len(data_files) < 1:
            logging.info(f"# Can't find file for device: {dev}")
            file = ""
        else:
            file = os.path.abspath(data_files[0])
        logging.info(f"#  data points file : {file}")

        if file != "":
            meas_df = ext_measured(file, dev)
        else:
            meas_df = []

        df1 = pd.read_csv(f"mos_iv_regr/{dev}/{dev}.csv")
        df = df1[["L (um)", "W (um)"]].copy()
        df.dropna(inplace=True)

        sim_df = run_sims(df, dev_path, dev, 3)
        logging.info(
            f"# Device {dev} number of measured_datapoints : {len(sim_df) * len(meas_df)}"
            
        )
        logging.info(
            f"# Device {dev} number of simulated datapoints : {len(sim_df) * len(meas_df)}"
        )

        # passing dataframe to the error_calculation function
        # calling error function for creating statistical csv file

        error_cal(df, sim_df, meas_df, dev_path, dev)

        # reading from the csv file contains all error data
        # merged_all contains all simulated, measured, error data

        merged_all = pd.read_csv(f"{dev_path}/error_analysis.csv")

        # calculating the error of each device and reporting it
        min_error_total = float()
        max_error_total = float()
        error_total = float()

        # number of rows in the final excel sheet
        num_rows = merged_all["error"].count()

        for n in range(num_rows):
            error_total += merged_all["error"][n]
            if merged_all["error"][n] > max_error_total:
                max_error_total = merged_all["error"][n]
            elif merged_all["error"][n] < min_error_total:
                min_error_total = merged_all["error"][n]

        mean_error_total = error_total / num_rows

        # Making sure that min, max, mean errors are not > 100%
        if min_error_total > 100:
            min_error_total = 100

        if max_error_total > 100:
            max_error_total = 100

        if mean_error_total > 100:
            mean_error_total = 100

        # logging.infoing min, max, mean errors to the consol
        logging.info(
            f"# Device {dev} min error: {min_error_total:.2f}, max error: {max_error_total:.2f}, mean error {mean_error_total:.2f}"
        )

        if max_error_total < PASS_THRESH:
            logging.info(f"# Device {dev} has passed regression.")
        else:
            logging.error(f"# Device {dev} has failed regression. Needs more analysis.")



# # ================================================================
# -------------------------- MAIN --------------------------------
# ================================================================

if __name__ == "__main__":

    # Args
    arguments = docopt(__doc__, version="comparator: 0.1")
    workers_count = (
        os.cpu_count() * 2
        if arguments["--num_cores"] is None
        else int(arguments["--num_cores"])
    )
    logging.basicConfig(
        level=logging.DEBUG,
        handlers=[
            logging.StreamHandler(),
        ],
        format=f"%(asctime)s | %(levelname)-7s | %(message)s",
        datefmt="%d-%b-%Y %H:%M:%S",
    )
    
    # Calling main function
    main()

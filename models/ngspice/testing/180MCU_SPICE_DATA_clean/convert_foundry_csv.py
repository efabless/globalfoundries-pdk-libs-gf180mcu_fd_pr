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

# CONSTANT VALUES
## These values are manually selected after some analysis
## for provided measuremnet data.
# === FETS ===
NUM_DP_PER_TEMP_FET_03V3 = 25
NUM_DP_PER_TEMP_FET_06V0_NVT = 12
NUM_DP_PER_TEMP_FET_06V0 = 20
NUM_COLS_MEAS_VBS = 7
NUM_COLS_MEAS_VGS = 8
# === CAP_MOS ===
NUM_DP_PER_TEMP_MOSCAP_03V3 = 16


def parse_dp_id_vgs_vbs(sub_df, dev_name):
    """
    Function to parse measurement data for Ids Vs Vgs with Vbs sweep to be used in simulation.

    Parameters
    ----------
    sub_df : pd.DataFrame
        DataFrame that holds sub measurement information per each variation.
    dev_name : str
        Device we want to extract data for.
    Returns
    ----------
    df_id_vgs_vbs : pd.DataFrame
        DataFrame that holds all measurement points for Id Vs Vds with Vbs sweep
    """

    ## Id Vs Vgs [Vbs sweep]
    df_id_vgs_vbs = sub_df.iloc[:, :NUM_COLS_MEAS_VBS]
    vds_df_id_vgs_vbs = float(df_id_vgs_vbs.columns[0].split("/")[0].split("=")[1])
    df_id_vgs_vbs.drop(columns=df_id_vgs_vbs.columns[0], inplace=True)

    # Get vgs sweep values
    vgs_col_name = "vgs " if "nfet" in dev_name else "-vgs "
    # Get Vgs step value
    vgs_step_val = abs(df_id_vgs_vbs[vgs_col_name][1] - df_id_vgs_vbs[vgs_col_name][0])

    # Stacking all vbs sweeps in one column
    df_id_vgs_vbs = (
        df_id_vgs_vbs.set_index([vgs_col_name])
        .stack()
        .reset_index(name="id")
        .rename(columns={"level_1": "vbs"})
        .rename(columns={vgs_col_name: "vgs"})
    )

    # Multiplying vgs by -1 for pfet devices to match provided data
    df_id_vgs_vbs["vgs"] = df_id_vgs_vbs["vgs"].apply(lambda x: x * -1) if "pfet" in dev_name else df_id_vgs_vbs["vgs"]

    # Get min/max values of vgs sweep
    vgs_min_val = df_id_vgs_vbs["vgs"].min()
    vgs_max_val = df_id_vgs_vbs["vgs"].max()

    # Adding columns for all voltage sweeps and output
    df_id_vgs_vbs["vbs"] = df_id_vgs_vbs["vbs"].apply(lambda x: x.split("=")[1])
    df_id_vgs_vbs["vbs"] = df_id_vgs_vbs["vbs"].astype(float)
    df_id_vgs_vbs["vds"] = vds_df_id_vgs_vbs
    df_id_vgs_vbs["rds"] = np.nan
    df_id_vgs_vbs["const_var"] = "vds"
    df_id_vgs_vbs["const_var_val"] = vds_df_id_vgs_vbs
    df_id_vgs_vbs["out_col"] = "id"

    # Get vgs sweep values
    vbs_min_val = df_id_vgs_vbs["vbs"].min()
    vbs_max_val = df_id_vgs_vbs["vbs"].max()
    vbs_step_val = abs(df_id_vgs_vbs["vbs"][1] - df_id_vgs_vbs["vbs"][0])

    # Adding sweeps used per each variation
    df_id_vgs_vbs[
        "sweeps"
    ] = f"vgs {vgs_min_val} {vgs_max_val} {vgs_step_val} vbs {vbs_min_val} {vbs_max_val} {vbs_step_val}"

    return df_id_vgs_vbs


def parse_dp_id_vds_vgs(sub_df, dev_name):
    """
    Function to parse measurement data for Ids Vs Vds with Vgs sweep to be used in simulation.

    Parameters
    ----------
    sub_df : pd.DataFrame
        DataFrame that holds sub measurement information per each variation.
    dev_name : str
        Device we want to extract data for.

    Returns
    ----------
    df_id_vds_vgs : pd.DataFrame
        DataFrame that holds all measurement points for Id Vs Vds with Vgs sweep
    """

    ## Id Vs Vds [Vgs sweep]
    df_id_vds_vgs = sub_df.iloc[
        :, NUM_COLS_MEAS_VBS : NUM_COLS_MEAS_VBS + NUM_COLS_MEAS_VGS
    ]
    vbs_df_id_vds_vgs = float(df_id_vds_vgs.columns[0].split("/")[0].split("=")[1])
    df_id_vds_vgs.drop(columns=df_id_vds_vgs.columns[0], inplace=True)

    # Get vds sweep values
    vgs_col_name = "vds (V)" if "nfet" in dev_name else "-vds (V)"

    # Get vds step vaule used in sweep
    vds_step_val = abs(df_id_vds_vgs[vgs_col_name][1] - df_id_vds_vgs[vgs_col_name][0])

    # Stacking all vgs sweeps in one column
    df_id_vds_vgs = (
        df_id_vds_vgs.set_index([vgs_col_name])
        .stack()
        .reset_index(name="id")
        .rename(columns={"level_1": "vgs"})
        .rename(columns={vgs_col_name: "vds"})
    )

    # Multiplying vds by -1 for pfet devices to match provided data
    df_id_vds_vgs["vds"] = df_id_vds_vgs["vds"].apply(lambda x: x * -1) if "pfet" in dev_name else df_id_vds_vgs["vds"]

    # Get vds min/max values used in sweep
    vds_min_val = df_id_vds_vgs["vds"].min()
    vds_max_val = df_id_vds_vgs["vds"].max()

    # Adding columns for all voltage sweeps and output
    df_id_vds_vgs["vgs"] = df_id_vds_vgs["vgs"].apply(lambda x: x.split("=")[1])
    df_id_vds_vgs["vgs"] = df_id_vds_vgs["vgs"].astype(float)
    df_id_vds_vgs["vbs"] = vbs_df_id_vds_vgs
    df_id_vds_vgs["rds"] = np.nan
    df_id_vds_vgs["const_var"] = "vbs"
    df_id_vds_vgs["const_var_val"] = vbs_df_id_vds_vgs
    df_id_vds_vgs["out_col"] = "id"

    # Get vgs sweep values
    vgs_min_val = df_id_vds_vgs["vgs"].min()
    vgs_max_val = df_id_vds_vgs["vgs"].max()
    vgs_step_val = abs(df_id_vds_vgs["vgs"][1] - df_id_vds_vgs["vgs"][0])

    # Adding sweeps used per each variation
    df_id_vds_vgs[
        "sweeps"
    ] = f"vds {vds_min_val} {vds_max_val} {vds_step_val} vgs {vgs_min_val} {vgs_max_val} {vgs_step_val}"

    return df_id_vds_vgs


def parse_dp_rds_vds_vgs(sub_df, dev_name):
    """
    Function to parse measurement data for Rds Vs Vds with Vgs sweep to be used in simulation.

    Parameters
    ----------
    sub_df : pd.DataFrame
        DataFrame that holds sub measurement information per each variation.
    dev_name : str
        Device we want to extract data for.
    Returns
    ----------
    df_rds_vds_vgs : pd.DataFrame
        DataFrame that holds all measurement points for Rds Vs Vds with Vgs sweep
    """

    ## Rds Vs Vds [Vgs sweep]
    df_rds_vds_vgs = sub_df.iloc[:, -NUM_COLS_MEAS_VGS:]

    vbs_df_rds_vds_vgs = float(df_rds_vds_vgs.columns[0].split("/")[0].split("=")[1])
    df_rds_vds_vgs.drop(columns=df_rds_vds_vgs.columns[0], inplace=True)

    # Get vds sweep values
    vgs_col_name = "vds (V).1" if "nfet" in dev_name else "-vds (V).1"

    vds_step_val = abs(df_rds_vds_vgs[vgs_col_name][1] - df_rds_vds_vgs[vgs_col_name][0])

    # Stacking all vgs sweeps in one column
    df_rds_vds_vgs = (
        df_rds_vds_vgs.set_index([vgs_col_name])
        .stack()
        .reset_index(name="rds")
        .rename(columns={"level_1": "vgs"})
        .rename(columns={vgs_col_name: "vds"})
    )

    # Multiplying vds by -1 for pfet devices to match provided data
    df_rds_vds_vgs["vds"] = df_rds_vds_vgs["vds"].apply(lambda x: x * -1) if "pfet" in dev_name else df_rds_vds_vgs["vds"]

    # Get min/max values for vds sweeps
    vds_min_val = df_rds_vds_vgs["vds"].min()
    vds_max_val = df_rds_vds_vgs["vds"].max()

    # Adding columns for all voltage sweeps and output
    df_rds_vds_vgs["vgs"] = df_rds_vds_vgs["vgs"].apply(
        lambda x: ".".join(x.split("=")[1].split(".")[:2])
    )
    df_rds_vds_vgs["vgs"] = df_rds_vds_vgs["vgs"].astype(float)
    df_rds_vds_vgs["vbs"] = vbs_df_rds_vds_vgs
    df_rds_vds_vgs["id"] = np.nan
    df_rds_vds_vgs["const_var"] = "vbs"
    df_rds_vds_vgs["const_var_val"] = vbs_df_rds_vds_vgs
    df_rds_vds_vgs["out_col"] = "rds"

    # Get vgs sweep values
    vgs_min_val = df_rds_vds_vgs["vgs"].min()
    vgs_max_val = df_rds_vds_vgs["vgs"].max()
    vgs_step_val = abs(df_rds_vds_vgs["vgs"][1] - df_rds_vds_vgs["vgs"][0])

    df_rds_vds_vgs[
        "sweeps"
    ] = f"vds {vds_min_val} {vds_max_val} {vds_step_val} vgs {vgs_min_val} {vgs_max_val} {vgs_step_val}"

    return df_rds_vds_vgs


def parse_dp_sweeps(sub_df, dev_name):
    """
    Function to parse measurement data to be used in simulation.

    Parameters
    ----------
    sub_df : pd.DataFrame
        DataFrame that holds sub measurement information per each variation.
    dev_name : str
        Device we want to extract data for.
    Returns
    -------
    df_dp_sweeps : pd.DataFrame
        DataFrame that holds all extracted points for all sweeps.
    """

    ## Id Vs Vgs [Vbs sweep]
    df_id_vgs_vbs = parse_dp_id_vgs_vbs(sub_df, dev_name)

    ## Id Vs Vds [Vgs sweep]
    df_id_vds_vgs = parse_dp_id_vds_vgs(sub_df, dev_name)

    ## Rds Vs Vds [Vgs sweep]
    df_rds_vds_vgs = parse_dp_rds_vds_vgs(sub_df, dev_name)

    df_dp_sweeps = pd.concat([df_id_vgs_vbs, df_id_vds_vgs, df_rds_vds_vgs])

    return df_dp_sweeps


def get_orig_col_names(df, variations_count):
    """
    Function to get original columns names for dataframe and number of columns per variation.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame we need to extract some info from it
    variations_count: int
        Number of variation in the dataframe
    Returns
    -------
        num_data_col_per_dp: Number of data columns per variation
        orig_col_names: Original column names of dataframe per variation
    """

    # Get number of columns that holds measurement data for each variation
    num_data_col_per_dp = int(len(df.columns) / variations_count)
    # Get columns names that holds data for each variation
    orig_col_names = df.columns[:num_data_col_per_dp]

    logging.info(f" No of data columns per variation: {num_data_col_per_dp}")
    logging.info(f" Original columns per variation:\n {orig_col_names}")

    return num_data_col_per_dp, orig_col_names


def generate_fets_variations(df, dp_df, dev_name, variations_count):
    """
    Function to generate full data frame of measured data with all variations.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame that holds all the measurement information for selected fet.
    dp_df : pd.DataFrame
        DataFrame that holds all data points for all varaitions.
    dev_name : str
        Device we want to extract data for.
    variations_count : float
        Number of variations per each selected device
    Returns
    -------
        None
    """

    # Get number of columns that holds measurement data for each variation
    # Get columns names that holds data for each variation
    num_data_col_per_dp, orig_col_names = get_orig_col_names(df, variations_count)

    # Generating all data points per each variation and combining all data in one DF
    all_dfs = []
    for i in range(0, len(df.columns), num_data_col_per_dp):
        sub_df = df[df.columns[i : i + num_data_col_per_dp]].copy()
        sub_df.columns = orig_col_names
        parsed_df = parse_dp_sweeps(sub_df, dev_name)
        for c in dp_df.columns:
            parsed_df[c] = dp_df.loc[len(all_dfs), c]
        all_dfs.append(parsed_df)

    all_dfs = pd.concat(all_dfs)
    all_dfs.drop_duplicates(inplace=True)
    all_dfs.rename(columns={"corners": "corner"}, inplace=True)

    # Generate data file that holds all sweep values per each variation to be used in simulation
    generate_fets_sweeps(all_dfs, dev_name)

    # Generate final data file that holds all data points to be used in comparision
    ## Re-arranging columns of final data file
    all_dfs_cols = [
        "W (um)",
        "L (um)",
        "corner",
        "temp",
        "vds",
        "vgs",
        "vbs",
        "id",
        "rds",
    ]
    all_dfs = all_dfs.reindex(columns=all_dfs_cols)

    logging.info(f"Length of all data points {len(all_dfs)}")

    # Making sure that we don't have any nan values except in measured output [Id or Rds]
    for c in all_dfs.columns:
        logging.info(f"col: {c} has nan: {all_dfs[c].isna().any()}")

    return all_dfs


def generate_fets_sweeps(all_dfs, dev_name):
    """
    Function to generate full data frame of measured data with all variations.

    Parameters
    ----------
    all_dfs : pd.DataFrame
        DataFrame that holds all the measurement data after extraction.
    dev_name : str
        Device we want to extract data for.
    Returns
    -------
        None
    """

    # Generate csv file contains simulation sweeps
    ## Re-arranging columns of sweep data file
    sweeps_df_cols = [
        "W (um)",
        "L (um)",
        "corner",
        "temp",
        "const_var",
        "const_var_val",
        "sweeps",
        "out_col",
    ]
    sweeps_df = all_dfs.reindex(columns=sweeps_df_cols)
    sweeps_df.drop_duplicates(inplace=True)

    # Splitting sweeps depends one selected measured output
    sweeps_df_id = sweeps_df[sweeps_df['out_col'] == 'id']
    sweeps_df_rds = sweeps_df[sweeps_df['out_col'] == 'rds']
    # Drop out_col columns as it will be redundant
    sweeps_df_id = sweeps_df_id.drop('out_col', axis=1)
    sweeps_df_rds = sweeps_df_rds.drop('out_col', axis=1)
    # Saving sweep data files to csv
    sweeps_df_id.to_csv(f"{dev_name}_sweeps_id.csv", index=False)
    sweeps_df_rds.to_csv(f"{dev_name}_sweeps_rds.csv", index=False)
    logging.info(f"Sweep csv file for {dev_name}: {sweeps_df}")
    logging.info(f"Number of sweep points for {dev_name}: {len(sweeps_df)}")
    logging.info(f"Sweep csv file for {dev_name} at : {sweeps_df}_sweeps.csv")


def dataframe_cleanup(df, unwanted_cols):
    """
    Function to clean data frame from unwanted cols.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame we want to clean it
    unwanted_cols: list
        List of unwanted columns you need to remove
    Returns
    -------
    df : pd.DataFrame
        Output dataFrame after removing unwanted cols.
    """

    # Get the columns with only NaN values
    nan_columns = df.columns[df.isna().all()]
    # Drop the columns with only NaN values
    df.drop(columns=nan_columns, inplace=True)
    df.drop(columns=unwanted_cols, inplace=True)

    return df


def get_variation_count(df, col_name):
    """
    Function to extract measurement data for Fets.

    Parameters
    ----------
    df : pd.dataframe
        Data frame for measured data to get variaitons from it
    col_name : str
        Name of column we will use to count it as a variation.
    Returns
    -------
        variation_count: Number of variations in the provided dataframe
    """
    # Get num of variations for fets depending on length values in data
    variations_count = df[col_name].count()

    logging.info(f"No of variations are {variations_count}")
    logging.info(f"Length of data points is {len(df.columns)}")

    return variations_count


def stack_df_cols(sub_df, col_untouched, stacked_col_name, stacked_col_index):
    """
    Function to stack dataframe columns in new column with column index.

    Parameters
    ----------
    sub_df : pd.DataFrame
        DataFrame that we need to stack columns in it.
    col_untouched : str
       Name of column that we need to keep it untouched while stacking other columns.
    stacked_col_name : str
       Name of column we stack all data of other columns in it.
    stacked_col_index : str
        Name of column that contains index of stacked columns.
    Returns
    -------
        stack_df_cols: Reshaped dataframe that contains stacked columns with column index.
    """

    sub_df = (
        sub_df.set_index([col_untouched])
        .stack()
        .reset_index(name=stacked_col_index)
        .rename(columns={"level_1": stacked_col_name})
    )

    return sub_df


def fet_meas_extraction(df, dev_name):
    """
    Function to extract measurement data for Fets.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame that holds all the measurement information for selected fet.
    dev_name : str
        Device we want to extract data for.
    Returns
    -------
        None
    """

    # Drop any unwanted columns
    id_cols = [c for c in df.columns if "Id (A)" in c]
    rd_cols = [c for c in df.columns if "Rds" in c]
    unwanted_cols = ["Unnamed: 2", "Ids"] + id_cols + rd_cols

    # Cleanup dataframe from unwanted columns we don't use
    df = dataframe_cleanup(df, unwanted_cols)

    # Get num of variations for fets depending on length values in data
    variations_count = get_variation_count(df, "L (um)")

    # For Fets 03v3, There are 75 variations = 25*3 [For each temp] and all variations are extracted at tt corner
    ## For Fets 06v0, There are 60 variations = 20*3 [For each temp] and all variations are extracted at tt corner
    ## For Fets 06v0_nvt, There are 36 variations = 12*3 [For each temp] and all variations are extracted at tt corner
    ## Please note that the temp variation wasn't included in dataset so we will have to add that new column
    if "03v3" in dev_name:
        NUM_DP_PER_TEMP = NUM_DP_PER_TEMP_FET_03V3
    elif "06v0_nvt" in dev_name:
        NUM_DP_PER_TEMP = NUM_DP_PER_TEMP_FET_06V0_NVT
    else:
        NUM_DP_PER_TEMP = NUM_DP_PER_TEMP_FET_06V0

    all_temp = (
        [25] * NUM_DP_PER_TEMP + [-40] * NUM_DP_PER_TEMP + [125] * NUM_DP_PER_TEMP
    )

    # Define new data frame that holds all variations
    dp_cols = ["W (um)", "L (um)", "corners"]
    dp_df = df[dp_cols].iloc[:variations_count].copy()
    dp_df["temp"] = all_temp
    df.drop(columns=dp_cols, inplace=True)

    # Generate the full dataframe that holds all meas data in a clean format
    all_dfs = generate_fets_variations(df, dp_df, dev_name, variations_count)

    # Writing final dataframe that holds all clean data
    all_dfs.drop_duplicates(inplace=True)

    # Splitting final df depends on measured output
    all_dfs_id = all_dfs.loc[all_dfs['id'].notnull()]
    all_dfs_rds = all_dfs.loc[all_dfs['rds'].notnull()]
    # Drop rds/id columns as it will be redundant
    all_dfs_id = all_dfs_id.drop('rds', axis=1)
    all_dfs_rds = all_dfs_rds.drop('id', axis=1)
    # Saving full extracted measured data to csv
    all_dfs_id.to_csv(f"{dev_name}_meas_id.csv", index=False)
    all_dfs_rds.to_csv(f"{dev_name}_meas_rds.csv", index=False)
    logging.info(f"Full extracted measurement data for {dev_name}: {all_dfs}")
    logging.info(
        f"Full extracted measurement data for {dev_name} at: {dev_name}_meas.csv"
    )


def moscap_meas_extraction(df: str, dev_name: str) -> pd.DataFrame:
    """
    Function to extract measurement data for Fets.

    Parameters
    ----------
    df : pd.dataframe
        Data frame for measured data provided by foundry
    dev_name : str
        Device we want to extract data for.
    Returns
    -------
       None
    """

    # Drop any unwanted columns
    dummy_cols = [c for c in df.columns if "dummy_" in c]
    cj_cols = [c for c in df.columns if "Cj (fF)" in c]
    unwanted_cols = ['w', 'l', 'CV (fF)'] + dummy_cols + cj_cols

    # Cleanup dataframe from unwanted columns we don't use
    df = dataframe_cleanup(df, unwanted_cols)

    # For CAP_MOS 03v3/06v0, There are 144 variations = 4*4*3*3 [For device_type * W_L_variation * corners * temp]
    ## We have 4 types of CAP_MOS 03v3 [cap_nmos, cap_pmos, cap_nmos_b, cap_pmos_b]
    ## We have 4 W&L combination [(50, 50), (1, 1), (50, 1), (1, 50) um]
    ## We have 3 corners [typical, ff, ss]
    ## We have 3 temperature [25, -40, 175]

    all_temp = (
        [25] * NUM_DP_PER_TEMP_MOSCAP_03V3 + [-40] * NUM_DP_PER_TEMP_MOSCAP_03V3 + [175] * NUM_DP_PER_TEMP_MOSCAP_03V3
    )

    # Define new data frame that holds all variations
    dp_df = pd.DataFrame({'temp': all_temp})

    # "Unnamed: 2" cols: This column holds some info related to each device [name, W&L]
    ## Example nmoscap_3p3 (50u x50u )
    dp_df["device_name"] = df["Unnamed: 2"].apply(lambda x: x.split("\n")[0])
    dp_df["W (um)"] = df["Unnamed: 2"].apply(lambda x: x.split("\n")[1].split("x")[0].replace("(", "").replace("u", ""))
    dp_df["L (um)"] = df["Unnamed: 2"].apply(lambda x: x.split("\n")[1].split("x")[1].replace(")", "").replace("u", ""))
    dp_df["W (um)"] = dp_df["W (um)"].astype(float)
    dp_df["L (um)"] = dp_df["L (um)"].astype(float)

    # Cleanup dataframe from unwanted columns we don't use
    unwanted_cols = ['Unnamed: 2', 'corners']
    df = dataframe_cleanup(df, unwanted_cols)

    # Get number of columns that holds measurement data for each variation
    # Get columns names that holds data for each variation
    ## Using NUM_DP_PER_TEMP_MOSCAP_03V3 * 3: As data is all 3 corners are combined in one table
    variations_count = NUM_DP_PER_TEMP_MOSCAP_03V3 * 3
    num_data_col_per_dp, orig_col_names = get_orig_col_names(df, variations_count)

    # Generating all data points per each variation and combining all data in one DF
    all_dfs = []
    col_untouched = 'Vj'           # Name of column we don't need to touch it while stacking other columns
    stacked_col_name = 'corner'    # Name of new column in which we stacked other columns
    stacked_col_index = 'Cj'       # Name of column that holds all values of stacked columns

    for i in range(0, len(df.columns), num_data_col_per_dp):
        sub_df = df[df.columns[i : i + num_data_col_per_dp]].copy()
        sub_df.columns = orig_col_names
        stacked_corner_df = stack_df_cols(sub_df, col_untouched, stacked_col_name, stacked_col_index)
        for c in dp_df.columns:
            stacked_corner_df[c] = dp_df.loc[len(all_dfs), c]
        all_dfs.append(stacked_corner_df)

    all_dfs = pd.concat(all_dfs)
    all_dfs.drop_duplicates(inplace=True)

    # Cleaning some columns and values to match latest version of GF180MCU models
    all_dfs["device_name"] = all_dfs["device_name"].apply(lambda x: x.replace("nmoscap", "cap_nmos").replace("pmoscap", "cap_pmos"))
    all_dfs["device_name"] = all_dfs["device_name"].apply(lambda x: x.replace("3p3", "03v3").replace("6p0", "06v0"))

    ## Re-arranging columns of final data file
    all_dfs_cols = [
        "device_name",
        "W (um)",
        "L (um)",
        "corner",
        "temp",
        "Vj",
        "Cj",
    ]
    all_dfs = all_dfs.reindex(columns=all_dfs_cols)

    # Writing final dataframe that holds all clean data
    all_dfs.drop_duplicates(inplace=True)
    all_dfs.to_csv(f"{dev_name}_meas_cv.csv", index=False)
    logging.info(f"Full extracted measurement data for {dev_name}:\n {all_dfs}")
    logging.info(
        f"Full extracted measurement data for {dev_name} at: {dev_name}_meas_cv.csv"
    )


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
        fet_meas_extraction(df, dev_type)
    elif "cap_mos" in dev_type:
        df = pd.read_excel(excel_path)
        logging.info(f"Starting data extraction from {excel_path} sheet for {dev_type} device")
        moscap_meas_extraction(df, dev_type)
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

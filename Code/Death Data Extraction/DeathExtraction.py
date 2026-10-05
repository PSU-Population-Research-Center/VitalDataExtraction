import pandas as pd
import numpy as np
import zipfile
import json
import os
from urllib.request import urlopen
import re
import numpy as np


def read_nchs_df(year):
    """
    Pulls specifications for reading an NCHS death file from a fwf from the 
    NBER website in data frame format.

    Parameters
    ----------
    year : int
            year of nchs data to read dictionary for

    Returns
    -------
    pd.DataFrame
        a data frame with text for reading fixed width NCHS death file
    """
    mort_str = "mortality" if year >= 2018 else "mort"
    surl = "https://data.nber.org/nvss/mortality/programs/dct/" + mort_str +\
        str(year) + ".dct"
    source_lines = [str(l).replace("b'", "") for l in urlopen(surl)]
    trimmed_lines = [re.sub(" *\\)", ")", str(l)) for l in source_lines]
    sub_lines = [
        l.replace("'", "") for l in trimmed_lines if l.startswith("_col")]
    sub_lines = [
        l.replace("\\t", " ") for l in sub_lines if l.startswith("_col")]
    tmp_path = "/tmp/tmp_dta_src"
    f = open(tmp_path, "w")
    f.writelines([s.replace("\\n", "\n") for s in sub_lines])
    f.close()
    dldf = pd.read_table(tmp_path, sep="\\s+", header = None)
    os.remove(tmp_path)
    return dldf


def read_nchs_dict(year):
    """
    Pulls specifications for reading an NCHS death file from a fwf from the 
    NBER website.

    Parameters
    ----------
    year : int
            year of nchs data to read dictionary for

    Returns
    -------
    dict
        a dictionary with specifications for reading fixed width NCHS death file
    """
    dldf = read_nchs_df(year)
    dldf["start"] = dldf[0].apply(lambda x: int(re.findall(r'\d+', x)[0])-1)
    dldf["end"] = dldf[3].apply(
        lambda x: int(re.findall(r'\d+', x)[0])) + dldf["start"]
    dldf["var"] = dldf[2]
    dldf["type"] = pd.Series("str", index=dldf.index).case_when(
                [(dldf[1] == "int", "Int64"),
                 (dldf[1] == "byte", "Int64"),
                 (dldf[1] == "double", "float64")])
    r_ = range(dldf.shape[0])
    src_dct = {
        dldf["var"][i]: tuple([dldf["start"][i], dldf["end"][i]]) for i in r_}
    src_dtype = {dldf["var"][i]: dldf["type"][i] for i in r_}
    if year >= 2003:
        src_dct["state"] = tuple([28, 30])
        src_dct["cntyfips"] = tuple([34, 37])
        src_dct["pregstat"] = tuple([142, 143])
    if year >= 2003:
        src_dtype["state"] = "str"
        src_dtype["cntyfips"] = "Int64"
        src_dtype["pregstat"] = "str"
    src_dct["record_2"] = tuple([348, 353])
    out_dct = {"pos": src_dct, "dtype": src_dtype}
    return out_dct


def read_state_fips_df():
    """
    Pulls state fips codes and abbreviations into data frame.

    Parameters
    ----------
    None

    Returns
    -------
    pd.DataFrame
        a data frame with state abbvs and fips codes
    """
    fip_abv_df = pd.read_table(
        "https://www2.census.gov/geo/docs/reference/codes2020/" +\
        "national_state2020.txt", sep = "|")
    fip_abv_df["STATEFP"] = fip_abv_df[
        "STATEFP"].astype(str).str.pad(2,fillchar='0')
    fip_abv_df = fip_abv_df[["STATE", "STATEFP"]]
    return fip_abv_df


class DeathExtraction(object):
    """
    A generic class used to extract death data from various file types.

    ...

    Attributes
    ----------
    year : int
        year of data to extract
    state : str
        state of data to extract
    source : str
        file path to read for the source
    """
    def __init__(self, year, state, source):
        self.year = year
        self.state = state
        self.source = source
        self.raw_df = None
        self.death_df = pd.DataFrame()
        self.fips_df = read_state_fips_df()

    def read_data(self):
        return None
    
    def inspect_data(self):
        print("NA Counts")
        print(self.death_df.apply(lambda x: x.isna().sum(), axis = 0))
        print(self.death_df.describe())
        for c in self.death_df.columns:
            print(self.death_df[c].value_counts())
        return None
    
    def write_data(self):
        base = "~/Downloads/"
        odir = base + self.state
        ofile = odir + "/{}.csv".format(self.year)
        os.makedirs(odir, exist_ok=True)
        self.death_df.to_csv(ofile, index = False)
        return None


class NCHSDeathExtraction(DeathExtraction):
    """
    Class used to extract death data from NCHS files.

    ...

    Attributes
    ----------
    year : int
        year of data to extract
    state : str
        state of data to extract
    """
    def __init__(self, year, state = None):
        geo_stub = "" if year < 1994 else "USPS"
        # NOTE: This needs to be updated to wherever your zipped folders are
        src_str = "/vol/share/population_research/_DATA/NCHS_DEATH/" +\
            "MortAC{}/MULT{}.USPSAllCnty.zip".format(year, year)
        super().__init__(year, state, source = src_str)
        self.state_idx = None
        self.data_dict = read_nchs_dict(year)
        self.data_dict_src = "https://data.nber.org/nvss/mortality/" +\
            "programs/dct/mortality" + str(year) + ".dct"

    def read_state_res_data(self):
        """
        Read in the indexes for states from the raw data, shouldnt be used by
        itself for most use cases.

        Parameters
        ----------
        None
        """
        fip_abv_df = self.fips_df.copy().rename(columns={
            "STATE":"state", "STATEFP":"cntyfips"})
        z = zipfile.ZipFile(self.source)
        sfs = [x for x in z.namelist() if x.endswith("txt")]
        colnames = ["state" if self.year >= 2003 else "stresfip"]
        colspecs = [self.data_dict["pos"][i] for i in colnames]
        dts = {i: "str" for i in colnames}
        state_idx_raw = [pd.read_fwf(
            z.open(sf), names=colnames, colspecs=colspecs,
            dtype = dts) for sf in sfs]
        self.state_idx = [
            x.merge(fip_abv_df, how = "left") for x in state_idx_raw]
        for i in range(len(self.state_idx)):
            self.state_idx[i]["state"] = \
                self.state_idx[i]["state"].fillna("")

    def read_data(self, select_cols = None, **kwargs):
        """
        Read in raw data from NCHS zip files into DataFrame.
    
        Parameters
        ----------
        select_cols: str or list of strs
            specific colomns in the file to read, if None reads all columns.
        kwargs:
            parameters passed to the read_fwf file such as nrows
        """
        z = zipfile.ZipFile(self.source)
        if not isinstance(select_cols, list) and select_cols is not None:
            select_cols = [select_cols]
        sfs = [x for x in z.namelist() if x.endswith("txt")]
        colnames = select_cols if select_cols is not None else list(
            self.data_dict["pos"].keys())
        colspecs = [self.data_dict["pos"][i] for i in colnames]
        dts = {i: self.data_dict["dtype"][i] for i in colnames}
        # self.read_state_res_data()
        # num_lines = [
        #     sum(1 for _ in z.open(sfs[i])) for i in range(len(self.state_idx))]
        # skips = [
        #     list(np.where(x.state != self.state)[0]) for x in self.state_idx]
        skips = [[],[]]
        # code to make sure we didnt miss blanks at the end of filed to skip
        # for i in range(len(self.state_idx)):
        #     if self.state_idx[i].shape[0] != num_lines[i]:
        #         skips[i] += list(range(len(self.state_idx[i]), num_lines[i]))
        raw_df = pd.concat([pd.read_fwf(
            z.open(sfs[0]), names=colnames, colspecs=colspecs,
            dtype = dts, skiprows = skips[i], **kwargs) 
            for i in range(len(skips))])
        self.raw_df = raw_df
        self.raw_df.reset_index(inplace=True, drop = True)
        self.death_df = self.raw_df[[]].copy()
        # self.death_df.loc[:,"state"] = self.state
        # merged_fip_df = self.fips_df.copy().rename(columns={
        #     "STATE":"state", "STATEFP":"stresfip"})
        # self.death_df = self.death_df.merge(merged_fip_df, how = "left")
        # self.death_df = self.death_df.rename(columns={
        #     "state": "STATE", "stresfip": "STATEFP"})

    def extract_age(self):
        """
        Extracts single year age from a loaded raw NCHS data frame.
        """
        if self.year > 2003:
            age_df = self.raw_df["age"]
        self.death_df.loc[:, "AGE"] = age_df
        return None

    def extract_county(self):
        """
        Extracts county (3 digit fips code) from a loaded raw NCHS data frame.
        """
        if self.year >= 2003:
            county_df = self.raw_df["cntyfips"].copy()
        county_df.replace({"000": pd.NA, "999": pd.NA}, inplace=True)
        self.death_df.loc[:, "COUNTYFP"] = self.death_df["STATEFP"].copy() +\
            county_df
        return None

    def extract_mothers_bridged_race4(self):
        """
        Extracts bridged race group from NCHS data. Observations will be one of
        the following 4 groups. White, Black, API (Asian Pacific Islander),
        AIAN (American Indian Alaskan Native).
        """
        if self.year <= 2002:
            mbrace = pd.Series(pd.NA, index=self.raw_df.index).case_when(
                [(self.raw_df["mrace"] == 1, "White"),
                (self.raw_df["mrace"] == 2, "Black"),
                (self.raw_df["mrace"] == 3, "AIAN"),
                (self.raw_df["mrace"].isin([4, 5, 6, 7]), "API"),
                (self.raw_df["mrace"].isin(range(8, 88, 10)), "API"),
                (self.raw_df["mrace"] == 9, pd.NA)
                ])
        elif self.year > 2002 and self.year <= 2019:
            race_col = "mracerec" if self.year < 2014 else "mbrace"
            mbrace = pd.Series(pd.NA, index=self.raw_df.index).case_when(
                [(pd.to_numeric(self.raw_df[race_col]) == 1, "White"),
                (pd.to_numeric(self.raw_df[race_col]) == 2, "Black"),
                (pd.to_numeric(self.raw_df[race_col]) == 3, "AIAN"),
                (pd.to_numeric(self.raw_df[race_col]) == 4, "API"),
                (pd.to_numeric(self.raw_df[race_col]) == 9, pd.NA)
                ])
        # bridged race is not present in data 2020 and beyond
        elif self.year >= 2020:
            mbrace = pd.Series(pd.NA, index=self.raw_df.index)
        self.death_df.loc[:, "MBRACE4"] = mbrace
        return None
    
    def extract_mothers_race40(self):
        """
        Extracts multiple race group from NCHS data. Observations will be one of
        the following 40 groups. See page 15 here
        https://ftp.cdc.gov/pub/Health_Statistics/NCHS/Dataset_Documentation/DVS/mortality/2024-Mortality-Public-Use-File-Documentation.pdf
        """
        if self.year <= 2002:
            mbrace = pd.Series(pd.NA, index=self.raw_df.index).case_when(
                [(self.raw_df["mrace"] == 1, "White"),
                (self.raw_df["mrace"] == 2, "Black"),
                (self.raw_df["mrace"] == 3, "AIAN"),
                (self.raw_df["mrace"].isin([4, 5, 6, 7]), "API"),
                (self.raw_df["mrace"].isin(range(8, 88, 10)), "API"),
                (self.raw_df["mrace"] == 9, pd.NA)
                ])
        elif self.year > 2002 and self.year <= 2019:
            race_col = "mracerec" if self.year < 2014 else "mbrace"
            mbrace = pd.Series(pd.NA, index=self.raw_df.index).case_when(
                [(pd.to_numeric(self.raw_df[race_col]) == 1, "White"),
                (pd.to_numeric(self.raw_df[race_col]) == 2, "Black"),
                (pd.to_numeric(self.raw_df[race_col]) == 3, "AIAN"),
                (pd.to_numeric(self.raw_df[race_col]) == 4, "API"),
                (pd.to_numeric(self.raw_df[race_col]) == 9, pd.NA)
                ])
        # bridged race is not present in data 2020 and beyond
        elif self.year < 2018:
            mbrace = pd.Series(pd.NA, index=self.raw_df.index)
        self.death_df.loc[:, "MBRACE4"] = mbrace
        return None

    def extract_mothers_hispanic(self):
        """
        Extract mothers hispanic ethicity, True or False.
        """
        hisp5 = [1, 2, 3, 4, 5]
        if self.year <= 2002:
            mhisp = pd.Series(pd.NA, index=self.raw_df.index).case_when(
                [
                (pd.to_numeric(self.raw_df["orracem"]).isin(hisp5), True),
                (pd.to_numeric(self.raw_df["orracem"]).isin([6,7,8]), False),
                (pd.to_numeric(self.raw_df["orracem"]) == 9, pd.NA)
                ])
        elif self.year > 2002 and self.year <= 2013:
            mhisp = pd.Series(pd.NA, index=self.raw_df.index).case_when(
                [
                (pd.to_numeric(self.raw_df["mracehisp"]).isin(hisp5), True),
                (pd.to_numeric(self.raw_df["mracehisp"]).isin([6,7,8]), False),
                (pd.to_numeric(self.raw_df["mracehisp"]) == 9, pd.NA)
                ])
        elif self.year >= 2014:
            mhisp = pd.Series(pd.NA, index=self.raw_df.index).case_when(
                [
                (pd.to_numeric(self.raw_df["mhisp_r"]).isin(hisp5), True),
                (pd.to_numeric(self.raw_df["mhisp_r"]).isin([0]), False),
                (pd.to_numeric(self.raw_df["mhisp_r"]) == 9, pd.NA)
                ])
        self.death_df.loc[:, "MHISP"] = mhisp
        return None


if __name__ == "__main__":
    for year in range(2024, 2025):
        for state in ["OR"]:
            print("Extraction for " + state + " year " + str(year))
            DE = NCHSDeathExtraction(year = year, state = state)
            DE.read_data(select_cols = [
                "age", "marstat", "sex", "ucod", "pregstat", "monthdth", "race40", "hispanic"])
            DE.raw_df.to_csv(
                "~/Documents/maternal_mortality/Data/Deaths/{}.csv".format(year),
                index = False)

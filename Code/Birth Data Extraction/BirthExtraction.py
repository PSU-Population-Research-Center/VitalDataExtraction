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
    Pulls specifications for reading an NCHS birth file from a fwf from the 
    NBER website in data frame format.

    Parameters
    ----------
    year : int
            year of nchs data to read dictionary for

    Returns
    -------
    pd.DataFrame
        a data frame with text for reading fixed width NCHS birth file
    """
    surl = "https://data.nber.org/nvss/natality/programs/dct/natality" +\
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
    Pulls specifications for reading an NCHS birth file from a fwf from the 
    NBER website.

    Parameters
    ----------
    year : int
            year of nchs data to read dictionary for

    Returns
    -------
    dict
        a dictionary with specifications for reading fixed width NCHS birth file
    """
    dldf = read_nchs_df(year)
    dldf["start"] = dldf[0].apply(lambda x: int(re.findall(r'\d+', x)[0])-1)
    dldf["end"] = dldf[3].apply(
        lambda x: int(re.findall(r'\d+', x)[0])) + dldf["start"]
    dldf["var"] = dldf[2]
    dldf["type"] = dldf[3].apply(
        lambda x: ["str", "Int64"][x[2] == "f"])
    r_ = range(dldf.shape[0])
    src_dct = {
        dldf["var"][i]: tuple([dldf["start"][i], dldf["end"][i]]) for i in r_}
    src_dtype = {dldf["var"][i]: dldf["type"][i] for i in r_}
    if year >= 2003 and year <= 2013:
        src_dct["mrstate"] = tuple([108, 110])
        src_dct["mrcntyfips"] = tuple([113, 116])
        src_dtype["mrstate"] = "str"
        src_dtype["mrcntyfips"] = "str"
    if year >= 2014 and year <= 2020:
        src_dct["mrstate"] = tuple([88, 90])
        src_dct["mrcntyfips"] = tuple([90, 93])
        src_dtype["mrstate"] = "str"
        src_dtype["mrcntyfips"] = "str"
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
        "national_state2020.txt", sep = "|").rename(
            columns={"STATE": "mrstate", "STATEFP": "stresfip"})
    fip_abv_df["stresfip"] = fip_abv_df[
        "stresfip"].astype(str).str.pad(2,fillchar='0')
    fip_abv_df = fip_abv_df[["mrstate", "stresfip"]]
    return fip_abv_df


class BirthExtraction(object):
    """
    A generic class used to extract birth data from various file types.

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
        self.birth_df = pd.DataFrame()

    def read_data(self):
        return None


class NCHSBirthExtraction(BirthExtraction):
    """
    Class used to extract birth data from NCHS files.

    ...

    Attributes
    ----------
    year : int
        year of data to extract
    state : str
        state of data to extract
    """
    def __init__(self, year, state):
        geo_stub = "" if year < 1994 else "USPS"
        src_str = "/vol/share/population_research/_DATA/NCHS_BIRTH/" +\
            "NatAC{}/NATL{}{}.AllCnty.zip".format(year, year, geo_stub)
        super().__init__(year, state, source = src_str)
        self.state_idx = None
        self.data_dict = read_nchs_dict(year)
        self.data_dict_src = "https://data.nber.org/nvss/natality/" +\
            "programs/dct/natality" + str(year) + ".dct"

    def read_state_res_data(self):
        """
        Read in the indexes for states from the raw data, shouldnt be used by
        itself for most use cases.

        Parameters
        ----------
        None
        """
        fip_abv_df = read_state_fips_df()
        z = zipfile.ZipFile(self.source)
        sfs = [x for x in z.namelist() if x.endswith("txt")]
        colnames = ["mrstate" if self.year >= 2003 else "stresfip"]
        colspecs = [self.data_dict["pos"][i] for i in colnames]
        dts = {i: "str" for i in colnames}
        state_idx_raw = [pd.read_fwf(
            z.open(sf), names=colnames, colspecs=colspecs,
            dtype = dts) for sf in sfs]
        self.state_idx = [
            x.merge(fip_abv_df, how = "left") for x in state_idx_raw]

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
        self.read_state_res_data()
        skips = [
            np.where(x.mrstate != self.state)[0] for x in self.state_idx]
        raw_df = pd.concat([pd.read_fwf(
            z.open(sfs[i]), names=colnames, colspecs=colspecs,
            dtype = dts, skiprows = skips[i], **kwargs) 
            for i in range(len(self.state_idx))])
        self.raw_df = raw_df

    def extract_age(self):
        """
        Extracts single year age from a loaded raw NCHS data frame.
        """
        if self.year <= 2002:
            age_df = self.raw_df[["dmage"]]
        if self.year == 2003:
            age_df = self.raw_df[["mager41"]] + 13
        if self.year > 2003:
            age_df = self.raw_df[["mager"]]
        age_df.columns.values[0] = "AGE"
        self.birth_df = pd.concat([self.birth_df, age_df], axis = 1)
        return None
    
    def extract_county(self):
        """
        Extracts county (3 digit fips code) from a loaded raw NCHS data frame.
        """
        if self.year <= 2002:
            county_df = pd.DataFrame(
                self.raw_df["cntyres"].apply(lambda x: x[2:5]))
        if self.year >= 2003:
            county_df = self.raw_df[["mrcntyfips"]]
        county_df.columns.values[0] = "COUNTY"
        self.birth_df = pd.concat([self.birth_df, county_df], axis = 1)
        return None

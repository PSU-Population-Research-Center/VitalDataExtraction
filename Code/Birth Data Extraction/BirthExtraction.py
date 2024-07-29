import pandas as pd
import numpy as np
import zipfile
import json
import os
from urllib.request import urlopen
import re
import numpy as np

def read_nchs_dict(year):
    surl = "https://data.nber.org/nvss/natality/programs/dct/natality" +\
        str(year) + ".dct"
    source_lines = [str(l).replace("b'", "") for l in urlopen(surl)]
    trimmed_lines = [re.sub(" *\\)", ")", str(l)) for l in source_lines]
    sub_lines = [
        l.replace("'", "") for l in trimmed_lines if l.startswith("_col")]
    tmp_path = "/tmp/tmp_dta_src"
    f = open(tmp_path, "w")
    f.writelines([s.replace("\\n", "\n") for s in sub_lines])
    f.close()
    dldf = pd.read_table(tmp_path, sep="\\s+", header = None)
    os.remove(tmp_path)
    dldf["start"] = dldf[0].apply(lambda x: int(re.findall(r'\d+', x)[0])-1)
    dldf["end"] = dldf[3].apply(
        lambda x: int(re.findall(r'\d+', x)[0])) + dldf["start"]
    dldf["var"] = dldf[2]
    dldf["type"] = dldf[3].apply(
        lambda x: ["str", "Int64"][x[2] == "f"])
    r_ = range(dldf.shape[0])
    src_dct = {
        dldf["var"][i]: tuple([dldf["start"][i], dldf["end"][i]]) for i in r_}
    src_dtype = {
        dldf["var"][i]: dldf["type"][i] for i in r_}
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
    

class BirthExtraction(object):
        def __init__(self, year, source, quarter = None):
            self.year = year
            self.source = source
            self.quarter = quarter
            self.raw_df = None
            self.birth_df = None

        def read_data(self):
            return None
        
        def extract_data(self): 
            return None


class NCHSBirthExtraction(BirthExtraction):
        def __init__(self, year):
            super().__init__(year, source = NCHSBIRTHMETA[year]["source"])
            self.state_idx = None
            self.data_dict = read_nchs_dict(year)
            self.data_dict_src = "https://data.nber.org/nvss/natality/" +\
                "programs/dct/natality" + str(year) + ".dct"

        def read_state_res_data(self):
            fip_abv_df = pd.read_table(
                "https://www2.census.gov/geo/docs/reference/codes2020/" +\
                "national_state2020.txt", sep = "|").rename(
                    columns={"STATE": "mrstate", "STATEFP": "stresfip"})
            fip_abv_df["stresfip"] = fip_abv_df[
                "stresfip"].astype(str).str.pad(2,fillchar='0')
            fip_abv_df = fip_abv_df[["mrstate", "stresfip"]]
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

        def read_data(self, state_sub = None, **kwargs):
            z = zipfile.ZipFile(self.source)
            sfs = [x for x in z.namelist() if x.endswith("txt")]
            colnames = list(self.data_dict["pos"].keys())
            colspecs = [self.data_dict["pos"][i] for i in colnames]
            dts = self.data_dict["dtype"]
            skips = [None for i in range(len(sfs))]
            if state_sub is not None:
                self.read_state_res_data()
                skips = [np.where(
                    x.mrstate != state_sub)[0] for x in self.state_idx]
            raw_df = pd.concat([pd.read_fwf(
                z.open(sfs[i]), names=colnames, colspecs=colspecs,
                dtype = dts, skiprows = skips[i], **kwargs) 
                for i in range(len(self.state_idx))])
            self.raw_df = raw_df

        def extract_data(self):
            return None

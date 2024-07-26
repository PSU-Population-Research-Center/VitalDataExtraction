import pandas as pd
import numpy as np
import zipfile
from BirthMeta import NCHSBIRTHMETA

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

        def read_data(self):
            z = zipfile.ZipFile(self.source)
            sfs = [x for x in z.namelist() if x.endswith("txt")]
            colnames = list(NCHSBIRTHMETA[self.year]["cols"].keys())
            colspecs = list(NCHSBIRTHMETA[self.year]["cols"].values())
            raw_df = pd.concat([pd.read_fwf(
                z.open(sf), names=colnames, colspecs=colspecs) for sf in sfs])
            self.raw_df = raw_df

        def extract_data(self):
            return None

# Strategy of Vital Data Extraction

## Primary Step Build Skeleton
At minimum this is using NCHS data sources to build a skeleton of the number of births in a given year or quarter. More detailed data may be extracted here for matching and treated as set. In this way we may merge data from multiple sources into one data source. 

# Race Variables
Race variables change over time and given that this process in part tries to harmonize data overtime there is going to be data transformation and loss in this process. We take an approach that there are a number of potential categories an individual can identify with that fall under the umbrella of race/ethnicity and an individual can have an association with multiple groups. The variables that we extract in this process are currently the following; White, Black, API, AIAN, Hispanic.

## Birth Output
| ID| Age Of Mother | State | County | MOTHER RACE |  Date  | Year | Lat | Lon |
| - | ------------- | ----- | ------ | ----------- | ------ | ---- | --- | --- |
| 1 |      28       |   41  |   001  |     TRUE    | 1/1/99 | 1990 |  9  |  9  | 
|...|      ...      |  ...  |   ...  |     ...     |   ...  | ...  | ... |  9  |
|999|      32       |   41  |   009  |     FALSE   | 1/2/09 | 2009 |  3  |  9  |


## code example
```python
import NCHSBirthExtraction from BirthExtraction

# loads an object which will read data for a year state combination
BirthModule = NCHSBirthExtraction(1994)

# reads in the raw data
BirthModule.read_data()

# Extract some data
BirthModule.extract_age()

# Validate extracts
BirthModule.validate()

# Write the extracted data
BirthModule.write_extract()
```

## How to run singularity env
To run the Singularity environment be sure you are in the singularity folder and run the following code to start an `ipython` console

```
singularity run --bind /vol:/vol ./singularity-conda.sif ipython
```

## Variables to extract

### Mother Foreign Born
Variable: MFBORN  
Domain: Boolean  
Method: `self.extract_mothers_fborn()`  
Description: Mothers foreign born status, whether they were born in the the US or somewhere else.

### Mother Education
Variable: MEDU  
Domain: String, "Less than High School", "High School Grad", "Bachelor's Degree"  
Method: `self.extract_mothers_edu()`  
Description: Mothers education. For early NCHS years high school diploma and
bachelors degree was not recorded. For those years we shall use at least 4 years
of high school to denote high school grad and use at least 4 years of college to
denote bachelors degree.  

### Fathers Age
Variable: FAGE  
Domain: Numeric  
Method: `self.extract_fathers_age()`  
Description: Fathers single year age.

### Fathers Bridged Race 4
Variable: FBRACE4  
Domain: String
Method: `self.extract_fathers_bridged_race4()`  
Description: Fathers bridged race. Must be one of White, Black, API, or AIAN.

### Father Hispanic
Variable: FHISP  
Domain: Boolean
Method: `self.extract_fathers_hispanic()`  
Description: Fathers Hispanic Identity.

### Father Foreign Born
Variable: FFBORN  
Domain: Boolean
Method: `self.extract_fathers_fborn()`  
Description: Fathers foreign born status, whether they were born in the the US or somewhere else. 

### Sex of Child
Variable: SEX  
Domain: String, "Male" or "Female"  
Method: `self.extract_sex()`  
Description: Extract binary sex of child.

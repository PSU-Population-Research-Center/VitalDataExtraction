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


# code example
```python
import NCHSBirthExtraction from BirthExtraction

# loads an object which will read data for a year state combination
BirthModule = NCHSBirthExtraction(1994, "OR")

# reads in the raw data
BirthModule.read_data()

# Extract some data
BirthModule.extract_age()

# Validate extracts
BirthModule.validate()

# Write the extracted data
BirthModule.write_extract()
```

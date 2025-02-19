# std libs
import os

# third party libs
import yaml
import pandas as pd

# custom libs
from sql_tools import write_to_database


# constant variables
FILENAME = os.path.join(os.getcwd(), 'creds.yaml')

# accessing DB credentials
with open(FILENAME, "r") as file:
    creds = yaml.safe_load(file)
    
# defining dtypes

METEO_TYPES = {'temperature':'float64','relative_humidity':'float64',
               'precipitation_rate':'float64','wind_speed':'float64',
               'zipcode':'str'}
CONTRACT_TYPES = {'CONTRACT_ID':'int64','CLIENT_TYPE_ID':'int64',
                   'AVG_EUROS_IMPORT':'float64','POWER_P1':'float64',
                   'HAS_GAS':'boolean','HAS_SOLAR':'boolean','ZIPCODE':'str'}
ZIPCODE_TYPES = {'ZIPCODE':'str','ZC_LATITUDE':'float64',
                 'ZC_LONGITUDE':'float64','AUTONOMOUS_COMMUNITY':'str',
                 'AUTONOMOUS_COMMUNITY_NK':'str','PROVINCE':'str'}


# helpers
# defining filtering condition function that will be used to store only relevant meteo records in memory
def _filter_data_isin(table: str, column: str, lookup: list):
    '''
    Arg:
        table -> table you want to filter
        column -> table column as input for the lookup
        lookup -> list or any iterable that contains lookup values
    '''
    return table[table[column].isin(lookup)]

# defining a function to categorize p1_power column
def _category_p(power: float) -> str:
    if power >= 5000:
        return 'Over 5 MW'
    elif power < 3000:
        return 'Under 3 MW'
    else:
        return 'Between 3 and 5 MW'


# creating dataframes from csv files skipping the meteo one for now
df_contracts = pd.read_csv('contracts_eae.csv', dtype=CONTRACT_TYPES)
df_zipcode = pd.read_csv('zipcode_eae_v2.csv', dtype=ZIPCODE_TYPES)

# normalizing column names in lowercase
df_contracts.columns = df_contracts.columns.str.lower()
df_zipcode.columns = df_zipcode.columns.str.lower()

# listing top 10 zipcodes by contract count
zipcode_grouped = df_contracts.groupby('zipcode')['contract_id'].count().reset_index()
zipcode_top =  list(zipcode_grouped.nlargest(10,'contract_id')['zipcode'])

# fetching filtered df for meteo
# for each record in meteo we will check if the zipcode is among the top 10 before appending them to a dataframe
# the following line does not really populate the df
# the chunksize argument transforms it into an iterator that loads once it is processed
chunks = pd.read_csv('meteo_eae.csv', chunksize = 100000, \
                        dtype = METEO_TYPES, parse_dates= ['date'])

# now we are processing the chunks and concatenating them only with filtered values
# all not necessary values are destroyed after the following line is processed
df_meteo_top = pd.concat([_filter_data_isin(table=chunk, \
                            column='zipcode',lookup=zipcode_top) \
                            for chunk in chunks], ignore_index=True)

# creating p1 category as required
df_contracts['p1_category'] = df_contracts['power_p1'].apply(lambda x: _category_p(x))

# filtering out client type 0
df_contracts = df_contracts[df_contracts['client_type_id']==0]

#performing the required join
df_contracts_temperatures = df_contracts.merge(df_meteo_top, how='right', left_on='zipcode', right_on='zipcode')

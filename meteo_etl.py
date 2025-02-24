
# Importing standard libraries
import os

# Importing third party libraries
import yaml
import pandas as pd

# Importing custom libraries
from sql_tools import write_to_database


# Defining the constant variables 
FILENAME = os.path.join(os.getcwd(), 'creds.yaml')

# Defining the data types for the .csv files
# Note: Changing the has_solar dtype in the contracts table from int to bool for later classification use  
METEO_TYPES = {'temperature':'float64','relative_humidity':'float64',
               'precipitation_rate':'float64','wind_speed':'float64',
               'zipcode':'str'}
CONTRACT_TYPES = {'CONTRACT_ID':'int64','CLIENT_TYPE_ID':'int64',
                   'AVG_EUROS_IMPORT':'float64','POWER_P1':'float64',
                   'HAS_GAS':'boolean','HAS_SOLAR':'boolean','ZIPCODE':'str'}
ZIPCODE_TYPES = {'ZIPCODE':'str','ZC_LATITUDE':'float64',
                 'ZC_LONGITUDE':'float64','AUTONOMOUS_COMMUNITY':'str',
                 'AUTONOMOUS_COMMUNITY_NK':'str','PROVINCE':'str'}

# Defining final look of the tables
FINAL_COLS_RENAME = {'p1_category':'power_category', 'temperature_min':'min_temperature',
           'temperature_max':'max_temperature', 'relative_humidity_mean' : 'avg_rel_humidity',
            'contract_id_count':'n'}
FINAL_COLS = ['zipcode' , 'year', 'month', 'power_category', \
           'max_temperature', 'min_temperature', 'avg_rel_humidity','n']

# Accessing the database credentials for MySQL Workbench
with open(FILENAME, "r") as file:
    creds = yaml.safe_load(file)
    
# Helpers
# Defining a filtering condition function that will be used to store only relevant meteo records in memory
def _filter_data_isin(table: str, column: str, lookup: list):
    '''
    Arg:
        table -> table you want to filter
        column -> table column as input for the lookup
        lookup -> list or any iterable that contains lookup values
    '''
    return table[table[column].isin(lookup)]

# Defining a function to categorize p1_power column in the contracts table
def _category_p(power: float) -> str:
    if power >= 5000:
        return 'Over 5 MW'
    elif power < 3000:
        return 'Under 3 MW'
    else:
        return 'Between 3 and 5 MW'

# Reading data
def read_data():
    
    # Creating dataframes from csv files 
    # The meteo file will be loaded later 
    df_contracts = pd.read_csv('contracts_eae.csv', dtype=CONTRACT_TYPES)
    df_zipcode = pd.read_csv('zipcode_eae_v2.csv', dtype=ZIPCODE_TYPES)

    # Normalizing column names in lowercase 
    df_contracts.columns = df_contracts.columns.str.lower()
    df_zipcode.columns = df_zipcode.columns.str.lower()

    # Identifying all zipcodes with more than 10 contracts
    zipcode_grouped = df_contracts.groupby('zipcode')['contract_id'].count()
    zipcode_top = list(zipcode_grouped[zipcode_grouped > 10].index)

    # Fetching filtered df for meteo_eae.csv
    # For each record in meteo we will check if the zipcode has >10 contracts
    # The following line does not immediately populate the df
    # The chunksize argument transforms it into an iterator that loads the data into the df once it is processed
    chunks = pd.read_csv('meteo_eae.csv', chunksize = 100000, delimiter=';', \
                            dtype = METEO_TYPES, parse_dates= ['date'])

    # Now we are processing the chunks and concatenating them only with zipcodes associated with >10 contracts
    # All not unnecessary values are destroyed after the following line is processed
    df_meteo_top_raw = pd.concat([_filter_data_isin(table=chunk, \
                                column='zipcode',lookup=zipcode_top) \
                                for chunk in chunks], ignore_index=True)
    
    return df_contracts, df_meteo_top_raw

# Transforming data
def transform_data(df_contracts, df_meteo_top_raw):
    
    # Applying the helper function _category_p() to the contracts df to classify power usage 
    df_contracts['p1_category'] = df_contracts['power_p1'].apply(lambda x: _category_p(x))

    # Keeping only clients with client_type == 0 in the contracts df
    df_contracts_zero_raw = df_contracts[df_contracts['client_type_id']==0]

    # Removing unnecessary columns before creating the joint table of meteo and contracts
    df_contracts_zero = df_contracts_zero_raw[['contract_id','p1_category','zipcode','has_solar']]
    df_meteo_top = df_meteo_top_raw[['date','temperature','relative_humidity','zipcode']]

    # Performing the required right join on zipcode between df_meteo_top and df_contracts_zero
    df_solar_indicators_raw = df_contracts_zero.merge(df_meteo_top, how='right', \
                                                                left_on='zipcode', right_on='zipcode')

    # Separating the date column into 2 columns: year and month
    # Removing the now obsolete date column 
    df_solar_indicators_raw['year'] = df_solar_indicators_raw['date'].dt.strftime("%Y")
    df_solar_indicators_raw['month'] = df_solar_indicators_raw['date'].dt.strftime("%B")
    df_solar_indicators_raw = df_solar_indicators_raw.drop(columns='date')

    # Performing the groupby to generate max temp, min temp, and avg relative humidity 
    df_solar_indicators_raw = df_solar_indicators_raw.groupby(['year','month','zipcode','p1_category','has_solar']).agg( \
                                    {'temperature':['min', 'max'],'relative_humidity':'mean','contract_id':'count'} \
                                    ).reset_index()

    # Flattening the multi_index generated by the groupby in order to prepare for loading df into MySQL Database
    df_solar_indicators_raw.columns = ['_'.join(col).strip('_') for col in df_solar_indicators_raw.columns]
    df_solar_indicators_raw = df_solar_indicators_raw.rename(columns=FINAL_COLS_RENAME)

    # Rounding temperatures and reverting avg_rel_humidity from percentages to decimals
    df_solar_indicators_raw['max_temperature'] = df_solar_indicators_raw['max_temperature'].round(1)
    df_solar_indicators_raw['min_temperature'] = df_solar_indicators_raw['max_temperature'].round(1)
    df_solar_indicators_raw['avg_rel_humidity'] = (df_solar_indicators_raw['avg_rel_humidity']/100).round(2)


    # Creating two df by splitting df_solar_indicators_raw into contracts with and without solar
    solar_indicators_with_solar = df_solar_indicators_raw[df_solar_indicators_raw['has_solar']==True][FINAL_COLS]
    solar_indicators_no_solar = df_solar_indicators_raw[df_solar_indicators_raw['has_solar']==False][FINAL_COLS]

    return solar_indicators_no_solar, solar_indicators_with_solar

# Writing data
def load_data(solar_indicators_no_solar,solar_indicators_with_solar):
    
    # Loading the two df into MySQL Workbench
    write_to_database(creds=creds['mysql-db'], df=solar_indicators_with_solar, table_name='solar_indicators_with_solar_ft', if_exists='replace')
    write_to_database(creds=creds['mysql-db'], df=solar_indicators_no_solar, table_name='solar_indicators_no_solar_ft', if_exists='replace')
    message = 'Tasks run successfully'
    
    return message

# Execution
def main():
    
    # Defining execution of the tasks
    initial_dataframes = read_data()
    final_dataframes = transform_data(initial_dataframes[0],initial_dataframes[1])
    final_message = load_data(final_dataframes[0],final_dataframes[1])
    print(final_message)

if __name__ == '__main__':
    main()
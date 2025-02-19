#std libs
import os

#third party libs
import yaml
import pandas as pd

#custom libs
from sql_tools import write_to_database

#VARIABLES
FILENAME = os.path.join(os.getcwd(), 'creds.yaml')

#Accessing DB credentials
with open(FILENAME, "r") as file:
    creds = yaml.safe_load(file)
    
#Defining dtypes

meteo_types = {'temperature':'float64','relative_humidity':'float64',
               'precipitation_rate':'float64','wind_speed':'float64',
               'zipcode':'str'}
contracts_types = {'CONTRACT_ID':'int64','CLIENT_TYPE_ID':'int64',
                   'AVG_EUROS_IMPORT':'float64','POWER_P1':'float64',
                   'HAS_GAS':'boolean','HAS_SOLAR':'boolean','ZIPCODE':'str'}
zipcode_types = {'ZIPCODE':'str','ZC_LATITUDE':'float64',
                 'ZC_LONGITUDE':'float64','AUTONOMOUS_COMMUNITY':'str',
                 'AUTONOMOUS_COMMUNITY_NK':'str','PROVINCE':'str'}

#Creating dataframes from csv files
df_meteo = pd.read_csv('meteo_eae.csv', delimiter=';',dtype=meteo_types,parse_dates=['date'])
df_contracts = pd.read_csv('contracts_eae.csv', dtype=contracts_types)
df_zipcode = pd.read_csv('zipcode_eae_v2.csv', dtype=zipcode_types)

#no
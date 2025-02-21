# Importing standard libraries
import os

# Importing third party libraries
import pandas as pd
import yaml 
from sqlalchemy import create_engine

# Declaring constant variable 
FILENAME = os.path.join(os.getcwd(), 'creds.yaml')

# Read credentials from the cred.yaml file 
with open(FILENAME, "r") as file:
    creds = yaml.safe_load(file)


def reads_from_mysql(creds, query):
    """
    Returns as dataframe the result of a query to a MySQL database.

    Args:
        creds (dict): The credentials to access the database.
        query (string): The query.

    Returns:
        pandas dataframe: the output table of the query.
    """
    _db_user = creds['username']
    _db_password = creds['password']
    _db_host = creds['host']
    _db_name = creds['database']
    engine = create_engine(f"mysql://{_db_user}:{_db_password}@{_db_host}:3306/{_db_name}")
    df = pd.read_sql(query, engine)
    return df

def write_to_database(creds, df, table_name, if_exists='append'):
    """
    Write a dataframe into a MySql table.

    Args:
        creds (dict): The credentials to access the database.
        df (pandas DataFrame): The table to load.
        table_name (str): The table name in the database
        if_exists (str): Default 'append'. Other values are 'fail' and 'replace'
    """
    _db_user = creds['username']
    _db_password = creds['password']
    _db_host = creds['host']
    _db_name = creds['database']
    engine = create_engine(f"mysql://{_db_user}:{_db_password}@{_db_host}:3306/{_db_name}")
    with engine.connect() as connection:
        df.to_sql(table_name, con=connection, if_exists=if_exists, index=False) 

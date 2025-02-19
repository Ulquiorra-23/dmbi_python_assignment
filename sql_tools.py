#std libs
import os

#third party libs
from sqlalchemy import create_engine

#VARIABLES
FILENAME = os.path.join(os.getcwd(), 'creds.yaml')


with open(FILENAME, "r") as file:
    creds = yaml.safe_load(file)


def reads_from_mysql(creds, query):
    _db_user = creds['username']
    _db_password = creds['password']
    _db_host = creds['host']
    _db_name = creds['database']
    engine = create_engine(f"mysql://{_db_user}:{_db_password}@{_db_host}:3306/{_db_name}")
    df = pd.read_sql(query, engine)
    return df

def write_to_database(creds, df, table_name, if_exists='append'):
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
    with engine.connect() as connection:
        df.to_sql(table_name, con=connection, if_exists=if_exists, index=False) 

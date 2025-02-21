# Python ETL - Group Project

## Python ETL:
Automatically pull data from .csv files, apply standardized transformations, and upload the processed data to a MySQL Workbench database.

## Group members:
[Juan Jose Montesinos](https://www.linkedin.com/in/jmont90/)\
[Maximilian von Braun](https://www.linkedin.com/in/maximilian-von-braun-b714b624b/)\
[Jakob Spranger](https://www.linkedin.com/in/jakob-spranger-3396b2170/)\
[Massimiliano Napolitano](https://www.linkedin.com/in/massimiliano-nap/)

## How to run the ETL process:
1. Go into the *creds.yaml* file and configure the database address, host, username, and password to your target database in MySQL Workbench

2. Make sure the following .csv files are present in this folder. The filenames are as follows:\
a. contracts_eae.csv\
b. meteo_eae.csv\
c. zipcode_eae_v2.csv

3. Run the *py_etl.py* file to perform the ETL process

4. After completion, you should see the new tables in your MySQL Workbench database

## Optimizations:
We performed 2 optimizations to improve memory usage:

1. During the transformations, we only keep the relevant columns from the **contracts** and **meteo** tables. This improves performance by ignoring columns not needed for the transformation

2. When reading the *meteo_eae.csv* file, we declare a chunksize of 100,000 rows per chunk. In doing so, we incrementally read the file and consider only the data for relevant zipcodes (i.e. those with >10 contracts) instead of loading the full file and removing irrelevant zipcodes later
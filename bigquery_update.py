from google.oauth2 import service_account
from google.cloud import bigquery
import pandas as pd

#Get Service Account
credentials_my = service_account.Credentials.from_service_account_file("your_service_account_key.json")

#Define Schema
job_config = bigquery.LoadJobConfig(schema=[
        bigquery.SchemaField("name", bigquery.enums.SqlTypeNames.STRING),
        bigquery.SchemaField("category", bigquery.enums.SqlTypeNames.STRING),
        bigquery.SchemaField("description", bigquery.enums.SqlTypeNames.STRING),
        bigquery.SchemaField("price", bigquery.enums.SqlTypeNames.INT64),
        bigquery.SchemaField("weight", bigquery.enums.SqlTypeNames.FLOAT64),
        bigquery.SchemaField("stock", bigquery.enums.SqlTypeNames.INT64),
        bigquery.SchemaField("image_urls", bigquery.enums.SqlTypeNames.STRING)
        ],
    write_disposition="WRITE_TRUNCATE")

#Connect to table
table_id = "your_project_id.your_dataset.your_table"
client_target = bigquery.Client(credentials=credentials_my, project="your_project_id")

#Get excel file
df = pd.read_excel("scraping_result (2021-09-11 15 43).xlsx")

#Upload table
client_target.load_table_from_dataframe(df, table_id, job_config=job_config)
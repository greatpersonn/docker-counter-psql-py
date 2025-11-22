import psycopg2
from config import DB_PARAMS

def get_conn():
    return psycopg2.connect(**DB_PARAMS)

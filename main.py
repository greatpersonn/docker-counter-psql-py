import time
import multiprocessing as mp
import psycopg2
from psycopg2 import sql
import sys

DB_PARAMS = {
    'dbname': 'counter_db',
    'user': 'admin',
    'password': 'admin',
    'host': 'postgres-db',
    'port': 5432
}

ITER = 10_000 
CLIENTS = 10 
USER_ID = 1

def reset_counter():
    conn = psycopg2.connect(**DB_PARAMS)
    cur = conn.cursor()
    cur.execute("UPDATE user_counters SET counter = 0, version = 0 WHERE user_id = %s", (USER_ID,))
    conn.commit()
    cur.close()
    conn.close()

def worker_lost_update(_):
    conn = psycopg2.connect(**DB_PARAMS)
    cur = conn.cursor()
    for i in range(ITER):
        cur.execute("BEGIN")
        cur.execute("SELECT counter FROM user_counters WHERE user_id = %s", (USER_ID,))
        row = cur.fetchone()
        c = row[0] if row else 0
        c += 1
        cur.execute("UPDATE user_counters SET counter = %s WHERE user_id = %s", (c, USER_ID))
        conn.commit()
    cur.close()
    conn.close()

def worker_serializable(_):
    conn = psycopg2.connect(**DB_PARAMS)
    conn.set_session(isolation_level='SERIALIZABLE', autocommit=False)
    cur = conn.cursor()
    for i in range(ITER):
        try:
            cur.execute("BEGIN")
            cur.execute("SELECT counter FROM user_counters WHERE user_id = %s", (USER_ID,))
            row = cur.fetchone()
            c = row[0] if row else 0
            c += 1
            cur.execute("UPDATE user_counters SET counter = %s WHERE user_id = %s", (c, USER_ID))
            conn.commit()
        except Exception as e:
            conn.rollback()
            try:
                cur.execute("BEGIN")
                cur.execute("SELECT counter FROM user_counters WHERE user_id = %s", (USER_ID,))
                row = cur.fetchone()
                c = row[0] if row else 0
                c += 1
                cur.execute("UPDATE user_counters SET counter = %s WHERE user_id = %s", (c, USER_ID))
                conn.commit()
            except Exception:
                conn.rollback()
    cur.close()
    conn.close()

def worker_inplace(_):
    conn = psycopg2.connect(**DB_PARAMS)
    cur = conn.cursor()
    for i in range(ITER):
        cur.execute("BEGIN")
        cur.execute("UPDATE user_counters SET counter = counter + 1 WHERE user_id = %s", (USER_ID,))
        conn.commit()
    cur.close()
    conn.close()

def worker_row_locking(_):
    conn = psycopg2.connect(**DB_PARAMS)
    cur = conn.cursor()
    for i in range(ITER):
        cur.execute("BEGIN")
        cur.execute("SELECT counter FROM user_counters WHERE user_id = %s FOR UPDATE", (USER_ID,))
        row = cur.fetchone()
        c = row[0]
        c += 1
        cur.execute("UPDATE user_counters SET counter = %s WHERE user_id = %s", (c, USER_ID))
        conn.commit()
    cur.close()
    conn.close()

def worker_optimistic(_):
    conn = psycopg2.connect(**DB_PARAMS)
    cur = conn.cursor()
    for i in range(ITER):
        while True:
            cur.execute("BEGIN")
            cur.execute("SELECT counter, version FROM user_counters WHERE user_id = %s", (USER_ID,))
            row = cur.fetchone()
            counter, version = row[0], row[1]
            new_counter = counter + 1
            new_version = version + 1
            cur.execute("""
                UPDATE user_counters
                SET counter = %s, version = %s
                WHERE user_id = %s AND version = %s
            """, (new_counter, new_version, USER_ID, version))
            conn.commit()
            if cur.rowcount > 0:
                break
    cur.close()
    conn.close()

VARIANTS = {
    'lost': worker_lost_update,
    'serializable': worker_serializable,
    'inplace': worker_inplace,
    'rowlock': worker_row_locking,
    'optimistic': worker_optimistic
}

def run_variant(name):
    reset_counter()
    func = VARIANTS[name]
    t0 = time.perf_counter()
    with mp.Pool(processes=CLIENTS) as pool:
        pool.map(func, range(CLIENTS))
    t1 = time.perf_counter()
    conn = psycopg2.connect(**DB_PARAMS)
    cur = conn.cursor()
    cur.execute("SELECT counter, version FROM user_counters WHERE user_id = %s", (USER_ID,))
    row = cur.fetchone()
    print(f"Variant={name} time={t1-t0:.3f}s final_counter={row[0]} final_version={row[1]}")
    cur.close()
    conn.close()

if __name__ == '__main__':
    if len(sys.argv) < 2 or sys.argv[1] not in VARIANTS:
        print("Usage: python3 main.py [lost|serializable|inplace|rowlock|optimistic]")
        sys.exit(1)
    run_variant(sys.argv[1])

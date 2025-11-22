from db.db_conn import get_conn
from config import ITER, USER_ID

def worker(_):
    conn = get_conn()
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
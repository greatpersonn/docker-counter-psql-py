from db.db_conn import get_conn
from config import ITER, USER_ID

def worker(_):
    conn = get_conn()
    cur = conn.cursor()
    for i in range(ITER):
        cur.execute("BEGIN")
        cur.execute("UPDATE user_counters SET counter = counter + 1 WHERE user_id = %s", (USER_ID,))
        conn.commit()
    cur.close()
    conn.close()

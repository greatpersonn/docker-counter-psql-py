from db.db_conn import get_conn
from config import ITER, USER_ID

def worker(_):
    conn = get_conn()
    cur = conn.cursor()
    for i in range(ITER):
        cur.execute("BEGIN")
        cur.execute("SELECT counter FROM user_counters WHERE user_id=%s", (USER_ID,))
        c = cur.fetchone()[0]
        c += 1
        cur.execute("UPDATE user_counters SET counter=%s WHERE user_id=%s", (c, USER_ID))
        conn.commit()
    cur.close()
    conn.close()

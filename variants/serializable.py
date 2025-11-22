from db.db_conn import get_conn
from config import ITER, USER_ID

def worker(_):
    conn = get_conn()
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
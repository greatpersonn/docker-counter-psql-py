from db import get_conn
from config import USER_ID

def reset_counter():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE user_counters SET counter = 0, version = 0 WHERE user_id = %s", (USER_ID,))
    conn.commit()
    cur.close()
    conn.close()

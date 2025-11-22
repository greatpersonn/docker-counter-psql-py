import time
import multiprocessing as mp
import sys

from reset import reset_counter
from db.db_conn import get_conn
from config import CLIENTS, USER_ID

from variants.lost_update import worker as lost_worker
from variants.serializable import worker as serializable_worker
from variants.inplace_update import worker as inplace_worker
from variants.row_locking import worker as rowlock_worker
from variants.optimistic import worker as optimistic_worker

VARIANTS = {
    'lost': lost_worker,
    'serializable': serializable_worker,
    'inplace': inplace_worker,
    'rowlock': rowlock_worker,
    'optimistic': optimistic_worker
}

def run_variant(name):
    reset_counter()
    func = VARIANTS[name]

    t0 = time.perf_counter()
    with mp.Pool(processes=CLIENTS) as pool:
        pool.map(func, range(CLIENTS))
    t1 = time.perf_counter()

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT counter, version FROM user_counters WHERE user_id=%s", (USER_ID,))
    final = cur.fetchone()
    print(f"Variant={name} time={t1-t0:.3f}s final_counter={final[0]} final_version={final[1]}")
    cur.close()
    conn.close()

if __name__ == '__main__':
    if len(sys.argv) < 2 or sys.argv[1] not in VARIANTS:
        print("Usage: python3 main.py [lost|serializable|inplace|rowlock|optimistic]")
        sys.exit(1)
    run_variant(sys.argv[1])

import sys
import database

sql = " ".join(sys.argv[1:])
c = database.connect()
cur = c.execute(sql)
rows = cur.fetchall()

if not rows:
    print("(no rows)")
else:
    cols = [d[0] for d in cur.description]
    data = [[str(v) for v in r] for r in rows]
    widths = [max(len(cols[i]), *(len(row[i]) for row in data)) for i in range(len(cols))]
    line = "  ".join(col.ljust(w) for col, w in zip(cols, widths))
    print(line)
    print("  ".join("-" * w for w in widths))
    for row in data:
        print("  ".join(v.ljust(w) for v, w in zip(row, widths)))

c.commit()
c.close()


# python q.py "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
# python q.py "SELECT * FROM images"
# python q.py "SELECT * FROM export_history"
# python q.py "SELECT * FROM edit_history"
# python q.py "PRAGMA foreign_key_check"
import json, sqlite3, os
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

BASE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE, 'gift')
# Use the supplied schema only. Older copies call the expense table `expenses`;
# installations that use the requested `expensex` name are supported too.
con = sqlite3.connect(DB)
tables = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
EXPENSE_TABLE = 'expensex' if 'expensex' in tables else 'expenses'
con.close()

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=BASE, **kw)

    def send_json(self, data):
        b = json.dumps(data, ensure_ascii=False).encode();
        self.send_response(200);
        self.send_header('Content-Type', 'application/json; charset=utf-8');
        self.send_header('Content-Length', str(len(b)));
        self.end_headers();
        self.wfile.write(b)

    def do_GET(self):
        p = urlparse(self.path).path
        if not p.startswith('/api/'): return super().do_GET()
        c = sqlite3.connect(DB);
        c.row_factory = sqlite3.Row
        if p == '/api/data':
            bills = [dict(x) for x in c.execute(
                'SELECT g.id,g.name,g.date,count(i.id) people,coalesce(sum(CAST(i.amount AS REAL)),0) amount FROM gift g LEFT JOIN income i ON i.gift_id=g.id GROUP BY g.id ORDER BY g.date DESC,g.id DESC')]
            people = [dict(x) for x in c.execute(
                'SELECT i.id,i.gift_id AS bill_id,i.name,CAST(i.relation_id AS INTEGER) relation_id,CAST(i.amount AS REAL) amount,i."desc" AS note,g.name bill,r.name relation FROM income i LEFT JOIN gift g ON g.id=i.gift_id LEFT JOIN relation r ON r.id=CAST(i.relation_id AS INTEGER) ORDER BY i.id DESC')]
            expenses = [dict(x) for x in c.execute(
                'SELECT e.*,r.name relation,ca.name category FROM ' + EXPENSE_TABLE + ' e LEFT JOIN relation r ON r.id=e.relation_id LEFT JOIN cate ca ON ca.id=e.cate_id ORDER BY e.date DESC,e.id DESC')]
            self.send_json({'bills': bills, 'people': people, 'expenses': expenses,
                            'relations': [dict(x) for x in c.execute('SELECT * FROM relation')],
                            'categories': [dict(x) for x in c.execute('SELECT * FROM cate')]})
        else:
            self.send_json({'ok': False})
        c.close()

    def do_POST(self):
        d = json.loads(self.rfile.read(int(self.headers.get('Content-Length', 0))) or b'{}');
        c = sqlite3.connect(DB);
        c.execute('PRAGMA foreign_keys=ON');
        p = urlparse(self.path).path
        if p == '/api/bill':
            c.execute('INSERT INTO gift(name,date,amount) VALUES(?,?,?)', (d['name'], d.get('date', ''), '0'))
        elif p == '/api/person':
            c.execute('INSERT INTO income(gift_id,name,relation_id,amount,"desc") VALUES(?,?,?,?,?)',
                      (d['bill_id'], d['name'], str(d['relation_id']), str(d['amount']), d.get('note', '')))
        elif p == '/api/expense':
            c.execute('INSERT INTO ' + EXPENSE_TABLE + '(name,amount,date,relation_id,cate_id) VALUES(?,?,?,?,?)',
                      (d['name'], d['amount'], d['date'], d['relation_id'], d['cate_id']))
        elif p == '/api/manage':
            c.execute(
                'INSERT OR IGNORE INTO ' + ('relation' if d['type'] == 'relation' else 'cate') + '(name) VALUES(?)',
                (d['name'],))
        c.commit();
        c.close();
        self.send_json({'ok': True})

    def do_PUT(self):
        d = json.loads(self.rfile.read(int(self.headers.get('Content-Length', 0))) or b'{}')
        parts = urlparse(self.path).path.strip('/').split('/')
        kind, row_id = parts[1], parts[2]
        c = sqlite3.connect(DB)
        if kind == 'bill':
            c.execute('UPDATE gift SET name=?,date=? WHERE id=?', (d['name'], d['date'], row_id))
        elif kind == 'person':
            c.execute('UPDATE income SET gift_id=?,name=?,relation_id=?,amount=?,"desc"=? WHERE id=?',
                      (d['bill_id'], d['name'], str(d['relation_id']), str(d['amount']), d.get('note', ''), row_id))
        elif kind == 'expense':
            c.execute('UPDATE ' + EXPENSE_TABLE + ' SET name=?,amount=?,date=?,relation_id=?,cate_id=? WHERE id=?',
                      (d['name'], d['amount'], d['date'], d['relation_id'], d['cate_id'], row_id))
        elif kind == 'manage':
            table = 'relation' if d['type'] == 'relation' else 'cate'
            c.execute('UPDATE ' + table + ' SET name=? WHERE id=?', (d['name'], row_id))
        c.commit()
        c.close()
        self.send_json({'ok': True})

    def do_DELETE(self):
        p = urlparse(self.path).path.split('/');
        c = sqlite3.connect(DB);
        if len(p) > 3 and p[2] == 'manage':
            kind, row_id = p[3], p[4]
            if kind == 'relation':
                used = c.execute('SELECT EXISTS(SELECT 1 FROM income WHERE relation_id=? UNION ALL SELECT 1 FROM '+EXPENSE_TABLE+' WHERE relation_id=?)', (row_id,row_id)).fetchone()[0]
                table = 'relation'
            else:
                used = c.execute('SELECT EXISTS(SELECT 1 FROM '+EXPENSE_TABLE+' WHERE cate_id=?)', (row_id,)).fetchone()[0]
                table = 'cate'
            if used:
                c.close(); self.send_json({'ok':False,'error':'该项已有记录使用，暂不能删除'}); return
            c.execute('DELETE FROM '+table+' WHERE id=?', (row_id,)); c.commit(); c.close(); self.send_json({'ok':True}); return
        table = {'bill': 'gift', 'person': 'income', 'expense': EXPENSE_TABLE}.get(p[2]);
        if table == 'gift': c.execute('DELETE FROM income WHERE gift_id=?', (p[3],))
        c.execute('DELETE FROM ' + table + ' WHERE id=?', (p[3],));
        c.commit();
        c.close();
        self.send_json({'ok': True})

if __name__ == '__main__': print('礼单管理已启动: http://127.0.0.1:8765'); ThreadingHTTPServer(('127.0.0.1', 8765),
                                                                                               Handler).serve_forever()

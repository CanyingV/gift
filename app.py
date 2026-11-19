import json, sqlite3, os, zipfile, io
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, quote

# 静态资源目录与数据库路径可通过环境变量覆盖，供桌面壳 / Android 复用。
BASE = os.environ.get('GIFT_BASE_DIR') or os.path.dirname(os.path.abspath(__file__))
DB = os.environ.get('GIFT_DB_PATH') or os.path.join(BASE, 'gift')

def detect_expense_table(db_path):
    """兼容旧版 expenses 与新版 expensex 表名；数据库不存在时按 expenses 处理。"""
    if not os.path.exists(db_path):
        return 'expenses'
    try:
        con = sqlite3.connect(db_path)
        tables = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        con.close()
        return 'expensex' if 'expensex' in tables else 'expenses'
    except Exception:
        return 'expenses'

EXPENSE_TABLE = detect_expense_table(DB)

# SQLite stores dates as text and older rows are not zero-padded (2026-9-19).
# Build a normalized YYYY-MM-DD key so ORDER BY uses the real date.
def sql_date_key(col):
    rest = "substr({c},instr({c},'-')+1)".format(c=col)
    second = "instr({c},'-')+instr({r},'-')".format(c=col, r=rest)
    return ("printf('%04d-%02d-%02d',"
            "CAST(substr({c},1,instr({c},'-')-1) AS INTEGER),"
            "CAST(substr({r},1,instr({r},'-')-1) AS INTEGER),"
            "CAST(substr({c},{s}+1) AS INTEGER))").format(c=col, r=rest, s=second)

# ---------------- 轻量 xlsx 生成（仅用标准库，无需第三方依赖） ----------------
XLS_NS = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
REL_NS = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
PKG_NS = 'http://schemas.openxmlformats.org/package/2006/relationships'

def xesc(v):
    return (str(v).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            .replace('"', '&quot;').replace("'", '&apos;'))

def col_ref(n):
    s = ''
    while n:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s

def sheet_xml(rows, widths):
    out = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
           '<worksheet xmlns="' + XLS_NS + '">']
    out.append('<cols>' + ''.join(
        '<col min="{0}" max="{0}" width="{1}" customWidth="1"/>'.format(i + 1, w)
        for i, w in enumerate(widths)) + '</cols>')
    out.append('<sheetData>')
    for ri, row in enumerate(rows, 1):
        cells = []
        for ci, cell in enumerate(row, 1):
            val, kind = cell if isinstance(cell, tuple) else (cell, 's')
            val = '' if val is None else val
            ref = col_ref(ci) + str(ri)
            if kind == 'head':
                cells.append('<c r="%s" s="1" t="inlineStr"><is><t xml:space="preserve">%s</t></is></c>'
                             % (ref, xesc(val)))
            elif kind == 'money':
                cells.append('<c r="%s" s="2"><v>%s</v></c>' % (ref, val))
            elif kind == 'n':
                cells.append('<c r="%s"><v>%s</v></c>' % (ref, val))
            else:
                cells.append('<c r="%s" t="inlineStr"><is><t xml:space="preserve">%s</t></is></c>'
                             % (ref, xesc(val)))
        out.append('<row r="%d">%s</row>' % (ri, ''.join(cells)))
    out.append('</sheetData>')
    if rows:
        out.append('<autoFilter ref="A1:%s%d"/>' % (col_ref(len(widths)), len(rows)))
    out.append('</worksheet>')
    return ''.join(out)

def build_xlsx(sheets):
    """sheets: [(名称, [[(值, 类型), ...], ...], [列宽...]), ...]"""
    parts = {}
    parts['[Content_Types].xml'] = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
        + ''.join('<Override PartName="/xl/worksheets/sheet%d.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>' % (i + 1)
                  for i in range(len(sheets)))
        + '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
          '</Types>')
    parts['_rels/.rels'] = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="' + PKG_NS + '">'
        '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
        '</Relationships>')
    parts['xl/workbook.xml'] = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="' + XLS_NS + '" xmlns:r="' + REL_NS + '"><sheets>'
        + ''.join('<sheet name="%s" sheetId="%d" r:id="rId%d"/>' % (xesc(name), i + 1, i + 1)
                  for i, (name, _, _) in enumerate(sheets))
        + '</sheets></workbook>')
    parts['xl/_rels/workbook.xml.rels'] = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="' + PKG_NS + '">'
        + ''.join('<Relationship Id="rId%d" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet%d.xml"/>' % (i + 1, i + 1)
                  for i in range(len(sheets)))
        + '<Relationship Id="rId%d" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>' % (len(sheets) + 1)
        + '</Relationships>')
    parts['xl/styles.xml'] = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<styleSheet xmlns="' + XLS_NS + '">'
        '<numFmts count="1"><numFmt numFmtId="164" formatCode="&quot;¥&quot;#,##0.00"/></numFmts>'
        '<fonts count="2"><font><sz val="11"/><name val="Calibri"/></font>'
        '<font><b/><sz val="11"/><color rgb="FFFFFFFF"/><name val="Calibri"/></font></fonts>'
        '<fills count="3"><fill><patternFill patternType="none"/></fill>'
        '<fill><patternFill patternType="gray125"/></fill>'
        '<fill><patternFill patternType="solid"><fgColor rgb="FF2F7A63"/><bgColor indexed="64"/></patternFill></fill></fills>'
        '<borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>'
        '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>'
        '<cellXfs count="3">'
        '<xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>'
        '<xf numFmtId="0" fontId="1" fillId="2" borderId="0" xfId="0" applyFont="1" applyFill="1"><alignment horizontal="center" vertical="center"/></xf>'
        '<xf numFmtId="164" fontId="0" fillId="0" borderId="0" xfId="0" applyNumberFormat="1"/>'
        '</cellXfs><cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles></styleSheet>')
    for i, (_, rows, widths) in enumerate(sheets):
        parts['xl/worksheets/sheet%d.xml' % (i + 1)] = sheet_xml(rows, widths)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as z:
        for name, content in parts.items():
            z.writestr(name, content)
    return buf.getvalue()

def head(*labels):
    return [(x, 'head') for x in labels]

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=BASE, **kw)

    def send_json(self, data):
        b = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(200)
        self.send_header('Content-Type', 'application/json charset=utf-8')
        self.send_header('Content-Length', str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def send_xlsx(self, content, filename):
        self.send_response(200)
        self.send_header('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        self.send_header('Content-Disposition',
                         "attachment; filename=export.xlsx; filename*=UTF-8''" + quote(filename))
        self.send_header('Content-Length', str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def do_GET(self):
        p = urlparse(self.path).path
        if not p.startswith('/api/'): return super().do_GET()
        c = sqlite3.connect(DB)
        c.row_factory = sqlite3.Row
        if p == '/api/data':
            bills = [dict(x) for x in c.execute(
                'SELECT g.id,g.name,g.date,count(i.id) people,coalesce(sum(CAST(i.amount AS REAL)),0) amount FROM gift g LEFT JOIN income i ON i.gift_id=g.id GROUP BY g.id ORDER BY '
                + sql_date_key('g.date') + ' DESC,g.id DESC')]
            people = [dict(x) for x in c.execute(
                'SELECT i.id,i.gift_id AS bill_id,i.name,CAST(i.relation_id AS INTEGER) relation_id,CAST(i.amount AS REAL) amount,i."desc" AS note,g.name bill,r.name relation FROM income i LEFT JOIN gift g ON g.id=i.gift_id LEFT JOIN relation r ON r.id=CAST(i.relation_id AS INTEGER) ORDER BY i.id DESC')]
            expenses = [dict(x) for x in c.execute(
                'SELECT e.*,r.name relation,ca.name category FROM ' + EXPENSE_TABLE + ' e LEFT JOIN relation r ON r.id=e.relation_id LEFT JOIN cate ca ON ca.id=e.cate_id ORDER BY '
                + sql_date_key('e.date') + ' DESC,e.id DESC')]
            self.send_json({'bills': bills, 'people': people, 'expenses': expenses,
                            'relations': [dict(x) for x in c.execute('SELECT * FROM relation')],
                            'categories': [dict(x) for x in c.execute('SELECT * FROM cate')]})
        elif p == '/api/export/bills':
            bills = [dict(x) for x in c.execute(
                'SELECT g.id,g.name,g.date,count(i.id) people,coalesce(sum(CAST(i.amount AS REAL)),0) amount FROM gift g LEFT JOIN income i ON i.gift_id=g.id GROUP BY g.id ORDER BY '
                + sql_date_key('g.date') + ' DESC,g.id DESC')]
            people = [dict(x) for x in c.execute(
                'SELECT g.name bill,g.date,i.name,r.name relation,CAST(i.amount AS REAL) amount,i."desc" note FROM income i LEFT JOIN gift g ON g.id=i.gift_id LEFT JOIN relation r ON r.id=CAST(i.relation_id AS INTEGER) ORDER BY '
                + sql_date_key('g.date') + ' DESC,g.id DESC,i.id')]
            summary = [head('礼单名称', '日期', '人数', '礼金合计')]
            for b in bills:
                summary.append([b['name'], b['date'], b['people'], (b['amount'], 'money')])
            detail = [head('礼单', '日期', '来客', '关系', '金额', '备注')]
            for x in people:
                detail.append([x['bill'], x['date'], x['name'], x['relation'] or '',
                               (x['amount'], 'money'), x['note'] or ''])
            self.send_xlsx(build_xlsx([('礼单汇总', summary, [28, 16, 10, 16]),
                                       ('礼单明细', detail, [28, 16, 14, 14, 16, 30])]), '礼单.xlsx')
        elif p == '/api/export/expenses':
            rows = [dict(x) for x in c.execute(
                'SELECT e.name,e.date,ca.name category,r.name relation,CAST(e.amount AS REAL) amount FROM '
                + EXPENSE_TABLE + ' e LEFT JOIN relation r ON r.id=e.relation_id LEFT JOIN cate ca ON ca.id=e.cate_id ORDER BY '
                + sql_date_key('e.date') + ' DESC,e.id DESC')]
            out = [head('姓名', '日期', '分类', '关系', '金额')]
            for x in rows:
                out.append([x['name'], x['date'], x['category'] or '', x['relation'] or '',
                            (x['amount'], 'money')])
            self.send_xlsx(build_xlsx([('随礼记录', out, [20, 16, 16, 16, 16])]), '随礼.xlsx')
        else:
            self.send_json({'ok': False})
        c.close()

    def do_POST(self):
        d = json.loads(self.rfile.read(int(self.headers.get('Content-Length', 0))) or b'{}')
        c = sqlite3.connect(DB)
        c.execute('PRAGMA foreign_keys=ON')
        p = urlparse(self.path).path
        if p == '/api/bill':
            c.execute('INSERT INTO gift(name,date) VALUES(?,?)', (d['name'], d.get('date', '')))
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
        c.commit()
        c.close()
        self.send_json({'ok': True})

    def do_PUT(self):
        d = json.loads(self.rfile.read(int(self.headers.get('Content-Length', 0))) or b'{}')
        parts = [x for x in urlparse(self.path).path.split('/') if x]
        kind = parts[1] if len(parts) > 1 else ''
        if kind == 'manage' and len(parts) > 3:
            table = 'relation' if parts[2] == 'relation' else 'cate'
            row_id = parts[3]
        else:
            row_id = parts[2] if len(parts) > 2 else ''
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
            c.execute('UPDATE ' + table + ' SET name=? WHERE id=?', (d['name'], row_id))
        c.commit()
        c.close()
        self.send_json({'ok': True})

    def do_DELETE(self):
        p = urlparse(self.path).path.split('/')
        c = sqlite3.connect(DB)
        if len(p) > 3 and p[2] == 'manage':
            kind, row_id = p[3], p[4]
            if kind == 'relation':
                used = c.execute(
                    'SELECT EXISTS(SELECT 1 FROM income WHERE relation_id=? UNION ALL SELECT 1 FROM ' + EXPENSE_TABLE + ' WHERE relation_id=?)',
                    (row_id, row_id)).fetchone()[0]
                table = 'relation'
            else:
                used = \
                    c.execute('SELECT EXISTS(SELECT 1 FROM ' + EXPENSE_TABLE + ' WHERE cate_id=?)',
                              (row_id,)).fetchone()[0]
                table = 'cate'
            if used:
                c.close()
                self.send_json({'ok': False, 'error': '该项已有记录使用，暂不能删除'})
                return
            c.execute('DELETE FROM ' + table + ' WHERE id=?', (row_id,))
            c.commit()
            c.close()
            self.send_json({'ok': True})
            return
        table = {'bill': 'gift', 'person': 'income', 'expense': EXPENSE_TABLE}.get(p[2])
        if table == 'gift': c.execute('DELETE FROM income WHERE gift_id=?', (p[3],))
        c.execute('DELETE FROM ' + table + ' WHERE id=?', (p[3],))
        c.commit()
        c.close()
        self.send_json({'ok': True})

def run_server(host='127.0.0.1', port=8765):
    print('礼单管理已启动: http://%s:%d' % (host, port))
    ThreadingHTTPServer((host, port), Handler).serve_forever()

if __name__ == '__main__':
    run_server()

import json, sqlite3, os, zipfile, io
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, quote

# 静态资源目录与数据库路径可通过环境变量覆盖，供桌面壳 / Android 复用。
BASE = os.environ.get('GIFT_BASE_DIR') or os.path.dirname(os.path.abspath(__file__))
DB = os.environ.get('GIFT_DB_PATH') or os.path.join(BASE, 'gift')

# 礼单详情表固定为 expenses。
EXPENSE_TABLE = 'expenses'

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


# ---------------- 轻量 xlsx 解析（标准库，兼容 inlineStr / sharedStrings） ----------------
import re
from xml.etree import ElementTree as ET

XLS_M = '{' + XLS_NS + '}'
XLS_R = '{' + REL_NS + '}'
XLS_P = '{' + PKG_NS + '}'


def parse_xlsx(data):
    """把 xlsx 字节解析为 {sheet名: [[单元格文本, ...], ...]}。"""
    z = zipfile.ZipFile(io.BytesIO(data))
    try:
        shared = []
        if 'xl/sharedStrings.xml' in z.namelist():
            root = ET.fromstring(z.read('xl/sharedStrings.xml'))
            for si in root.findall(XLS_M + 'si'):
                shared.append(''.join(t.text or '' for t in si.iter(XLS_M + 't')))
        wb = ET.fromstring(z.read('xl/workbook.xml'))
        rels = ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))
        rel_map = {r.get('Id'): r.get('Target') for r in rels.findall(XLS_P + 'Relationship')}
        sheets = []
        for sh in wb.findall(XLS_M + 'sheets/' + XLS_M + 'sheet'):
            target = (rel_map.get(sh.get(XLS_R + 'id'), '') or '').lstrip('/')
            if not target.startswith('xl/'):
                target = 'xl/' + target
            sheets.append((sh.get('name') or '', target))

        def col_index(ref):
            m = re.match(r'([A-Za-z]+)', ref or '')
            if not m:
                return 0
            n = 0
            for ch in m.group(1).upper():
                n = n * 26 + (ord(ch) - 64)
            return n - 1

        out = {}
        for name, path in sheets:
            if path not in z.namelist():
                continue
            root = ET.fromstring(z.read(path))
            rows = []
            for row in root.findall(XLS_M + 'sheetData/' + XLS_M + 'row'):
                cells = {}
                for c in row.findall(XLS_M + 'c'):
                    ci = col_index(c.get('r'))
                    typ = c.get('t')
                    if typ == 'inlineStr':
                        node = c.find(XLS_M + 'is')
                        val = ''.join(x.text or '' for x in node.iter(XLS_M + 't')) if node is not None else ''
                    else:
                        node = c.find(XLS_M + 'v')
                        val = node.text or '' if node is not None else ''
                        if typ == 's':
                            try:
                                val = shared[int(val)]
                            except (ValueError, IndexError):
                                val = ''
                    cells[ci] = val
                if cells:
                    rows.append([cells.get(i, '') for i in range(max(cells) + 1)])
            out[name] = rows
        return out
    finally:
        z.close()


def norm_money(v):
    try:
        return float(str(v).strip().replace(',', '').replace('¥', '').replace('￥', '') or 0)
    except (ValueError, TypeError):
        return 0.0


def norm_date(v):
    """把 2026/11/11、2026.11.11、2026年11月11日 等统一成 2026-11-11。"""
    s = str(v or '').strip()
    if not s:
        return ''
    m = re.match(r'^(\d{4})\s*[/\-.年]\s*(\d{1,2})\s*[/\-.月]\s*(\d{1,2})\s*日?$', s)
    if m:
        y, mo, d = m.groups()
        return '%04d-%02d-%02d' % (int(y), int(mo), int(d))
    return s


def find_header(rows, keys):
    """在前若干行里找同时包含 keys 的表头，返回 (行号, {列名: 列号})。
    cols 收集该行所有非空表头，便于按列名读取任意列（分类/关系/备注等），
    keys 只用来判定哪一行是表头。"""
    for i, row in enumerate(rows[:12]):
        cols = {}
        for j, cell in enumerate(row):
            name = str(cell).strip()
            if name and name not in cols:
                cols[name] = j
        if all(k in cols for k in keys):
            return i, cols
    return -1, {}


def get_or_create(c, table, name, counter):
    """按名称查/建关系或分类，返回 id。"""
    name = str(name).strip()
    if not name:
        return 0
    row = c.execute('SELECT id FROM ' + table + ' WHERE name=?', (name,)).fetchone()
    if row:
        return row[0]
    cur = c.execute('INSERT INTO ' + table + '(name) VALUES(?)', (name,))
    counter[0] += 1
    return cur.lastrowid


def import_bill_rows(data, c):
    """导入礼单 Excel（礼单汇总 + 礼单明细），按自然键去重。"""
    sheets = parse_xlsx(data)
    summary = detail = None
    for name, rows in sheets.items():
        if '汇总' in name:
            summary = rows
        elif '明细' in name:
            detail = rows
    if summary is None and detail is None and sheets:
        rows = list(sheets.values())
        summary = rows[0]
        detail = rows[1] if len(rows) > 1 else None

    stat = {'bills': 0, 'people': 0, 'relations': 0, 'skipped': 0}
    rel_created = [0]

    if summary:
        hi, cols = find_header(summary, ['礼单名称', '日期'])
        if hi >= 0:
            for row in summary[hi + 1:]:
                def cell(key, default=''):
                    j = cols.get(key)
                    return str(row[j]).strip() if j is not None and j < len(row) else default
                name = cell('礼单名称')
                if not name or name.startswith('示例'):
                    continue
                date = norm_date(cell('日期'))
                if c.execute('SELECT 1 FROM gift WHERE name=?', (name,)).fetchone():
                    stat['skipped'] += 1
                    continue
                c.execute('INSERT INTO gift(name,date) VALUES(?,?)', (name, date))
                stat['bills'] += 1

    if detail:
        hi, cols = find_header(detail, ['礼单', '来客', '关系', '金额'])
        if hi >= 0:
            for row in detail[hi + 1:]:
                def cell(key, default=''):
                    j = cols.get(key)
                    return str(row[j]).strip() if j is not None and j < len(row) else default
                bill_name, guest = cell('礼单'), cell('来客')
                if not bill_name or not guest or guest.startswith('示例'):
                    continue
                date = norm_date(cell('日期'))
                bill = c.execute('SELECT id FROM gift WHERE name=?', (bill_name,)).fetchone()
                if bill:
                    bid = bill[0]
                else:
                    cur = c.execute('INSERT INTO gift(name,date) VALUES(?,?)', (bill_name, date))
                    bid = cur.lastrowid
                    stat['bills'] += 1
                rid = get_or_create(c, 'relation', cell('关系'), rel_created)
                amount = norm_money(cell('金额'))
                note = cell('备注')
                dup = c.execute(
                    'SELECT 1 FROM income WHERE gift_id=? AND name=? AND relation_id=? '
                    'AND CAST(amount AS REAL)=? AND coalesce("desc",\'\')=?',
                    (bid, guest, str(rid), amount, note)).fetchone()
                if dup:
                    stat['skipped'] += 1
                    continue
                c.execute('INSERT INTO income(gift_id,name,relation_id,amount,"desc") VALUES(?,?,?,?,?)',
                          (bid, guest, str(rid), str(amount), note))
                stat['people'] += 1
    stat['relations'] = rel_created[0]
    return stat


def import_expense_rows(data, c):
    """导入随礼 Excel（随礼记录），按自然键去重。"""
    sheets = parse_xlsx(data)
    rows = None
    for name, sheet in sheets.items():
        if '随礼' in name:
            rows = sheet
            break
    if rows is None and sheets:
        rows = list(sheets.values())[0]
    stat = {'expenses': 0, 'relations': 0, 'categories': 0, 'skipped': 0}
    rel_created, cate_created = [0], [0]
    hi, cols = find_header(rows or [], ['姓名', '日期', '金额'])
    if hi < 0:
        return stat
    for row in rows[hi + 1:]:
        def cell(key, default=''):
            j = cols.get(key)
            return str(row[j]).strip() if j is not None and j < len(row) else default
        name = cell('姓名')
        if not name or name.startswith('示例'):
            continue
        date = norm_date(cell('日期'))
        amount = norm_money(cell('金额'))
        rid = get_or_create(c, 'relation', cell('关系'), rel_created)
        cid = get_or_create(c, 'cate', cell('分类'), cate_created)
        dup = c.execute(
            'SELECT 1 FROM ' + EXPENSE_TABLE +
            ' WHERE name=? AND date=? AND CAST(amount AS REAL)=? AND relation_id=? AND cate_id=?',
            (name, date, amount, rid, cid)).fetchone()
        if dup:
            stat['skipped'] += 1
            continue
        c.execute('INSERT INTO ' + EXPENSE_TABLE +
                  '(name,amount,date,relation_id,cate_id) VALUES(?,?,?,?,?)',
                  (name, amount, date, rid, cid))
        stat['expenses'] += 1
    stat['relations'] = rel_created[0]
    stat['categories'] = cate_created[0]
    return stat


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
        elif p == '/api/template/bills':
            summary = [head('礼单名称', '日期', '人数', '礼金合计'),
                       ['示例：张三乔迁', '2026-01-01', '', '']]
            detail = [head('礼单', '日期', '来客', '关系', '金额', '备注'),
                      ['示例：张三乔迁', '2026-01-01', '李四', '朋友', (200, 'money'), '示例行，可删除']]
            self.send_xlsx(build_xlsx([('礼单汇总', summary, [28, 16, 10, 16]),
                                       ('礼单明细', detail, [28, 16, 14, 14, 16, 30])]), '礼单模板.xlsx')
        elif p == '/api/template/expenses':
            out = [head('姓名', '日期', '分类', '关系', '金额'),
                   ['王五', '2026-01-01', '结婚', '朋友', (300, 'money')]]
            self.send_xlsx(build_xlsx([('随礼记录', out, [20, 16, 16, 16, 16])]), '随礼模板.xlsx')
        else:
            self.send_json({'ok': False})
        c.close()

    def do_POST(self):
        import base64
        d = json.loads(self.rfile.read(int(self.headers.get('Content-Length', 0))) or b'{}')
        c = sqlite3.connect(DB)
        c.execute('PRAGMA foreign_keys=ON')
        p = urlparse(self.path).path
        if p in ('/api/import/bills', '/api/import/expenses'):
            try:
                raw = base64.b64decode(d.get('data', ''))
                if not raw:
                    raise ValueError('文件为空')
                stat = (import_bill_rows(raw, c) if p == '/api/import/bills'
                        else import_expense_rows(raw, c))
                c.commit()
                self.send_json({'ok': True, 'stat': stat})
            except Exception as e:
                c.rollback()
                self.send_json({'ok': False, 'error': '导入失败：' + str(e)})
            finally:
                c.close()
            return
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

"""轻量 xlsx 生成与解析（仅用标准库，无需第三方依赖）。

生成侧直接拼 OOXML 部件并用 zipfile 打包；解析侧兼容 inlineStr 与 sharedStrings。
"""
import io
import re
import zipfile
from xml.etree import ElementTree as ET

XLS_NS = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
REL_NS = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
PKG_NS = 'http://schemas.openxmlformats.org/package/2006/relationships'
XLS_M = '{' + XLS_NS + '}'
XLS_R = '{' + REL_NS + '}'
XLS_P = '{' + PKG_NS + '}'


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
    """在前若干行里找同时包含 keys 的表头，返回 (行号, {列名: 列号})。"""
    for i, row in enumerate(rows[:12]):
        cols = {}
        for j, cell in enumerate(row):
            name = str(cell).strip()
            if name and name not in cols:
                cols[name] = j
        if all(k in cols for k in keys):
            return i, cols
    return -1, {}

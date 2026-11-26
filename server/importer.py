"""Excel 导入业务逻辑：按自然键去重，全部通过 ORM 写入。"""
from . import repository as repo
from .models import db
from .xlsx import find_header, norm_date, norm_money, parse_xlsx


def import_bill_rows(data):
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

    def cell(cols, row, key, default=''):
        j = cols.get(key)
        return str(row[j]).strip() if j is not None and j < len(row) else default

    with db.atomic():
        if summary:
            hi, cols = find_header(summary, ['礼单名称', '日期'])
            if hi >= 0:
                for row in summary[hi + 1:]:
                    name = cell(cols, row, '礼单名称')
                    if not name or name.startswith('示例'):
                        continue
                    if repo.bill_exists(name):
                        stat['skipped'] += 1
                        continue
                    repo.create_bill(name, norm_date(cell(cols, row, '日期')))
                    stat['bills'] += 1

        if detail:
            hi, cols = find_header(detail, ['礼单', '来客', '关系', '金额'])
            if hi >= 0:
                for row in detail[hi + 1:]:
                    bill_name, guest = cell(cols, row, '礼单'), cell(cols, row, '来客')
                    if not bill_name or not guest or guest.startswith('示例'):
                        continue
                    bid = repo.find_bill_by_name(bill_name)
                    if bid is None:
                        bid = repo.create_bill(bill_name, norm_date(cell(cols, row, '日期')))
                        stat['bills'] += 1
                    rid, created = repo.get_or_create_manage('relation', cell(cols, row, '关系'))
                    if created:
                        stat['relations'] += 1
                    amount = norm_money(cell(cols, row, '金额'))
                    note = cell(cols, row, '备注')
                    if repo.income_exists(bid, guest, rid, amount, note):
                        stat['skipped'] += 1
                        continue
                    repo.create_person(bid, guest, rid, amount, note)
                    stat['people'] += 1
    return stat


def import_expense_rows(data):
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
    hi, cols = find_header(rows or [], ['姓名', '日期', '金额'])
    if hi < 0:
        return stat

    def cell(key, default=''):
        j = cols.get(key)
        return str(row[j]).strip() if j is not None and j < len(row) else default

    with db.atomic():
        for row in rows[hi + 1:]:
            name = cell('姓名')
            if not name or name.startswith('示例'):
                continue
            date = norm_date(cell('日期'))
            amount = norm_money(cell('金额'))
            rid, rel_created = repo.get_or_create_manage('relation', cell('关系'))
            cid, cate_created = repo.get_or_create_manage('category', cell('分类'))
            stat['relations'] += int(rel_created)
            stat['categories'] += int(cate_created)
            if repo.expense_exists(name, date, amount, rid, cid):
                stat['skipped'] += 1
                continue
            repo.create_expense(name, amount, date, rid, cid)
            stat['expenses'] += 1
    return stat

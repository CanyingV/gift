"""数据访问层：全部通过 ORM 完成增删改查，聚合与排序在 Python 端进行。

旧的 sqlite3 版本用 printf/substr 拼出日期排序键，是因为历史数据里的日期
没有补零（2026-9-19）。这里统一用 date_key() 做归一化，行为完全一致。
"""
from peewee import fn

from .models import Category, Expense, Gift, Income, Relation, db


def date_key(value):
    """把 YYYY-M-D 等历史日期转成可比较的 (年, 月, 日)。"""
    parts = str(value or '').split('-')
    try:
        year = int(parts[0]) if parts else 0
        month = int(parts[1]) if len(parts) > 1 else 0
        day = int(parts[2]) if len(parts) > 2 else 0
    except (ValueError, IndexError):
        return (0, 0, 0)
    return (year, month, day)


def _num(value):
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def get_relations():
    return [dict(x) for x in Relation.select().order_by(Relation.id).dicts()]


def get_categories():
    return [dict(x) for x in Category.select().order_by(Category.id).dicts()]


def get_bills():
    """礼单列表：人数与礼金合计在 Python 端按 gift_id 聚合。"""
    totals = {}
    for inc in Income.select().dicts():
        key = inc['gift']
        item = totals.setdefault(key, {'people': 0, 'amount': 0.0})
        item['people'] += 1
        item['amount'] += _num(inc['amount'])
    rows = []
    for gift in Gift.select().dicts():
        stat = totals.get(gift['id'], {'people': 0, 'amount': 0.0})
        rows.append({
            'id': gift['id'], 'name': gift['name'] or '', 'date': gift['date'] or '',
            'people': stat['people'], 'amount': stat['amount'],
        })
    rows.sort(key=lambda x: (date_key(x['date']), x['id']), reverse=True)
    return rows


def _income_rows(rows):
    """把 ORM 的收礼明细(dicts)补齐礼单/关系名称，供列表与详情页共用。"""
    bills = {x['id']: x['name'] or '' for x in Gift.select().dicts()}
    rels = {x['id']: x['name'] or '' for x in Relation.select().dicts()}
    return [{
        'id': x['id'], 'gift_id': x['gift'], 'bill_id': x['gift'],
        'name': x['name'] or '', 'relation_id': x['relation'] or 0,
        'amount': _num(x['amount']), 'note': x['note'] or '',
        'bill': bills.get(x['gift'], ''), 'relation': rels.get(x['relation'], ''),
    } for x in rows]


def get_people():
    """收礼明细：附带礼单名称与关系名称。"""
    rows = _income_rows(Income.select().dicts())
    rows.sort(key=lambda x: x['id'], reverse=True)
    return rows



def get_expenses():
    """随礼记录：附带关系与分类名称。"""
    rels = {x['id']: x['name'] or '' for x in Relation.select().dicts()}
    cats = {x['id']: x['name'] or '' for x in Category.select().dicts()}
    rows = [{
        'id': x['id'], 'name': x['name'] or '', 'amount': _num(x['amount']),
        'date': x['date'] or '', 'relation_id': x['relation'] or 0,
        'cate_id': x['category'] or 0,
        'relation': rels.get(x['relation'], ''), 'category': cats.get(x['category'], ''),
    } for x in Expense.select().dicts()]
    rows.sort(key=lambda x: (date_key(x['date']), x['id']), reverse=True)
    return rows


def _sum_amount(model):
    row = model.select(fn.COALESCE(fn.SUM(model.amount.cast('REAL')), 0).alias('total')).dicts().first()
    return _num(row['total'] if row else 0)


def _sum_by(model, key):
    """按字段分组求和；金额在数据库侧用 REAL 聚合，避免历史 TEXT 排序问题。"""
    name = getattr(key, 'name', key)
    rows = model.select(key, fn.SUM(model.amount.cast('REAL')).alias('total')).group_by(key).dicts()
    return {row[name]: _num(row['total']) for row in rows}


def get_dashboard_page():
    """总览页：汇总数字 + 最近 5 条礼单/随礼，不返回全部明细。"""
    bills = get_bills()
    income, out = _sum_amount(Income), _sum_amount(Expense)
    return {
        'summary': {
            'income': income, 'people': Income.select().count(),
            'out': out, 'expenseCount': Expense.select().count(),
            'billCount': len(bills),
            'latestBillDate': bills[0]['date'] if bills else '',
            'net': income - out,
        },
        'bills': bills[:5], 'expenses': get_expenses()[:5],
        'relations': get_relations(), 'categories': get_categories(),
    }


def get_bills_page():
    """礼单列表页：只要礼单汇总，关系供新建人员表单使用。"""
    return {'bills': get_bills(), 'relations': get_relations()}


def bill_id_exists(bill_id):
    return Gift.select().where(Gift.id == bill_id).exists()


def get_people_by_bill(bill_id):
    """某个礼单下的人员明细；礼单不存在返回 None。"""
    if not bill_id_exists(bill_id):
        return None
    people = _income_rows(Income.select().where(Income.gift == bill_id).dicts())
    people.sort(key=lambda x: x['id'], reverse=True)
    return people


def get_person(row_id):
    rows = _income_rows(Income.select().where(Income.id == row_id).dicts())
    return rows[0] if rows else None


def get_expense(row_id):
    rows = [x for x in get_expenses() if x['id'] == row_id]
    return rows[0] if rows else None


def get_bill_page(bill_id):
    """礼单详情页：单个礼单 + 该礼单的人员，不加载其他礼单的明细。"""
    gift = Gift.select().where(Gift.id == bill_id).first()
    if not gift:
        return None
    return {
        'bill': {'id': gift.id, 'name': gift.name or '', 'date': gift.date or ''},
        'people': get_people_by_bill(bill_id), 'relations': get_relations(),
        'billOptions': [{'id': x['id'], 'name': x['name'] or ''} for x in Gift.select().dicts()],
    }


def get_expenses_page():
    """随礼页：随礼记录 + 筛选项所需的关系和分类。"""
    return {
        'expenses': get_expenses(),
        'relations': get_relations(), 'categories': get_categories(),
    }


def get_stats_page():
    """统计页：按关系/分类在数据库侧聚合，不把明细发给前端。"""
    relations, categories = get_relations(), get_categories()
    income = _sum_by(Income, Income.relation)
    out_rel = _sum_by(Expense, Expense.relation)
    out_cate = _sum_by(Expense, Expense.category)
    total_in, total_out = _sum_amount(Income), _sum_amount(Expense)
    return {
        'summary': {'income': total_in, 'out': total_out, 'net': total_in - total_out},
        'incomeByRelation': [[r['name'], income.get(r['id'], 0)] for r in relations],
        'outByRelation': [[r['name'], out_rel.get(r['id'], 0)] for r in relations],
        'outByCategory': [[c['name'], out_cate.get(c['id'], 0)] for c in categories],
        'relations': relations, 'categories': categories,
    }


def get_people_for_export():
    """导出用的收礼明细：按礼单日期倒序、礼单 id 倒序、明细 id 升序。"""
    bills = get_bills()  # 已按日期倒序、id 倒序排好
    rank = {b['id']: i for i, b in enumerate(bills)}
    by_id = {b['id']: b for b in bills}
    rows = get_people()
    for row in rows:
        bill = by_id.get(row['bill_id'])
        row['date'] = bill['date'] if bill else ''
        row['_rank'] = rank.get(row['bill_id'], len(bills))
    rows.sort(key=lambda x: (x['_rank'], x['id']))
    for row in rows:
        row.pop('_rank', None)
    return rows


def create_bill(name, date=''):
    return Gift.create(name=name, date=date).id


def update_bill(row_id, name, date):
    return Gift.update(name=name, date=date).where(Gift.id == row_id).execute()


def delete_bill(row_id):
    with db.atomic():
        Income.delete().where(Income.gift == row_id).execute()
        return Gift.delete().where(Gift.id == row_id).execute()


def create_person(bill_id, name, relation_id, amount, note=''):
    return Income.create(gift=bill_id, name=name, relation=relation_id or None,
                         amount=str(amount), note=note).id


def update_person(row_id, bill_id, name, relation_id, amount, note=''):
    return Income.update(gift=bill_id, name=name, relation=relation_id or None,
                         amount=str(amount), note=note).where(Income.id == row_id).execute()


def delete_person(row_id):
    return Income.delete().where(Income.id == row_id).execute()


def create_expense(name, amount, date, relation_id, cate_id):
    return Expense.create(name=name, amount=str(amount), date=date,
                          relation=relation_id or None, category=cate_id or None).id


def update_expense(row_id, name, amount, date, relation_id, cate_id):
    return Expense.update(name=name, amount=str(amount), date=date,
                          relation=relation_id or None,
                          category=cate_id or None).where(Expense.id == row_id).execute()


def delete_expense(row_id):
    return Expense.delete().where(Expense.id == row_id).execute()


def manage_model(kind):
    return Relation if kind == 'relation' else Category


def add_manage(kind, name):
    model = manage_model(kind)
    obj, _ = model.get_or_create(name=name)
    return obj.id


def update_manage(kind, row_id, name):
    model = manage_model(kind)
    return model.update(name=name).where(model.id == row_id).execute()


def manage_in_use(kind, row_id):
    if kind == 'relation':
        return (Income.select().where(Income.relation == row_id).exists()
                or Expense.select().where(Expense.relation == row_id).exists())
    return Expense.select().where(Expense.category == row_id).exists()


def delete_manage(kind, row_id):
    model = manage_model(kind)
    return model.delete().where(model.id == row_id).execute()


def bill_exists(name):
    return Gift.select().where(Gift.name == name).exists()


def find_bill_by_name(name):
    row = Gift.select().where(Gift.name == name).first()
    return row.id if row else None


def get_or_create_manage(kind, name):
    """返回 (id, 是否新建)；空名称返回 (0, False)。"""
    name = str(name or '').strip()
    if not name:
        return 0, False
    obj, created = manage_model(kind).get_or_create(name=name)
    return obj.id, created


def income_exists(bill_id, name, relation_id, amount, note):
    return Income.select().where(
        (Income.gift == bill_id) & (Income.name == name)
        & (Income.relation == (relation_id or None))
        & (Income.amount.cast('REAL') == float(amount))
        & (Income.note == (note or ''))
    ).exists()


def expense_exists(name, date, amount, relation_id, cate_id):
    return Expense.select().where(
        (Expense.name == name) & (Expense.date == date)
        & (Expense.amount.cast('REAL') == float(amount))
        & (Expense.relation == (relation_id or None))
        & (Expense.category == (cate_id or None))
    ).exists()

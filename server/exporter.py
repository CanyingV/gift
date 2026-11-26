"""Excel 导出与模板下载：数据来自 ORM 仓储层。"""
from . import repository as repo
from .xlsx import build_xlsx, head


def export_bills():
    summary = [head('礼单名称', '日期', '人数', '礼金合计')]
    for bill in repo.get_bills():
        summary.append([bill['name'], bill['date'], bill['people'], (bill['amount'], 'money')])

    detail = [head('礼单', '日期', '来客', '关系', '金额', '备注')]
    for person in repo.get_people_for_export():
        detail.append([person['bill'], person['date'], person['name'],
                       person['relation'] or '', (person['amount'], 'money'), person['note'] or ''])

    return build_xlsx([('礼单汇总', summary, [28, 16, 10, 16]),
                       ('礼单明细', detail, [28, 16, 14, 14, 16, 30])])


def export_expenses():
    rows = [head('姓名', '日期', '分类', '关系', '金额')]
    for item in repo.get_expenses():
        rows.append([item['name'], item['date'], item['category'] or '',
                     item['relation'] or '', (item['amount'], 'money')])
    return build_xlsx([('随礼记录', rows, [20, 16, 16, 16, 16])])


def template_bills():
    summary = [head('礼单名称', '日期', '人数', '礼金合计'),
               ['示例：张三乔迁', '2026-01-01', '', '']]
    detail = [head('礼单', '日期', '来客', '关系', '金额', '备注'),
              ['示例：张三乔迁', '2026-01-01', '李四', '朋友', (200, 'money'), '示例行，可删除']]
    return build_xlsx([('礼单汇总', summary, [28, 16, 10, 16]),
                       ('礼单明细', detail, [28, 16, 14, 14, 16, 30])])


def template_expenses():
    rows = [head('姓名', '日期', '分类', '关系', '金额'),
            ['王五', '2026-01-01', '结婚', '朋友', (300, 'money')]]
    return build_xlsx([('随礼记录', rows, [20, 16, 16, 16, 16])])

"""集中式 RESTful 路由表。

所有接口在本文件按模块定义：页面聚合、礼单、收礼人员、随礼、关系/分类、
导入导出模板。handler.py 只负责通用分发与静态资源，不再写 if/elif 路由。
"""
import base64
import json
import re
from collections import namedtuple
from urllib.parse import quote

from . import exporter, importer, repository as repo


# ---------- 响应工具 ----------
class Response:
    def __init__(self, body=b'', status=200, headers=None):
        self.body = body
        self.status = status
        self.headers = headers or {}


def json_response(data, status=200):
    body = json.dumps(data, ensure_ascii=False).encode()
    return Response(body, status, {'Content-Type': 'application/json; charset=utf-8'})


def xlsx_response(content, filename):
    return Response(content, 200, {
        'Content-Type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'Content-Disposition': "attachment; filename=export.xlsx; filename*=UTF-8''" + quote(filename)
    })


def error(message, status=400):
    return json_response({'ok': False, 'error': message}, status)


def _name(body):
    return str(body.get('name', '') or '').strip()


# ---------- 页面聚合资源 ----------
def dashboard(params, body, query):
    return json_response(repo.get_dashboard_page())


def stats(params, body, query):
    return json_response(repo.get_stats_page())


# ---------- 礼单 /api/bills ----------
def list_bills(params, body, query):
    return json_response(repo.get_bills_page())


def create_bill(params, body, query):
    name = _name(body)
    if not name:
        return error('礼单名称不能为空')
    row_id = repo.create_bill(name, body.get('date', ''))
    return json_response({'ok': True, 'id': row_id}, 201)


def get_bill(params, body, query):
    page = repo.get_bill_page(params['id'])
    return json_response(page) if page is not None else error('礼单不存在', 404)


def update_bill(params, body, query):
    name = _name(body)
    if not name:
        return error('礼单名称不能为空')
    if not repo.bill_id_exists(params['id']):
        return error('礼单不存在', 404)
    repo.update_bill(params['id'], name, body.get('date', ''))
    return json_response({'ok': True})


def delete_bill(params, body, query):
    if not repo.bill_id_exists(params['id']):
        return error('礼单不存在', 404)
    repo.delete_bill(params['id'])
    return json_response({'ok': True})


# ---------- 收礼人员 /api/bills/{id}/people、/api/people/{id} ----------
def list_people(params, body, query):
    people = repo.get_people_by_bill(params['id'])
    return json_response({'people': people}) if people is not None else error('礼单不存在', 404)


def create_person(params, body, query):
    if not repo.bill_id_exists(params['id']):
        return error('礼单不存在', 404)
    name = _name(body)
    if not name:
        return error('姓名不能为空')
    row_id = repo.create_person(params['id'], name, body.get('relation_id', 0),
                                body.get('amount', 0), body.get('note', ''))
    return json_response({'ok': True, 'id': row_id}, 201)


def get_person(params, body, query):
    person = repo.get_person(params['id'])
    return json_response(person) if person is not None else error('记录不存在', 404)


def update_person(params, body, query):
    if repo.get_person(params['id']) is None:
        return error('记录不存在', 404)
    repo.update_person(params['id'], body.get('bill_id', 0), _name(body),
                       body.get('relation_id', 0), body.get('amount', 0), body.get('note', ''))
    return json_response({'ok': True})


def delete_person(params, body, query):
    repo.delete_person(params['id'])
    return json_response({'ok': True})


# ---------- 随礼 /api/expenses ----------
def list_expenses(params, body, query):
    return json_response(repo.get_expenses_page())


def create_expense(params, body, query):
    name = _name(body)
    if not name:
        return error('姓名不能为空')
    row_id = repo.create_expense(name, body.get('amount', 0), body.get('date', ''),
                                 body.get('relation_id', 0), body.get('cate_id', 0))
    return json_response({'ok': True, 'id': row_id}, 201)


def get_expense(params, body, query):
    row = repo.get_expense(params['id'])
    return json_response(row) if row is not None else error('记录不存在', 404)


def update_expense(params, body, query):
    if repo.get_expense(params['id']) is None:
        return error('记录不存在', 404)
    repo.update_expense(params['id'], _name(body), body.get('amount', 0), body.get('date', ''),
                        body.get('relation_id', 0), body.get('cate_id', 0))
    return json_response({'ok': True})


def delete_expense(params, body, query):
    repo.delete_expense(params['id'])
    return json_response({'ok': True})


# ---------- 关系 /api/relations 与分类 /api/categories ----------
def _manage_rows(kind):
    return repo.get_relations() if kind == 'relation' else repo.get_categories()


def _manage_create(kind, body):
    name = _name(body)
    if not name:
        return error('名称不能为空')
    row_id = repo.add_manage(kind, name)
    return json_response({'ok': True, 'id': row_id}, 201)


def _manage_update(kind, params, body):
    name = _name(body)
    if not name:
        return error('名称不能为空')
    repo.update_manage(kind, params['id'], name)
    return json_response({'ok': True})


def _manage_delete(kind, params):
    if repo.manage_in_use(kind, params['id']):
        return error('该项已有记录使用，暂不能删除', 409)
    repo.delete_manage(kind, params['id'])
    return json_response({'ok': True})


def list_relations(params, body, query):
    return json_response({'relations': _manage_rows('relation')})


def create_relation(params, body, query):
    return _manage_create('relation', body)


def update_relation(params, body, query):
    return _manage_update('relation', params, body)


def delete_relation(params, body, query):
    return _manage_delete('relation', params)


def list_categories(params, body, query):
    return json_response({'categories': _manage_rows('category')})


def create_category(params, body, query):
    return _manage_create('category', body)


def update_category(params, body, query):
    return _manage_update('category', params, body)


def delete_category(params, body, query):
    return _manage_delete('category', params)


# ---------- 导入 /api/imports、导出 /api/exports、模板 /api/templates ----------
def _import(params, body, kind):
    try:
        raw = base64.b64decode(body.get('data', ''))
        if not raw:
            raise ValueError('文件为空')
        stat = (importer.import_bill_rows(raw) if kind == 'bills'
                else importer.import_expense_rows(raw))
        return json_response({'ok': True, 'stat': stat})
    except Exception as exc:
        return error('导入失败：' + str(exc), 400)


def import_bills(params, body, query):
    return _import(params, body, 'bills')


def import_expenses(params, body, query):
    return _import(params, body, 'expenses')


def export_bills(params, body, query):
    return xlsx_response(exporter.export_bills(), '礼单.xlsx')


def export_expenses(params, body, query):
    return xlsx_response(exporter.export_expenses(), '随礼.xlsx')


def template_bills(params, body, query):
    return xlsx_response(exporter.template_bills(), '礼单模板.xlsx')


def template_expenses(params, body, query):
    return xlsx_response(exporter.template_expenses(), '随礼模板.xlsx')


# ---------- 路由表 ----------
Route = namedtuple('Route', 'method pattern handler name')
ROUTES = []


def route(method, path, handler, name):
    ROUTES.append(Route(method, re.compile(r'^' + path + r'$'), handler, name))


# 页面聚合
route('GET', r'/api/dashboard', dashboard, 'dashboard')
route('GET', r'/api/stats', stats, 'stats')

# 礼单
route('GET', r'/api/bills', list_bills, 'bills.list')
route('POST', r'/api/bills', create_bill, 'bills.create')
route('GET', r'/api/bills/(?P<id>\d+)', get_bill, 'bills.get')
route('PUT', r'/api/bills/(?P<id>\d+)', update_bill, 'bills.update')
route('DELETE', r'/api/bills/(?P<id>\d+)', delete_bill, 'bills.delete')

# 收礼人员（列表与创建嵌套在礼单下，单条资源共享 /api/people）
route('GET', r'/api/bills/(?P<id>\d+)/people', list_people, 'people.list')
route('POST', r'/api/bills/(?P<id>\d+)/people', create_person, 'people.create')
route('GET', r'/api/people/(?P<id>\d+)', get_person, 'people.get')
route('PUT', r'/api/people/(?P<id>\d+)', update_person, 'people.update')
route('DELETE', r'/api/people/(?P<id>\d+)', delete_person, 'people.delete')

# 随礼
route('GET', r'/api/expenses', list_expenses, 'expenses.list')
route('POST', r'/api/expenses', create_expense, 'expenses.create')
route('GET', r'/api/expenses/(?P<id>\d+)', get_expense, 'expenses.get')
route('PUT', r'/api/expenses/(?P<id>\d+)', update_expense, 'expenses.update')
route('DELETE', r'/api/expenses/(?P<id>\d+)', delete_expense, 'expenses.delete')

# 关系与分类
route('GET', r'/api/relations', list_relations, 'relations.list')
route('POST', r'/api/relations', create_relation, 'relations.create')
route('PUT', r'/api/relations/(?P<id>\d+)', update_relation, 'relations.update')
route('DELETE', r'/api/relations/(?P<id>\d+)', delete_relation, 'relations.delete')
route('GET', r'/api/categories', list_categories, 'categories.list')
route('POST', r'/api/categories', create_category, 'categories.create')
route('PUT', r'/api/categories/(?P<id>\d+)', update_category, 'categories.update')
route('DELETE', r'/api/categories/(?P<id>\d+)', delete_category, 'categories.delete')

# 导入 / 导出 / 模板
route('POST', r'/api/imports/bills', import_bills, 'imports.bills')
route('POST', r'/api/imports/expenses', import_expenses, 'imports.expenses')
route('GET', r'/api/exports/bills', export_bills, 'exports.bills')
route('GET', r'/api/exports/expenses', export_expenses, 'exports.expenses')
route('GET', r'/api/templates/bills', template_bills, 'templates.bills')
route('GET', r'/api/templates/expenses', template_expenses, 'templates.expenses')


def dispatch(method, path, body=None, query=None):
    """按 METHOD + PATH 匹配路由；未命中返回 404。"""
    for item in ROUTES:
        if item.method != method:
            continue
        match = item.pattern.match(path)
        if match:
            params = {k: (int(v) if k == 'id' and v.isdigit() else v)
                      for k, v in match.groupdict().items()}
            return item.handler(params, body or {}, query or {})
    return error('接口不存在：' + method + ' ' + path, 404)

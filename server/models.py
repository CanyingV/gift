"""ORM 模型层：映射现有 SQLite 表结构，不手写任何 SQL 语句。

旧数据中 income.amount / income.relation_id 是 TEXT 存储的数字字符串，
Peewee 的字段会在读写时做类型转换；日期统一保留原始文本，由 Python 端归一化排序。
"""
from peewee import AutoField, CharField, ForeignKeyField, Model, SqliteDatabase

from .config import DB_PATH

db = SqliteDatabase(DB_PATH)


class BaseModel(Model):
    class Meta:
        database = db


class Relation(BaseModel):
    id = AutoField()
    name = CharField(null=True)

    class Meta:
        table_name = 'relation'


class Category(BaseModel):
    id = AutoField()
    name = CharField(null=True)

    class Meta:
        table_name = 'cate'


class Gift(BaseModel):
    id = AutoField()
    name = CharField(null=True)
    date = CharField(null=True)

    class Meta:
        table_name = 'gift'


class Income(BaseModel):
    id = AutoField()
    gift = ForeignKeyField(Gift, column_name='gift_id', backref='incomes')
    name = CharField(null=True)
    amount = CharField(null=True)
    relation = ForeignKeyField(Relation, column_name='relation_id', null=True)
    note = CharField(null=True, column_name='desc')

    class Meta:
        table_name = 'income'


class Expense(BaseModel):
    id = AutoField()
    name = CharField(null=True)
    amount = CharField(null=True)
    date = CharField(null=True)
    relation = ForeignKeyField(Relation, column_name='relation_id', null=True)
    category = ForeignKeyField(Category, column_name='cate_id', null=True)

    class Meta:
        table_name = 'expenses'


MODELS = [Relation, Category, Gift, Income, Expense]


def init_db():
    """首次运行时建表；已有数据库文件保持原样。"""
    db.create_tables(MODELS, safe=True)

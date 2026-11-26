'use strict';

/* 表单提交动作：所有数据变更都经 mutate() 调用后端 API */
const relField = value => ({
    name: 'relation_id', label: '关系', type: 'select', value,
    options: (data.relations || []).map(r => ({value: r.id, label: r.name})), required: true
});
const cateField = value => ({
    name: 'cate_id', label: '分类', type: 'select', value,
    options: (data.categories || []).map(c => ({value: c.id, label: c.name})), required: true
});
const billField = value => ({
    name: 'bill_id', label: '所属礼单', type: 'select', value,
    options: (data.billOptions || data.bills || []).map(b => ({value: b.id, label: b.name})), required: true
});
const numFields = d => ({
    ...d,
    amount: Number(d.amount), relation_id: Number(d.relation_id),
    cate_id: Number(d.cate_id), bill_id: Number(d.bill_id)
});

function addBill() {
    openForm('创建礼单', '', [
        {name: 'name', label: '礼单名称', placeholder: '例如：生日', required: true},
        {name: 'date', label: '日期', type: 'date', value: today, required: true}
    ], d => mutate('/api/bills', 'POST', d, '礼单已创建'));
}

function editBill(x) {
    openForm('编辑', x.name, [
        {name: 'name', label: '礼单名称', value: x.name, required: true},
        {name: 'date', label: '日期', type: 'date', value: x.date, required: true}
    ], d => mutate('/api/bills/' + x.id, 'PUT', d, '已保存'));
}

function addPerson(id) {
    openForm('上礼', '', [
        {name: 'name', label: '姓名', placeholder: '请输入姓名', required: true},
        relField(),
        {name: 'amount', label: '金额（元）', type: 'number', min: 0, step: '0.01', placeholder: '0.00', required: true},
        {name: 'note', label: '备注', placeholder: '选填', full: true}
    ], d => mutate('/api/bills/' + id + '/people', 'POST', {
        ...d, amount: Number(d.amount), relation_id: Number(d.relation_id)
    }, '已添加'));
}

function editPerson(x) {
    openForm('编辑', x.name, [
        billField(x.bill_id), relField(x.relation_id),
        {name: 'name', label: '姓名', value: x.name, required: true},
        {name: 'amount', label: '金额（元）', type: 'number', min: 0, step: '0.01', value: x.amount, required: true},
        {name: 'note', label: '备注', value: x.note || '', full: true}
    ], d => mutate('/api/people/' + x.id, 'PUT', numFields(d), '已保存'));
}

function addExpense() {
    openForm('记录随礼', '', [
        {name: 'name', label: '姓名', placeholder: '请输入姓名', required: true},
        cateField(), relField(),
        {name: 'amount', label: '金额（元）', type: 'number', min: 0, step: '0.01', placeholder: '0.00', required: true},
        {name: 'date', label: '日期', type: 'date', value: today, required: true}
    ], d => mutate('/api/expenses', 'POST', {
        ...d, amount: Number(d.amount), relation_id: Number(d.relation_id), cate_id: Number(d.cate_id)
    }, '已记录'));
}

function editExpense(x) {
    openForm('编辑随礼记录', x.name, [
        {name: 'name', label: '姓名', value: x.name, required: true},
        cateField(x.cate_id), relField(x.relation_id),
        {name: 'amount', label: '金额（元）', type: 'number', min: 0, step: '0.01', value: x.amount, required: true},
        {name: 'date', label: '日期', type: 'date', value: x.date, required: true}
    ], d => mutate('/api/expenses/' + x.id, 'PUT', numFields(d), '已保存'));
}

function editManage(kind, x) {
    const isRel = kind === 'relation';
    openForm(isRel ? '修改关系' : '修改分类', x.name, [
        {name: 'name', label: '名称', value: x.name, required: true, full: true}
    ], d => mutate('/api/' + (isRel ? 'relations' : 'categories') + '/' + x.id, 'PUT', d, '已保存'));
}

'use strict';

/* 总览页：只负责把数据组装成模板变量，HTML 结构在 templates/dashboard.html */
function dashboardCtx() {
    const bills = data.bills || [], expenses = data.expenses || [];
    const s = data.summary || {};
    const income = s.income || 0, out = s.out || 0, net = s.net || 0;
    const kpis = [
        kpi('收礼总额', `<span class="income">${money(income)}</span>`, `共 ${s.people || 0} 位来客`, 'wallet', 'in'),
        kpi('礼单数量', s.billCount || 0, `最近 ${s.latestBillDate ? fmtDate(s.latestBillDate) : '暂无'}`, 'list'),
        kpi('随礼总额', `<span class="expense">${money(out)}</span>`, `共 ${s.expenseCount || 0} 笔记录`, 'out', 'out'),
        kpi('往来结余', money(net), net >= 0 ? '收礼多于随礼' : '随礼多于收礼', 'chart', 'gold')
    ].join('');

    const recentBills = bills.length ? `<div class="list">${bills.slice(0, 5).map(b => `
        <div class="list-row click" data-action="open-bill" data-id="${b.id}">
            <div class="cell-main"><div class="avatar">${icon('list')}</div><div class="cell-body"><div class="cell-title">${esc(b.name)}</div><div class="cell-sub">${fmtDate(b.date)} · ${b.people} 人</div></div></div>
            <div class="cell-amount money income">${money(b.amount)}</div><div class="icon-btn">${icon('chevron')}</div>
        </div>`).join('')}</div>`
        : empty('还没有礼单，先创建一份吧', `<button class="btn primary sm" data-action="new-bill">${icon('plus')} 创建礼单</button>`);

    const recentExpenses = expenses.length ? `<div class="list">${expenses.slice(0, 5).map(e => `
        <div class="list-row">
            <div class="cell-main"><div class="avatar" style="${styleOf('relation', e.relation_id)}">${esc(initial(e.name))}</div><div class="cell-body"><div class="cell-title">${esc(e.name)}</div><div class="cell-sub">${esc(e.category || catName(e.cate_id))} · ${fmtDate(e.date)}</div></div></div>
            <div class="cell-amount money expense">${money(e.amount)}</div>
        </div>`).join('')}</div>`
        : empty('还没有随礼记录', `<button class="btn primary sm" data-action="new-expense">${icon('plus')} 记录随礼</button>`);

    return {template: 'dashboard', ctx: {kpis, recentBills, recentExpenses}};
}

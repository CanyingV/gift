'use strict';

/* 礼单列表页：HTML 结构在 templates/bills.html */
function billsCtx() {
    const bills = [...(data.bills || [])];
    const sorted = bills;
    // 默认按后端返回的日期倒序；只有用户主动切换排序时才在前端重排
    if (state.sort === 'amount-desc') sorted.sort((a, b) => Number(b.amount) - Number(a.amount));
    else if (state.sort === 'amount-asc') sorted.sort((a, b) => Number(a.amount) - Number(b.amount));
    else if (state.sort === 'date-asc') sorted.sort((a, b) => dateKey(a.date).localeCompare(dateKey(b.date)) || a.id - b.id);
    const totalAmount = sum(bills, 'amount');
    const totalPeople = bills.reduce((n, b) => n + Number(b.people || 0), 0);

    const kpis = [
        kpi('礼单总数', bills.length, '', 'list'),
        kpi('收礼总额', `<span class="income">${money(totalAmount)}</span>`, '', 'wallet', 'in'),
        kpi('来客人数', totalPeople, '', 'users'),
        kpi('平均每单', money(bills.length ? totalAmount / bills.length : 0), '', 'chart', 'gold')
    ].join('');

    const sortOptions = [
        ['date-desc', '时间↓'], ['date-asc', '时间↑'],
        ['amount-desc', '金额↓'], ['amount-asc', '金额↑']
    ].map(([v, label]) => `<option value="${v}" ${state.sort === v ? 'selected' : ''}>${label}</option>`).join('');

    const listBlock = sorted.length ? `<div class="list" id="bill-list">${sorted.map(b => `
        <div class="row-wrap" data-search="${esc(String(b.name || '').toLowerCase())}">
            <div class="list-row click" data-action="open-bill" data-id="${b.id}">
                <div class="cell-main"><div class="avatar">${icon('gift')}</div><div class="cell-body"><div class="cell-title">${esc(b.name)}</div><div class="cell-sub">${esc(fmtDate(b.date))}<span class="cell-count-mobile"> · ${b.people} 人</span></div></div></div>
                <div class="cell-count">${b.people} 人</div>
                <div class="cell-amount money income">${money(b.amount)}</div>
            </div>
            <div class="row-actions">
                <button class="icon-btn" data-action="edit-bill" data-id="${b.id}" title="编辑">${icon('edit')}</button>
                <button class="icon-btn danger" data-action="del-bill" data-id="${b.id}" title="删除">${icon('trash')}</button>
            </div>
        </div>`).join('')}</div><div class="search-none" id="bill-none" style="display:none">没有找到匹配的礼单</div>`
        : empty('还没有礼单，点击右上角创建一份', `<button class="btn primary sm" data-action="new-bill">${icon('plus')} 创建礼单</button>`);

    return {
        template: 'bills',
        ctx: {
            kpis, sortOptions, listBlock,
            query: esc(state.q), count: sorted.length
        }
    };
}

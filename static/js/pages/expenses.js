'use strict';

/* 随礼页：HTML 结构在 templates/expenses.html */
function expensesCtx() {
    let list = [...(data.expenses || [])];
    list = list.filter(e => {
        if (state.expCate && String(e.cate_id) !== state.expCate) return false;
        if (state.expRel && String(e.relation_id) !== state.expRel) return false;
        return true;
    });
    // 默认按后端返回的日期倒序；切换排序时仅在前端重排
    if (state.expSort === 'amount-desc') list.sort((a, b) => Number(b.amount) - Number(a.amount));
    else if (state.expSort === 'amount-asc') list.sort((a, b) => Number(a.amount) - Number(b.amount));
    else if (state.expSort === 'date-asc') list.sort((a, b) => dateKey(a.date).localeCompare(dateKey(b.date)) || a.id - b.id);

    const all = data.expenses || [];
    const kpis = [
        kpi('随礼总额', `<span class="expense">${money(sum(all, 'amount'))}</span>`, '', 'out', 'out'),
        kpi('记录笔数', all.length, '', 'list'),
        kpi('平均每笔', money(all.length ? sum(all, 'amount') / all.length : 0), '', 'chart', 'gold'),
        kpi('最大一笔', money(Math.max(0, ...all.map(e => Number(e.amount || 0)))), '', 'wallet')
    ].join('');

    const categoryOptions = (data.categories || []).map(c =>
        `<option value="${c.id}" ${state.expCate == c.id ? 'selected' : ''}>${esc(c.name)}</option>`).join('');
    const relationOptions = (data.relations || []).map(r =>
        `<option value="${r.id}" ${state.expRel == r.id ? 'selected' : ''}>${esc(r.name)}</option>`).join('');
    const sortOptions = [
        ['date-desc', '时间↓'], ['date-asc', '时间↑'],
        ['amount-desc', '金额↓'], ['amount-asc', '金额↑']
    ].map(([v, label]) => `<option value="${v}" ${state.expSort === v ? 'selected' : ''}>${label}</option>`).join('');

    const listBlock = list.length ? `<div class="list" id="exp-list">${list.map(e => `
        <div class="row-wrap" data-search="${esc(String(e.name || '').toLowerCase())}">
            <div class="list-row">
                <div class="cell-main"><div class="avatar" style="${styleOf('relation', e.relation_id)}">${esc(initial(e.name))}</div><div class="cell-body"><div class="cell-title">${esc(e.name)}</div><div class="cell-meta-line"><div class="cell-sub">${esc(fmtDate(e.date))}</div><div class="cell-tags-mobile"><span class="chip" style="${styleOf('relation', e.relation_id)}">${esc(e.relation || relName(e.relation_id))}</span><span class="chip" style="${styleOf('category', e.cate_id)}">${esc(e.category || catName(e.cate_id))}</span></div></div></div></div>
                <div class="cell-tags"><span class="chip" style="${styleOf('relation', e.relation_id)}">${esc(e.relation || relName(e.relation_id))}</span><span class="chip" style="${styleOf('category', e.cate_id)}">${esc(e.category || catName(e.cate_id))}</span></div>
                <div class="cell-amount money expense">${money(e.amount)}</div>
            </div>
            <div class="row-actions">
                <button class="icon-btn" data-action="edit-expense" data-id="${e.id}" title="编辑">${icon('edit')}</button>
                <button class="icon-btn danger" data-action="del-expense" data-id="${e.id}" title="删除">${icon('trash')}</button>
            </div>
        </div>`).join('')}</div><div class="search-none" id="exp-none" style="display:none">没有找到匹配的记录</div>`
        : empty('还没有随礼记录，点击右上角添加一笔', `<button class="btn primary sm" data-action="new-expense">${icon('plus')} 记录随礼</button>`);

    return {
        template: 'expenses',
        ctx: {
            kpis, categoryOptions, relationOptions, sortOptions, listBlock,
            query: esc(state.expQ), count: list.length
        }
    };
}

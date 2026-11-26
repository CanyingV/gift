'use strict';

/* 礼单详情页：HTML 结构在 templates/bill_detail.html */
function billDetailCtx(bill) {
    const ps = (data.people || []).filter(x => x.bill_id == bill.id);
    const shown = ps.filter(x => !state.personRel || String(x.relation_id) === state.personRel);
    const groups = (data.relations || []).map(r => ({
        id: r.id, name: r.name, n: ps.filter(p => p.relation_id == r.id).length,
        v: sum(ps.filter(p => p.relation_id == r.id), 'amount')
    })).filter(x => x.n);
    const total = sum(ps, 'amount') || 1;

    const relationSummary = groups.length ? `<div class="segment">${groups.map(g =>
        `<i style="width:${g.v / total * 100}%;background:${toneOf('relation', g.id).solid}"></i>`).join('')}</div>
        <div class="legend">${groups.map(g =>
        `<div class="legend-item"><span class="dot" style="background:${toneOf('relation', g.id).solid}"></span>${esc(g.name)} · ${g.n} 人 <b>${money(g.v)}</b></div>`).join('')}</div>`
        : '<div class="muted" style="font-size:13px">添加人员后，这里会自动汇总各关系的礼金</div>';

    const relationOptions = (data.relations || []).map(r =>
        `<option value="${r.id}" ${state.personRel == r.id ? 'selected' : ''}>${esc(r.name)}</option>`).join('');

    const peopleBlock = shown.length ? `<div class="list" id="person-list">${shown.map(p => `
        <div class="row-wrap" data-search="${esc((String(p.name || '') + relName(p.relation_id) + String(p.note || '')).toLowerCase())}">
            <div class="list-row">
                <div class="cell-main"><div class="avatar" style="${styleOf('relation', p.relation_id)}">${esc(initial(p.name))}</div><div class="cell-body"><div class="cell-title">${esc(p.name)}</div>${p.note ? `<div class="cell-sub">${esc(p.note)}</div>` : ''}</div></div>
                <span class="chip" style="${styleOf('relation', p.relation_id)}">${esc(relName(p.relation_id))}</span>
                <div class="cell-amount money income">${money(p.amount)}</div>
            </div>
            <div class="row-actions">
                <button class="icon-btn" data-action="edit-person" data-id="${p.id}" title="编辑">${icon('edit')}</button>
                <button class="icon-btn danger" data-action="del-person" data-id="${p.id}" title="删除">${icon('trash')}</button>
            </div>
        </div>`).join('')}</div><div class="search-none" id="person-none" style="display:none">没有找到匹配的人员</div>`
        : empty('这份礼单还没有人，添加第一位来客吧', `<button class="btn primary sm" data-action="new-person" data-id="${bill.id}">${icon('plus')} 添加人员</button>`);

    return {
        template: 'bill_detail',
        ctx: {
            billId: bill.id, billName: esc(bill.name), billDate: esc(fmtDate(bill.date)),
            peopleCount: ps.length, peopleAmount: money(sum(ps, 'amount')),
            relationSummary, relationOptions, peopleBlock,
            visibleCount: shown.length, personQuery: esc(state.personQ)
        }
    };
}

'use strict';

/* 统计页：HTML 结构在 templates/stats.html */
function chartCard(title, rows, tone, foot) {
    const active = rows.filter(r => Number(r[1]) > 0);
    return `<section class="card"><div class="card-head"><div><div class="card-title">${title}</div><div class="card-sub">${foot}</div></div></div>
        ${active.length ? active.map(r => {
        const max = Math.max(...active.map(x => Number(x[1])), 1);
        return `<div class="chart-row"><div class="chart-line"><span>${esc(r[0])}</span><b class="${tone === 'red' ? 'income' : tone === 'gold' ? '' : 'expense'}">${money(r[1])}</b></div><div class="bar-track"><div class="bar-fill ${tone || ''}" style="width:${Number(r[1]) / max * 100}%"></div></div></div>`;
    }).join('') : '<div class="muted" style="font-size:12px;padding:14px 0">暂无数据</div>'}</section>`;
}

function statsCtx() {
    const s = data.summary || {};
    const income = s.income || 0, out = s.out || 0;

    const summary = `
        <div class="summary-item"><span>收礼总额</span><b class="income">${money(income)}</b></div>
        <div class="summary-item"><span>随礼总额</span><b class="expense">${money(out)}</b></div>
        <div class="summary-item"><span>往来结余</span><b>${money(s.net || 0)}</b></div>
        <span class="chip ${income >= out ? 'red' : 'green'}">${income >= out ? '收礼多于随礼' : '随礼多于收礼'}</span>`;

    // 聚合由后端完成，前端只接收 [[名称, 金额], ...]
    const charts = [
        chartCard('收礼(关系)', data.incomeByRelation || [], 'red', ''),
        chartCard('随礼(关系)', data.outByRelation || [], '', ''),
        chartCard('随礼(类别)', data.outByCategory || [], 'gold', '')
    ].join('');

    const tagList = (items, kind) => items.length ? items.map(x => `<span class="tag">${esc(x.name)}
        <button class="icon-btn" data-action="edit-${kind}" data-id="${x.id}" title="编辑">${icon('edit')}</button>
        <button class="icon-btn danger" data-action="del-${kind}" data-id="${x.id}" title="删除">${icon('trash')}</button></span>`).join('')
        : '<span class="muted" style="font-size:12px">暂无' + (kind === 'relation' ? '关系' : '分类') + '</span>';

    return {
        template: 'stats',
        ctx: {
            summary, charts,
            relationTags: tagList(data.relations || [], 'relation'),
            categoryTags: tagList(data.categories || [], 'category')
        }
    };
}

'use strict';

/* 弹窗、提示、导入导出的通用交互，见 templates/index.html 中的通用结构 */
function closeModal() {
    const host = $('#modal-host');
    if (host) host.remove();
    document.removeEventListener('keydown', onEsc);
}

function onEsc(e) {
    if (e.key === 'Escape') closeModal();
}

function showModal(html) {
    closeModal();
    const host = document.createElement('div');
    host.className = 'modal-mask';
    host.id = 'modal-host';
    host.innerHTML = `<div class="modal" role="dialog" aria-modal="true">${html}</div>`;
    document.body.appendChild(host);
    host.addEventListener('click', e => {
        if (e.target === host || e.target.closest('[data-close]')) closeModal();
    });
    document.addEventListener('keydown', onEsc);
}

function openForm(title, subtitle, fields, submit, danger) {
    const body = fields.map(f => {
        let input;
        if (f.type === 'select') {
            input = `<select class="input" name="${f.name}" ${f.required ? 'required' : ''}>${f.options.map(o => `<option value="${esc(o.value)}" ${String(o.value) === String(f.value) ? 'selected' : ''}>${esc(o.label)}</option>`).join('')}</select>`;
        } else {
            input = `<input class="input" name="${f.name}" type="${f.type || 'text'}" value="${esc(f.value ?? '')}" ${f.placeholder ? `placeholder="${esc(f.placeholder)}"` : ''} ${f.min !== undefined ? `min="${f.min}"` : ''} ${f.step ? `step="${f.step}"` : ''} ${f.required ? 'required' : ''}>`;
        }
        return `<label class="field ${f.full ? 'full' : ''}"><span>${f.label}</span>${input}</label>`;
    }).join('');
    showModal(`<div class="modal-head"><div class="modal-icon ${danger ? 'danger' : ''}">${icon(danger ? 'alert' : 'edit')}</div><div><h3>${esc(title)}</h3><p>${esc(subtitle || '')}</p></div></div>
        <form id="app-form"><div class="form-grid">${body}</div><div class="modal-foot"><button type="button" class="btn ghost" data-close>取消</button><button type="submit" class="btn ${danger ? 'danger' : 'primary'}">保存</button></div></form>`);
    $('#app-form').addEventListener('submit', e => {
        e.preventDefault();
        submit(Object.fromEntries(new FormData(e.currentTarget)));
    });
}

function confirmDialog(title, message, onOk) {
    showModal(`<div class="modal-head"><div class="modal-icon danger">${icon('trash')}</div><div><h3>${esc(title)}</h3><p>请确认这一步操作</p></div></div>
        <div class="confirm-text">${esc(message)}</div>
        <div class="modal-foot"><button class="btn ghost" data-close>取消</button><button class="btn danger" id="confirm-ok">确认删除</button></div>`);
    $('#confirm-ok').addEventListener('click', onOk);
}

function exportDialog() {
    showModal(`<div class="modal-head"><div class="modal-icon">${icon('upload')}</div><div><h3>导出 Excel</h3><p>选择需要下载的数据文件</p></div></div>
        <div class="export-list">
            <a class="export-item" href="/api/exports/bills" download="礼单.xlsx" data-action="dl" data-url="/api/exports/bills" data-name="礼单.xlsx">
                <div class="export-icon red">${icon('gift')}</div>
                <div class="export-txt"><b>礼单.xlsx</b><small>礼单汇总 + 全部明细（按日期倒序）</small></div>
                ${icon('chevron')}
            </a>
            <a class="export-item" href="/api/exports/expenses" download="随礼.xlsx" data-action="dl" data-url="/api/exports/expenses" data-name="随礼.xlsx">
                <div class="export-icon green">${icon('out')}</div>
                <div class="export-txt"><b>随礼.xlsx</b><small>全部随礼记录（按日期倒序）</small></div>
                ${icon('chevron')}
            </a>
        </div>
        <div class="modal-foot"><button class="btn ghost" data-close>关闭</button></div>`);
}

function importDialog() {
    showModal(`<div class="modal-head"><div class="modal-icon">${icon('download')}</div><div><h3>导入 Excel</h3><p>按导出文件的格式导入，重复记录会自动跳过</p></div></div>
        <div class="export-list">
            <div class="export-item">
                <div class="export-icon red">${icon('gift')}</div>
                <div class="export-txt"><b>礼单.xlsx</b><small>礼单汇总 + 明细；同名礼单不重复创建</small></div>
                <button type="button" class="btn ghost sm" data-action="pick-file" data-kind="bills">选择文件</button>
                <input type="file" id="file-bills" accept=".xlsx" hidden>
            </div>
            <div class="export-item">
                <div class="export-icon green">${icon('out')}</div>
                <div class="export-txt"><b>随礼.xlsx</b><small>随礼记录；相同记录自动跳过</small></div>
                <button type="button" class="btn ghost sm" data-action="pick-file" data-kind="expenses">选择文件</button>
                <input type="file" id="file-expenses" accept=".xlsx" hidden>
            </div>
        </div>
        <div class="import-tip">没有文件？<a href="/api/templates/bills" download="礼单模板.xlsx" data-action="dl" data-url="/api/templates/bills" data-name="礼单模板.xlsx">下载礼单模板</a> · <a href="/api/templates/expenses" download="随礼模板.xlsx" data-action="dl" data-url="/api/templates/expenses" data-name="随礼模板.xlsx">下载随礼模板</a>（格式与导出一致）</div>
        <div class="modal-foot"><button class="btn ghost" data-close>关闭</button></div>`);
    ['bills', 'expenses'].forEach(kind => {
        const input = $('#file-' + kind);
        input.addEventListener('change', () => {
            if (input.files && input.files[0]) doImport(kind, input.files[0]);
        });
    });
}

async function doImport(kind, file) {
    try {
        const buf = await file.arrayBuffer();
        const bytes = new Uint8Array(buf);
        let bin = '';
        const chunk = 0x8000;
        for (let i = 0; i < bytes.length; i += chunk) {
            bin += String.fromCharCode.apply(null, bytes.subarray(i, i + chunk));
        }
        const base64 = btoa(bin);
        const r = await fetch('/api/imports/' + kind, {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({data: base64})
        });
        const d = await r.json().catch(() => ({ok: false}));
        if (!d.ok) throw new Error(d.error || '导入失败');
        const s = d.stat || {};
        const parts = [];
        if (kind === 'bills') {
            if (s.bills) parts.push('礼单 ' + s.bills);
            if (s.people) parts.push('明细 ' + s.people);
            if (s.relations) parts.push('关系 ' + s.relations);
        } else {
            if (s.expenses) parts.push('随礼 ' + s.expenses);
            if (s.relations) parts.push('关系 ' + s.relations);
            if (s.categories) parts.push('分类 ' + s.categories);
        }
        const msg = '导入成功' + (parts.length ? '：' + parts.join('、') : '（无新增）') +
            (s.skipped ? '；跳过重复 ' + s.skipped : '');
        closeModal();
        toast(msg);
        await refresh();
    } catch (e) {
        toast(e.message || '导入失败', true);
    }
}

async function downloadFile(url, name) {
    const api = window.pywebview && window.pywebview.api;
    if (api && (api.save_file || api.saveFile)) {
        try {
            const r = await fetch(url);
            const blob = await r.blob();
            const buf = await blob.arrayBuffer();
            const bytes = new Uint8Array(buf);
            let bin = '', chunk = 0x8000;
            for (let i = 0; i < bytes.length; i += chunk)
                bin += String.fromCharCode.apply(null, bytes.subarray(i, i + chunk));
            const res = await (api.save_file || api.saveFile)(name, btoa(bin));
            if (res && res.ok) toast('已保存到下载目录：' + name);
            else throw new Error((res && res.error) || '保存失败');
        } catch (e) {
            toast('导出失败：' + (e.message || e), true);
        }
    } else {
        const a = document.createElement('a');
        a.href = url;
        a.download = name;
        document.body.appendChild(a);
        a.click();
        a.remove();
    }
}

function toast(msg, bad) {
    const t = document.createElement('div');
    t.className = 'toast' + (bad ? ' bad' : '');
    t.innerHTML = `${icon(bad ? 'alert' : 'check')}<span>${esc(msg)}</span>`;
    document.body.appendChild(t);
    setTimeout(() => {
        t.classList.add('out');
        setTimeout(() => t.remove(), 260);
    }, 2200);
}

async function mutate(url, method, body, msg, before) {
    try {
        const opt = {method: method || 'POST'};
        if (body !== null && body !== undefined) {
            opt.headers = {'Content-Type': 'application/json'};
            opt.body = JSON.stringify(body);
        }
        const r = await fetch(url, opt);
        const d = await r.json().catch(() => ({ok: true}));
        if (!d.ok) throw new Error(d.error || '操作失败');
        closeModal();
        // before 返回 true 表示它已切换到别的路由，由 hashchange 负责加载
        const navigated = before ? before() === true : false;
        toast(msg || '已保存');
        if (!navigated) await refresh();
    } catch (e) {
        toast(e.message || '操作失败', true);
    }
}

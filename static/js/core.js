'use strict';

/* 全局状态与通用工具：页面模板见 /templates/*.html，各页面数据组装见 pages/*.js */
const state = {
    page: 'dashboard',
    billId: null,
    q: '',
    sort: 'date-desc',
    personQ: '',
    personRel: '',
    expQ: '',
    expCate: '',
    expRel: '',
    expSort: 'date-desc'
};
let data = {};
let swipedWrap = null, touchStart = null;

function closeSwipe() {
    if (swipedWrap) {
        swipedWrap.classList.remove('swiped');
        swipedWrap = null;
    }
}

const $ = s => document.querySelector(s);
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
}[c]));
const icon = n => `<svg class="ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><use href="#i-${n}"></use></svg>`;
const money = n => '¥' + Number(n || 0).toLocaleString('zh-CN', {
    minimumFractionDigits: 0, maximumFractionDigits: 2
});
const sum = (xs, k) => (xs || []).reduce((s, x) => s + Number(x[k] || 0), 0);
const relName = id => (data.relations || []).find(x => x.id == id)?.name || '其他';
const catName = id => (data.categories || []).find(x => x.id == id)?.name || '其他';
const findBill = id => (data.bills || []).find(x => x.id == id);

const now = new Date();
const today = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`;

function fmtDate(s) {
    if (!s) return '—';
    const p = String(s).split('-');
    return p.length >= 3 ? `${p[0]}.${p[1].padStart(2, '0')}.${p[2].padStart(2, '0')}` : String(s);
}

function dateKey(s) {
    const p = String(s || '').split('-');
    return p.length >= 3 ? `${p[0]}-${p[1].padStart(2, '0')}-${p[2].padStart(2, '0')}` : String(s || '');
}

const TONES = {
    green: {bg: '#eaf3ed', fg: '#276b4d', solid: '#2f7a63'},
    gold: {bg: '#f8f0e1', fg: '#9a6d2d', solid: '#c08a3e'},
    rust: {bg: '#f9ece7', fg: '#a9503a', solid: '#b4533a'},
    blue: {bg: '#eaf0f6', fg: '#4b6f92', solid: '#6c8fb3'},
    purple: {bg: '#f1ecf7', fg: '#775ba0', solid: '#8d6e9f'},
    teal: {bg: '#e9f4f3', fg: '#2f7a72', solid: '#4a9b91'}
};
const REL_ORDER = ['green', 'gold', 'rust', 'blue', 'purple', 'teal'];
const CAT_ORDER = ['gold', 'blue', 'purple', 'green', 'rust', 'teal'];

function toneOf(kind, id) {
    const order = kind === 'category' ? CAT_ORDER : REL_ORDER;
    return TONES[order[Math.max(0, Number(id) - 1) % order.length]];
}

const styleOf = (kind, id) => {
    const t = toneOf(kind, id);
    return `background:${t.bg};color:${t.fg}`;
};
const initial = name => {
    const chars = Array.from(String(name || '').trim());
    return chars.length ? chars[chars.length - 1] : '?';
};

function kpi(label, value, foot, ic, tone) {
    return `<div class="card kpi"><div class="kpi-top"><span class="icon-box ${tone ? 'tone-' + tone : ''}">${icon(ic)}</span><span class="kpi-label">${label}</span></div><div class="value ${tone || ''}">${value}</div><div class="foot">${foot}</div></div>`;
}

function empty(text, action) {
    return `<div class="empty"><div class="empty-icon">${icon('gift')}</div><p>${esc(text)}</p>${action || ''}</div>`;
}

function pageHead(eyebrow, title, sub, action) {
    return `<div class="page-head"><div><div class="eyebrow">${eyebrow}</div><h1>${title}</h1><div class="page-sub">${sub}</div></div><div>${action || ''}</div></div>`;
}

/* ---------- 路由与按需加载 ---------- */
/* 每个路由只请求本页数据；模板也按路由加载，不再一次性预取全部。 */
const PAGE_APIS = {
    dashboard: '/api/dashboard',
    bills: '/api/bills',
    bill: id => '/api/bills/' + encodeURIComponent(id),
    expenses: '/api/expenses',
    stats: '/api/stats'
};
const tplCache = {};
let loadSeq = 0, renderSeq = 0;

function routeHash(page, billId) {
    return billId ? `#/bills/${billId}` : `#/${page || 'dashboard'}`;
}

function parseRoute() {
    const parts = String(location.hash || '').replace(/^#\/?/, '').split('/').filter(Boolean);
    if (parts[0] === 'bills' && parts[1] && /^\d+$/.test(parts[1]))
        return {page: 'bills', billId: Number(parts[1])};
    if (parts[0] && Object.prototype.hasOwnProperty.call(PAGE_APIS, parts[0]))
        return {page: parts[0], billId: null};
    return {page: 'dashboard', billId: null};
}

async function preloadTpl(name) {
    if (tplCache[name]) return;
    const res = await fetch('/templates/' + name + '.html');
    if (!res.ok) throw new Error('模板加载失败：' + name);
    tplCache[name] = await res.text();
}

function renderTpl(name, ctx) {
    return (tplCache[name] || '').replace(/\{\{(\w+)\}\}/g, (_, key) => (key in ctx ? ctx[key] : ''));
}

function renderTop() {
    const active = state.billId ? 'bills' : state.page;
    document.querySelectorAll('[data-nav]').forEach(b => b.classList.toggle('on', b.dataset.nav === active));
}

async function render() {
    closeSwipe();
    renderTop();
    const token = ++renderSeq;
    const app = $('#app');
    try {
        let name, ctx;
        if (state.billId) {
            const bill = data.bill;
            if (!bill || Number(bill.id) !== Number(state.billId)) {
                state.billId = null;
                try { history.replaceState(null, '', routeHash('bills')); }
                catch (_) { location.hash = '#/bills'; }
                return loadRoute();
            }
            const result = billDetailCtx(bill);
            name = result.template;
            ctx = result.ctx;
        } else {
            const builders = {
                dashboard: dashboardCtx, bills: billsCtx,
                expenses: expensesCtx, stats: statsCtx
            };
            const result = (builders[state.page] || dashboardCtx)();
            name = result.template;
            ctx = result.ctx;
        }
        if (!tplCache[name]) await preloadTpl(name);
        if (token !== renderSeq) return;
        app.innerHTML = renderTpl(name, ctx);
        restoreFilters();
    } catch (e) {
        if (token !== renderSeq) return;
        app.innerHTML = `<div class="empty"><div class="empty-icon">!</div><p>页面加载失败：${esc(e.message || e)}</p></div>`;
    }
}

// 重新渲染后按当前搜索词恢复行的显示状态（不改 state）
function restoreFilters() {
    const apply = (listId, countId, noneId, query) => {
        const list = document.getElementById(listId);
        if (!list) return;
        const q = String(query || '').trim().toLowerCase();
        const rows = list.querySelectorAll('.row-wrap');
        let shown = 0;
        rows.forEach(row => {
            const hit = !q || (row.getAttribute('data-search') || '').includes(q);
            row.style.display = hit ? '' : 'none';
            if (hit) shown++;
        });
        const count = document.getElementById(countId);
        if (count) count.textContent = shown + ' 条记录';
        const none = document.getElementById(noneId);
        if (none) none.style.display = (rows.length && shown === 0) ? '' : 'none';
    };
    apply('bill-list', 'bill-count', 'bill-none', state.q);
    apply('person-list', 'person-count', 'person-none', state.personQ);
    apply('exp-list', 'exp-count', 'exp-none', state.expQ);
}

async function rerenderKeepFocus() {
    const el = document.activeElement;
    const id = el && el.id, pos = el && el.selectionStart;
    await render();
    if (id) {
        const next = document.getElementById(id);
        if (next) {
            next.focus();
            try { next.setSelectionRange(pos, pos); } catch (_) { /* 部分元素不支持 */ }
        }
    }
}

/* 只请求当前路由的数据；快速切换时旧响应由 loadSeq 丢弃。 */
async function loadRoute() {
    const seq = ++loadSeq;
    const route = parseRoute();
    state.page = route.page;
    state.billId = route.billId;
    renderTop();
    const app = $('#app');
    app.innerHTML = '<div class="empty"><div class="empty-icon">…</div><p>加载中…</p></div>';
    try {
        const api = route.billId ? PAGE_APIS.bill(route.billId) : PAGE_APIS[route.page];
        const res = await fetch(api);
        const payload = await res.json().catch(() => ({}));
        if (seq !== loadSeq) return;
        if (!res.ok) throw new Error(payload.error || ('请求失败 ' + res.status));
        data = payload;
        await render();
    } catch (e) {
        if (seq !== loadSeq) return;
        app.innerHTML = `<div class="empty"><div class="empty-icon">!</div><p>无法读取数据：${esc(e.message || e)}</p></div>`;
    }
}

function navigate(page, billId = null) {
    const hash = routeHash(page, billId);
    if (location.hash !== hash) {
        location.hash = hash;   // hashchange 会触发 loadRoute()
    } else {
        loadRoute();            // 点击当前页时重新拉取一次
    }
}

/* 数据变更后只刷新当前页。 */
function refresh() {
    return loadRoute();
}

function start() {
    window.addEventListener('hashchange', loadRoute);
    if (!location.hash) {
        try { history.replaceState(null, '', routeHash('dashboard')); }
        catch (_) { location.hash = '#/dashboard'; }
    }
    loadRoute();
}

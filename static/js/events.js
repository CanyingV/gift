'use strict';

/* 事件绑定：与页面结构无关，统一放在这里 */
document.addEventListener('touchstart', e => {
    const wrap = e.target.closest('.row-wrap');
    if (!wrap) {
        closeSwipe();
        return;
    }
    if (swipedWrap && swipedWrap !== wrap) closeSwipe();
    const t = e.touches[0];
    touchStart = {wrap, x: t.clientX, y: t.clientY};
}, {passive: true});

document.addEventListener('touchend', e => {
    if (!touchStart) return;
    const t = e.changedTouches[0];
    const dx = t.clientX - touchStart.x, dy = t.clientY - touchStart.y;
    const wrap = touchStart.wrap;
    touchStart = null;
    if (Math.abs(dx) < 30 || Math.abs(dx) < Math.abs(dy)) return;
    if (dx < 0) {
        if (swipedWrap && swipedWrap !== wrap) closeSwipe();
        wrap.classList.add('swiped');
        swipedWrap = wrap;
    } else {
        wrap.classList.remove('swiped');
        if (swipedWrap === wrap) swipedWrap = null;
    }
}, {passive: true});

document.addEventListener('touchcancel', () => {
    touchStart = null;
}, {passive: true});

document.addEventListener('click', e => {
    if (e.target.closest('.row-wrap.swiped') && !e.target.closest('.row-actions')) {
        closeSwipe();
        return;
    }
    const nav = e.target.closest('[data-nav]');
    if (nav) {
        navigate(nav.dataset.nav);
        return;
    }
    const el = e.target.closest('[data-action]');
    if (!el) return;
    const a = el.dataset.action, id = Number(el.dataset.id);
    const one = arr => (arr || []).find(x => x.id === id);

    if (a === 'export') {
        exportDialog();
        return;
    }
    if (a === 'import') {
        importDialog();
        return;
    }
    if (a === 'dl') {
        e.preventDefault();
        downloadFile(el.dataset.url, el.dataset.name);
        return;
    }
    if (a === 'pick-file') {
        $('#file-' + el.dataset.kind).click();
        return;
    }
    if (a === 'new-bill') addBill();
    else if (a === 'new-expense') addExpense();
    else if (a === 'open-bill') {
        state.personQ = '';
        state.personRel = '';
        navigate('bills', id);
    } else if (a === 'back-bills') {
        navigate('bills');
    } else if (a === 'edit-bill') {
        const x = one(data.bills);
        if (x) editBill(x);
    } else if (a === 'del-bill') {
        const x = one(data.bills);
        if (x) confirmDialog('删除礼单', '「' + x.name + '」及其下所有收礼明细都会被删除，且无法恢复', () =>
            mutate('/api/bills/' + id, 'DELETE', null, '已删除', () => {
                if (state.billId === id) {
                    navigate('bills');   // 详情页删掉当前礼单，回到列表
                    return true;
                }
                return false;
            }));
    } else if (a === 'new-person') addPerson(id);
    else if (a === 'edit-person') {
        const x = one(data.people);
        if (x) editPerson(x);
    } else if (a === 'del-person') confirmDialog('删除收礼明细', '确定删除这条人员记录？', () => mutate('/api/people/' + id, 'DELETE', null, '已删除'));
    else if (a === 'edit-expense') {
        const x = one(data.expenses);
        if (x) editExpense(x);
    } else if (a === 'del-expense') confirmDialog('删除随礼记录', '确定删除这笔随礼记录？', () => mutate('/api/expenses/' + id, 'DELETE', null, '已删除'));
    else if (a === 'edit-relation') {
        const x = one(data.relations);
        if (x) editManage('relation', x);
    } else if (a === 'edit-category') {
        const x = one(data.categories);
        if (x) editManage('category', x);
    } else if (a === 'del-relation') confirmDialog('删除关系', '确定删除这个关系？', () => mutate('/api/relations/' + id, 'DELETE', null, '已删除'));
    else if (a === 'del-category') confirmDialog('删除分类', '确定删除这个分类？', () => mutate('/api/categories/' + id, 'DELETE', null, '已删除'));
    else if (a === 'add-relation' || a === 'add-category') {
        const isRel = a === 'add-relation';
        const input = document.getElementById(isRel ? 'relation-name' : 'category-name');
        const name = input && input.value.trim();
        if (!name) {
            toast('请先填写名称', true);
            return;
        }
        mutate('/api/' + (isRel ? 'relations' : 'categories'), 'POST', {name}, '已添加');
    }
});

// 搜索只在现有 DOM 上过滤行，不重建页面——避免桌面 WKWebView 下输入法被打断、焦点丢失
function filterRows(listId, countId, noneId, query, stateKey) {
    state[stateKey] = query;
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
}

document.addEventListener('input', e => {
    const id = e.target.id;
    if (id === 'bill-search') filterRows('bill-list', 'bill-count', 'bill-none', e.target.value, 'q');
    else if (id === 'person-search') filterRows('person-list', 'person-count', 'person-none', e.target.value, 'personQ');
    else if (id === 'exp-search') filterRows('exp-list', 'exp-count', 'exp-none', e.target.value, 'expQ');
});

document.addEventListener('change', e => {
    if (e.target.id === 'bill-sort') {
        state.sort = e.target.value;
        render();
    } else if (e.target.id === 'person-rel') {
        state.personRel = e.target.value;
        render();
    } else if (e.target.id === 'exp-cate') {
        state.expCate = e.target.value;
        render();
    } else if (e.target.id === 'exp-rel') {
        state.expRel = e.target.value;
        render();
    } else if (e.target.id === 'exp-sort') {
        state.expSort = e.target.value;
        render();
    }
});

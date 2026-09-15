/* Inlined into the report. No server, network requests, or model calls. */
const InsightsFeedback = (() => {
  'use strict';
  const maxBytes = 512 * 1024;
  const headerPattern = /^<!-- treefolk-insights-known:v1:([a-f0-9]{32}) -->$/;
  const rowPattern = /^- \[([ xX])\] (.+) <!-- insights:(advice-[a-f0-9]{16}) -->$/;
  const byteLength = text => new TextEncoder().encode(text).length;

  function parse(text, expectedId) {
    const lines = text.split(/\r?\n/);
    const header = headerPattern.exec(lines[0]);
    if (!header || byteLength(text) > maxBytes) throw new Error('这不是有效的 Insights 记录文件。');
    if (expectedId && header[1] !== expectedId) throw new Error('请选择页面所示位置的 known.md；这份文件属于另一份记录。');
    const entries = new Map();
    lines.slice(1).forEach((line, offset) => {
      const match = rowPattern.exec(line);
      if (!match) {
        if (line.includes('<!-- insights:')) throw new Error('记录条目格式有误，请保留条目后的标识。');
        return;
      }
      const [, checked, label, id] = match;
      if (entries.has(id)) throw new Error('记录文件中出现了重复标识。');
      entries.set(id, {id, label, known: checked.toLowerCase() === 'x', line: offset + 1});
    });
    return {storeId: header[1], entries, lines};
  }

  function update(text, expectedId, items, checked) {
    const state = parse(text, expectedId);
    const newline = text.includes('\r\n') ? '\r\n' : '\n';
    for (const item of items) {
      if (!/^advice-[a-f0-9]{16}$/.test(item.id) || typeof item.label !== 'string' ||
          !item.label.trim() || /[\r\n]/.test(item.label) || item.label.includes('<!-- insights:')) {
        throw new Error('建议的记录格式无效。');
      }
      const old = state.entries.get(item.id);
      if (old) {
        state.lines[old.line] = state.lines[old.line].replace(/^- \[[ xX]\]/, '- [' + (checked ? 'x' : ' ') + ']');
      } else {
        const line = '- [' + (checked ? 'x' : ' ') + '] ' + item.label + ' <!-- insights:' + item.id + ' -->';
        state.entries.set(item.id, {line: state.lines.length});
        state.lines.push(line);
      }
    }
    const result = state.lines.join(newline);
    const output = result.endsWith(newline) ? result : result + newline;
    parse(output, expectedId);
    return output;
  }

  async function read(handle, expectedId) {
    const file = await handle.getFile();
    if (file.size > maxBytes) throw new Error('记录文件过大，未读取或修改。');
    const text = await file.text();
    return {text, state: parse(text, expectedId)};
  }

  async function write(handle, expectedId, items, checked) {
    return writeChanges(handle, expectedId, [{items, checked}]);
  }

  async function writeChanges(handle, expectedId, changes) {
    // Lock first, then reread: preserve newer choices and handwritten notes.
    // Never reconstruct the file from an old HTML snapshot.
    const writable = await handle.createWritable({mode: 'exclusive'});
    try {
      const current = await read(handle, expectedId);
      const next = changes.reduce(
        (text, change) => update(text, expectedId, change.items, change.checked),
        current.text
      );
      await writable.write(next);
      await writable.close();
      return parse(next, expectedId);
    } catch (error) {
      await writable.abort().catch(() => {});
      throw error;
    }
  }

  async function remember(storeId, handle) {
    // Only a handle cache; known.md is the source of truth. file: storage and
    // permission persistence depend on the browser.
    if (!globalThis.indexedDB) return null;
    return new Promise((resolve, reject) => {
      const request = indexedDB.open('treefolk-insights-file-handles', 1);
      request.onupgradeneeded = () => request.result.createObjectStore('handles');
      request.onerror = () => reject(request.error);
      request.onblocked = () => resolve(null);
      request.onsuccess = () => {
        const db = request.result;
        const transaction = db.transaction('handles', handle ? 'readwrite' : 'readonly');
        const objectStore = transaction.objectStore('handles');
        const operation = handle ? objectStore.put(handle, storeId) : objectStore.get(storeId);
        let result = null;
        operation.onsuccess = () => { result = operation.result; };
        transaction.oncomplete = () => { db.close(); resolve(result); };
        transaction.onabort = transaction.onerror = () => { db.close(); reject(transaction.error); };
      };
    }).catch(() => null);
  }

  function mount(config) {
    const status = document.getElementById('feedback-status');
    const path = document.getElementById('feedback-path');
    const connect = document.getElementById('feedback-connect');
    const manager = document.getElementById('feedback-manager');
    const selection = document.getElementById('feedback-selection');
    const save = document.getElementById('feedback-save');
    const cancel = document.getElementById('feedback-cancel');
    const toast = document.getElementById('feedback-toast');
    const manageButtons = [...document.querySelectorAll('[data-feedback-manage]')];
    const supported = globalThis.isSecureContext && typeof globalThis.showOpenFilePicker === 'function';
    const enabled = supported && config.status === 'ready';
    let handle = null, busy = false, generation = 0, managing = false;
    let known = new Set(config.known || []);
    const controls = [];
    path.textContent = config.path || '这份旧报告没有记录文件；下次运行 insights 后可使用。';
    connect.disabled = !enabled;
    status.textContent = config.status !== 'ready' ? '已知记录不可用，本页暂不能保存更改。' :
      !supported ? '当前浏览器不支持直接写文件。请用支持此功能的桌面 Chrome 或 Edge 打开。' :
      '选择建议后再保存；首次保存时会要求选择记录文件。';

    function knownState(control) {
      const count = control.items.filter(item => known.has(item.id)).length;
      return count === control.items.length ? 'all' : count ? 'partial' : 'none';
    }

    function isDirty(control) {
      if (control.input.indeterminate) return false;
      const state = knownState(control);
      return state === 'partial' || control.input.checked !== (state === 'all');
    }

    function announce(message, error = false) {
      toast.textContent = message;
      toast.dataset.state = error ? 'error' : 'saved';
      toast.hidden = !message;
    }

    function refresh(resetDraft = false) {
      for (const control of controls) {
        const state = knownState(control);
        if (resetDraft || !managing) {
          control.input.checked = state === 'all';
          control.input.indeterminate = state === 'partial';
        }
        control.input.disabled = busy || !enabled;
        control.result.hidden = managing || state !== 'all';
        control.undo.disabled = busy || !enabled;
      }
      const dirty = controls.filter(isDirty);
      selection.textContent = dirty.length ? '已选择 '+dirty.length+' 项更改' : '选择要调整的建议';
      save.textContent = dirty.length ? '保存 '+dirty.length+' 项更改' : '保存更改';
      save.disabled = busy || !enabled || !dirty.length;
      cancel.textContent = dirty.length ? '取消' : '完成';
      connect.disabled = busy || !enabled;
      manager.hidden = !managing;
      document.body.classList.toggle('known-managing', managing);
      for (const button of manageButtons) {
        button.hidden = !controls.length;
        button.disabled = busy;
        button.setAttribute('aria-pressed', String(managing));
      }
    }
    function adopt(state) {
      known = new Set([...state.entries.values()].filter(item => item.known).map(item => item.id));
      refresh(true);
    }
    function failed(error) {
      status.textContent = error.name === 'AbortError' ? '已取消，未保存；选择仍保留。' :
        error.name === 'NotAllowedError' ? '没有写入权限，未保存。可以重新选择记录文件后再试。' :
        error.name === 'NoModificationAllowedError' ? '记录文件正被占用，未保存。请稍后重试。' :
        '未保存：' + error.message;
      announce(status.textContent, true);
    }
    async function choose(force = false) {
      if (!handle || force) {
        const [selected] = await showOpenFilePicker({id: 'insights-known', multiple: false,
          types: [{description: 'Insights 已知用法记录', accept: {'text/markdown': ['.md']}}]});
        await read(selected, config.store_id);
        handle = selected;
      }
      if (await handle.requestPermission({mode: 'readwrite'}) !== 'granted') {
        throw new DOMException('Write permission required', 'NotAllowedError');
      }
      return handle;
    }
    async function act(operation, working = '正在保存…') {
      if (busy || !enabled) return;
      generation += 1;
      busy = true;
      refresh();
      status.textContent = working;
      try { await operation(); } catch (error) { failed(error); }
      finally { busy = false; refresh(); }
    }
    connect.addEventListener('click', () => act(async () => {
      const selected = await choose(true);
      adopt((await read(selected, config.store_id)).state);
      status.textContent = '已连接记录文件。选择建议后点击保存更改。';
      announce('已连接记录文件。');
      void remember(config.store_id, selected);
    }, '正在连接记录文件…'));

    for (const button of manageButtons) button.addEventListener('click', () => {
      managing = !managing;
      status.textContent = enabled ? '选择建议后再保存；首次保存时会要求选择记录文件。' : status.textContent;
      refresh(true);
      if (managing) manager.focus();
    });

    cancel.addEventListener('click', () => {
      managing = false;
      refresh(true);
    });

    save.addEventListener('click', () => {
      const changes = controls.filter(isDirty).map(control => ({items: control.items, checked: control.input.checked}));
      if (!changes.length) return;
      void act(async () => {
        const selected = await choose();
        const state = await writeChanges(selected, config.store_id, changes);
        adopt(state);
        status.textContent = '已记录，下次生成将按这些选择过滤建议。';
        announce('已记录 '+changes.length+' 项更改，下次生成时生效。');
        void remember(config.store_id, selected);
      });
    });

    if (enabled) {
      const start = generation;
      void remember(config.store_id).then(async cached => {
        if (!cached || generation !== start) return;
        handle = cached;
        if (await cached.queryPermission({mode: 'readwrite'}) !== 'granted') return;
        const current = await read(cached, config.store_id);
        if (generation !== start) return;
        adopt(current.state);
        status.textContent = '已连接记录文件。选择建议后点击保存更改。';
      }).catch(() => { if (generation === start) handle = null; });
    }

    return {
      add(parent, items) {
        if (!items?.length) return;
        const label = document.createElement('label');
        label.className = 'known-choice';
        const input = document.createElement('input');
        input.type = 'checkbox';
        const labelText = document.createElement('span');
        labelText.textContent = '标记为已知';
        label.append(input, labelText);
        parent.append(label);
        const result = document.createElement('span');
        result.className = 'known-result';
        result.append(document.createTextNode('下次不再推荐 · '));
        const undo = document.createElement('button');
        undo.type = 'button';
        undo.className = 'known-undo';
        undo.textContent = '撤销';
        result.append(undo);
        parent.append(result);
        const control = {input, items, result, undo};
        controls.push(control);
        refresh();
        input.addEventListener('change', () => {
          input.indeterminate = false;
          refresh();
        });
        undo.addEventListener('click', () => {
          void act(async () => {
            const selected = await choose();
            const state = await write(selected, config.store_id, items, false);
            adopt(state);
            status.textContent = '已撤销，这条建议仍可在下次生成时出现。';
            announce('已撤销已知标记。');
            void remember(config.store_id, selected);
          }, '正在撤销…');
        });
      }
    };
  }
  return {parse, update, read, write, writeChanges, mount};
})();
if (typeof module !== 'undefined' && module.exports) module.exports = InsightsFeedback;

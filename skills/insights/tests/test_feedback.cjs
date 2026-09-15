/* File API doubles only; these tests do not grant real browser permissions. */
const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const os = require('node:os');
const path = require('node:path');
const {parse, update, write, writeChanges, mount} = require('../assets/feedback.js');

const store = 'a'.repeat(32);
const first = {id: 'advice-' + '1'.repeat(16), label: '一个具体技巧'};
const second = {id: 'advice-' + '2'.repeat(16), label: '同主题的另一个细节'};
const initial = `<!-- treefolk-insights-known:v1:${store} -->\r\n# 我知道的用法\r\n\r\n保留我的手写笔记。\r\n`;

function fileHandle(file, options = {}) {
  let aborted = false;
  return {
    get aborted() { return aborted; },
    async requestPermission() { return options.denied ? 'denied' : 'granted'; },
    async getFile() {
      const content = await fs.readFile(file, 'utf8');
      return {size: Buffer.byteLength(content), text: async () => content};
    },
    async createWritable(settings) {
      assert.equal(settings.mode, 'exclusive');
      if (options.beforeRead) await options.beforeRead();
      let pending;
      return {
        async write(value) { pending = value; },
        async close() {
          if (options.failClose) throw new Error('disk full');
          await fs.writeFile(file, pending);
        },
        async abort() { aborted = true; }
      };
    }
  };
}

async function fixture(t) {
  const folder = await fs.mkdtemp(path.join(os.tmpdir(), 'insights-feedback-'));
  t.after(() => fs.rm(folder, {recursive: true, force: true}));
  const file = path.join(folder, 'known.md');
  await fs.writeFile(file, initial);
  return file;
}

test('toggle and undo preserve notes, other choices and CRLF', () => {
  const checked = update(update(initial, store, [first], true), store, [second], true);
  const undone = update(checked, store, [first], false);
  assert.ok(undone.startsWith(initial));
  assert.ok(!undone.replaceAll('\r\n', '').includes('\n'));
  assert.equal(parse(undone, store).entries.get(first.id).known, false);
  assert.equal(parse(undone, store).entries.get(second.id).known, true);
  assert.equal(parse(undone, store).entries.size, 2);
});

test('invalid, foreign and duplicate records cannot be rewritten', () => {
  assert.throws(() => update('# unrelated private document', store, [first], true));
  assert.throws(() => parse(initial, 'b'.repeat(32)));
  assert.throws(() => parse(initial + '- [z] bad <!-- insights:' + first.id + ' -->\n'));
  const line = '- [x] label <!-- insights:' + first.id + ' -->\n';
  assert.throws(() => parse(initial + line + line));
  assert.throws(() => update(initial, store, [{...first, label: 'a\nb'}], true));
});

test('save rereads the current file and preserves a newer choice', async t => {
  const file = await fixture(t);
  const handle = fileHandle(file, {beforeRead: () => fs.writeFile(file, update(initial, store, [second], true))});
  await write(handle, store, [first], true);
  const saved = parse(await fs.readFile(file, 'utf8'), store);
  assert.equal(saved.entries.get(first.id).known, true);
  assert.equal(saved.entries.get(second.id).known, true);
});

test('batch save writes every staged choice in one transaction', async t => {
  const file = await fixture(t);
  const handle = fileHandle(file);
  await writeChanges(handle, store, [{items: [first], checked: true}, {items: [second], checked: true}]);
  const saved = parse(await fs.readFile(file, 'utf8'), store);
  assert.equal(saved.entries.get(first.id).known, true);
  assert.equal(saved.entries.get(second.id).known, true);
});

test('close failure and wrong-file errors leave disk unchanged', async t => {
  const file = await fixture(t);
  const handle = fileHandle(file, {failClose: true});
  await assert.rejects(write(handle, store, [first], true), /disk full/);
  assert.equal(handle.aborted, true);
  assert.equal(await fs.readFile(file, 'utf8'), initial);
  const wrong = fileHandle(file);
  await assert.rejects(write(wrong, 'b'.repeat(32), [first], true));
  assert.equal(wrong.aborted, true);
  assert.equal(await fs.readFile(file, 'utf8'), initial);
});

class Element {
  children = [];
  events = {};
  textContent = '';
  dataset = {};
  hidden = false;
  disabled = false;
  checked = false;
  indeterminate = false;
  attributes = {};
  classList = {toggle: () => {}};
  append(...items) { this.children.push(...items); }
  addEventListener(event, callback) { this.events[event] = callback; }
  setAttribute(name, value) { this.attributes[name] = value; }
  focus() {}
}

async function waitFor(check) {
  for (let i = 0; i < 100 && !check(); i++) await new Promise(resolve => setTimeout(resolve, 2));
}

test('selection stays local until save; failures preserve the draft and disk', async t => {
  const file = await fixture(t);
  const originals = ['document', 'isSecureContext', 'showOpenFilePicker'].map(key => [key, Object.getOwnPropertyDescriptor(globalThis, key)]);
  t.after(() => { for (const [key, descriptor] of originals) descriptor ? Object.defineProperty(globalThis, key, descriptor) : delete globalThis[key]; });
  for (const mode of ['cancel', 'denied', 'failClose', 'saved']) {
    await fs.writeFile(file, initial);
    const ids = ['feedback-status', 'feedback-path', 'feedback-connect', 'feedback-manager', 'feedback-selection', 'feedback-save', 'feedback-cancel', 'feedback-toast'];
    const elements = new Map(ids.map(id => [id, new Element()]));
    const manage = new Element();
    globalThis.document = {
      body: new Element(),
      getElementById: id => elements.get(id),
      querySelectorAll: selector => selector === '[data-feedback-manage]' ? [manage] : [],
      createElement: () => new Element(),
      createTextNode: text => text
    };
    globalThis.isSecureContext = true;
    let pickerCalls = 0;
    globalThis.showOpenFilePicker = async () => {
      pickerCalls += 1;
      if (mode === 'cancel') throw new DOMException('cancel', 'AbortError');
      return [fileHandle(file, {[mode]: true})];
    };
    const parent = new Element();
    mount({status: 'ready', path: file, store_id: store, known: []}).add(parent, [first]);
    const checkbox = parent.children[0].children[0];
    manage.events.click();
    assert.equal(elements.get('feedback-manager').hidden, false);
    checkbox.checked = true;
    checkbox.events.change();
    assert.equal(pickerCalls, 0);
    assert.equal(elements.get('feedback-save').disabled, false);
    elements.get('feedback-save').events.click();
    assert.equal(elements.get('feedback-save').disabled, true);
    await waitFor(() => !elements.get('feedback-status').textContent.startsWith('正在'));
    assert.equal(pickerCalls, 1);
    assert.equal(checkbox.checked, true);
    assert.equal(elements.get('feedback-status').textContent.startsWith('已记录'), mode === 'saved');
    if (mode !== 'saved') assert.equal(await fs.readFile(file, 'utf8'), initial);
    elements.get('feedback-cancel').events.click();
    assert.equal(elements.get('feedback-manager').hidden, true);
    assert.equal(checkbox.checked, mode === 'saved');
  }
});

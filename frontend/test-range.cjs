const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const { transformSync } = require('esbuild');
const React = require('react');
const { renderToStaticMarkup } = require('react-dom/server');

const source = fs.readFileSync('src/RangeField.jsx', 'utf8');
const compiled = transformSync(source, {loader:'jsx', format:'cjs'}).code;
const loaded = {exports:{}};
new Function('require', 'module', 'exports', compiled)(require, loaded, loaded.exports);
const { RangeField } = loaded.exports;
const props = {label:'Glucose', unit:'mg/dL', min:0, max:600, step:0.01, value:'', onChange:() => {}};

test('unselected range starts unconfirmed and has accessible label', () => {
  const html = renderToStaticMarkup(React.createElement(RangeField, props));
  assert.match(html, /type="range"/);
  assert.match(html, /Chưa chọn/);
  assert.match(html, /aria-label="Glucose"/);
});

test('pointer and keyboard explicitly confirm value', () => {
  const chosen = [];
  const node = RangeField({...props, onChange: value => chosen.push(value)});
  const slider = node.props.children[1].props.children[1];
  slider.props.onPointerDown({currentTarget:{value:'0'}});
  slider.props.onKeyDown({key:'Home', currentTarget:{value:'0'}});
  assert.deepEqual(chosen, ['0', '0']);
});

test('step buttons preserve precision and respect endpoints', () => {
  const chosen = [];
  const node = RangeField({...props, min:0, max:3, step:0.001, value:'0.123', onChange: value => chosen.push(value)});
  const controls = node.props.children[1].props.children;
  controls[0].props.onClick(); controls[2].props.onClick();
  assert.deepEqual(chosen, ['0.122', '0.124']);
  const edge = RangeField({...props, value:'600', onChange: value => chosen.push(value)});
  edge.props.children[1].props.children[2].props.onClick();
  assert.equal(chosen.at(-1), '600.00');
});

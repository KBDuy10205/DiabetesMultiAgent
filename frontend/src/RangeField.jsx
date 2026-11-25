import React from 'react';

export function RangeField({ label, unit, min, max, step, value, onChange }) {
  const display = value === '' ? 'Chưa chọn' : `${Number(value).toLocaleString('vi-VN', {maximumFractionDigits: 3})} ${unit}`;
  const confirmCurrent = event => { if (value === '') onChange(event.currentTarget.value); };
  const adjust = direction => {
    const precision = (String(step).split('.')[1] || '').length;
    const current = value === '' ? min : Number(value);
    const next = Math.max(min, Math.min(max, current + direction * step));
    onChange(next.toFixed(precision));
  };
  return <div className="field range-field"><div className="range-heading"><span>{label} <b>*</b></span><strong className={value === '' ? 'range-value unselected' : 'range-value'}>{display}</strong></div><div className="range-control"><button type="button" className="range-step" onClick={() => adjust(-1)} aria-label={`Giảm ${label}`}>−</button><input type="range" min={min} max={max} step={step} value={value === '' ? min : value} onPointerDown={confirmCurrent} onKeyDown={event => { if (['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown', 'Home', 'End', 'PageUp', 'PageDown'].includes(event.key)) confirmCurrent(event); }} onChange={event => onChange(event.target.value)} aria-label={label} aria-valuetext={display}/><button type="button" className="range-step" onClick={() => adjust(1)} aria-label={`Tăng ${label}`}>+</button></div><div className="range-ends"><span>{min} {unit}</span><span>{max} {unit}</span></div></div>;
}

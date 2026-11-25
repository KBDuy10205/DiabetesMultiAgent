import React, { useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { RangeField } from './RangeField.jsx';
import './style.css';

const FIELDS = [
  ['Pregnancies', 'Số lần mang thai', 'lần', 0, 20, 1], ['Glucose', 'Glucose huyết tương', 'mg/dL', 0, 600, 0.01],
  ['BloodPressure', 'Huyết áp tâm trương', 'mmHg', 0, 250, 0.01], ['SkinThickness', 'Độ dày nếp gấp da', 'mm', 0, 150, 0.01],
  ['Insulin', 'Insulin huyết thanh', 'µU/mL', 0, 1000, 0.01], ['BMI', 'Chỉ số BMI', 'kg/m²', 0, 100, 0.01],
  ['DiabetesPedigreeFunction', 'Chỉ số phả hệ tiểu đường', 'DPF', 0, 3, 0.001], ['Age', 'Tuổi', 'năm', 0, 120, 1],
];
const SECTIONS = [
  ['assessment', 'Đánh giá', '◈'], ['result', 'Kết quả', '▤'], ['chat', 'Hỏi đáp', '✳'], ['history', 'Lịch sử', '◷'],
];
const errors = {invalid_features:'Vui lòng nhập đủ 8 chỉ số hợp lệ.', invalid_measurement:'Vui lòng kiểm tra kết quả glucose.', assessment_unavailable:'Không thể đánh giá lúc này. Vui lòng thử lại.', chat_unavailable:'Không thể kết nối dịch vụ hỏi đáp.', llm_consent_required:'Cần đồng ý gửi câu hỏi và tài liệu tới dịch vụ AI.', history_unavailable:'Không thể mở lịch sử.', invalid_session:'Phiên trình duyệt không hợp lệ.'};

function sessionToken() {
  const key = 'duongnet_session';
  let token = localStorage.getItem(key);
  if (!/^[0-9a-f]{64}$/.test(token || '')) {
    token = Array.from(crypto.getRandomValues(new Uint8Array(32)), x => x.toString(16).padStart(2, '0')).join('');
    localStorage.setItem(key, token);
  }
  return token;
}
async function api(path, options = {}) {
  const response = await fetch(path, { ...options, headers: { 'Content-Type': 'application/json', 'X-Session-Token': sessionToken() }, cache: 'no-store' });
  const data = await response.json();
  if (!response.ok) throw new Error(errors[data.error] || 'Yêu cầu không hợp lệ hoặc dịch vụ chưa sẵn sàng.');
  return data;
}
function Icon({ name, size = 20 }) {
  const props = { width: size, height: size, viewBox:'0 0 24 24', fill:'none', stroke:'currentColor', strokeWidth:'1.7', strokeLinecap:'round', strokeLinejoin:'round', 'aria-hidden':true };
  if (name === 'spark') return <svg {...props}><path d="m12 3 1.7 5.3L19 10l-5.3 1.7L12 17l-1.7-5.3L5 10l5.3-1.7L12 3Z"/><path d="M19 16v4M17 18h4M5 17v3M3.5 18.5h3"/></svg>;
  if (name === 'shield') return <svg {...props}><path d="M12 22s7-3.2 7-10V5l-7-3-7 3v7c0 6.8 7 10 7 10Z"/><path d="m9 12 2 2 4-4"/></svg>;
  if (name === 'heart') return <svg {...props}><path d="M20.5 8.7c0 4.5-8.5 10-8.5 10s-8.5-5.5-8.5-10a4.5 4.5 0 0 1 8-2.8l.5.6.5-.6a4.5 4.5 0 0 1 8 2.8Z"/></svg>;
  return <svg {...props}><path d="M5 12h14M12 5v14"/></svg>;
}
function SourceList({ sources = [] }) {
  if (!sources.length) return <p className="quiet">Chưa có nguồn tài liệu được truy xuất.</p>;
  return <div className="sources">{sources.map((s, i) => <div className="source" key={`${s.chunk_id}-${i}`}><span className="source-tag">{s.citation}</span><div><strong>{s.title}</strong><small>{s.section_path?.join(' / ') || 'Tài liệu tham khảo'} · {s.chunk_id}</small>{s.url && <a href={s.url} target="_blank" rel="noreferrer">Xem nguồn gốc</a>}</div></div>)}</div>;
}
function ResultCard({ result }) {
  const s = result?.summary;
  if (!s) return <div className="empty"><div className="empty-icon"><Icon name="heart" size={26}/></div><h3>Chưa có kết quả</h3><p>Hoàn thành thông tin ở phần đánh giá để xem kết quả tại đây.</p></div>;
  const hasPrediction = s.prediction_status === 'ok' && Number.isFinite(s.probability);
  return <div className="result-grid"><div className="result-main"><span className="eyebrow">KẾT QUẢ THAM KHẢO</span><h2>{hasPrediction ? 'Ước tính từ mô hình' : 'Chưa thể đưa ra ước tính'}</h2><p className="muted">{hasPrediction ? 'Điểm số phản ánh đầu ra của mô hình học máy trên bộ dữ liệu Pima.' : 'Bước kiểm tra an toàn chưa cho phép chạy mô hình. Vui lòng xem thông báo bên dưới.'}</p>{hasPrediction && <><div className="score">{(s.probability * 100).toFixed(1)}<span>%</span></div><progress className="score-progress" value={s.probability} max="1" aria-label="Điểm số tham khảo"/><p className="small-note">Đây không phải xác suất đã được kiểm định cho cá nhân bạn.</p></>}</div><div className="result-side"><span className="eyebrow">CẦN LƯU Ý</span><h3>Đọc kết quả đúng cách</h3><p>Kết quả phục vụ học tập và tham khảo, không xác nhận hay loại trừ bệnh tiểu đường.</p><p>Mô hình chưa được kiểm định lâm sàng. Hãy trao đổi với bác sĩ về các chỉ số của bạn.</p>{result.saved && <div className="saved">✓ Đã lưu bản tóm tắt trên thiết bị này</div>}</div>{s.alerts?.map(a => <div className="alert alert-danger" key={a.rule_id}><strong>Cảnh báo an toàn</strong><p>{a.message}</p></div>)}{s.issues?.length > 0 && <div className="alert alert-warning"><strong>Thông tin cần kiểm tra</strong><p>{s.issues.map(x => `${x.field || 'xét nghiệm'}: ${x.code}`).join(' · ')}</p></div>}</div>;
}
function App() {
  const [page, setPage] = useState('assessment');
  const [features, setFeatures] = useState(Object.fromEntries(FIELDS.map(([key]) => [key, ''])));
  const [glucose, setGlucose] = useState('');
  const [save, setSave] = useState(false);
  const [result, setResult] = useState(null);
  const [lastInput, setLastInput] = useState(null);
  const [explainConsent, setExplainConsent] = useState(false);
  const [explanation, setExplanation] = useState(null);
  const [history, setHistory] = useState([]);
  const [question, setQuestion] = useState('');
  const [share, setShare] = useState(false);
  const [conversation, setConversation] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => { if (page === 'history') { setError(''); api('/api/history').then(x => setHistory(x.history)).catch(e => setError(e.message)); } }, [page]);
  const navigate = p => { setError(''); setPage(p); };
  async function submitAssessment(event) {
    event.preventDefault(); setError('');
    if (FIELDS.some(([key]) => features[key] === '' || !Number.isFinite(Number(features[key])) || Number(features[key]) < 0) || glucose === '' || !Number.isFinite(Number(glucose)) || Number(glucose) <= 0) { setError('Hãy chọn đầy đủ các chỉ số và kết quả glucose lớn hơn 0.'); return; }
    setBusy(true);
    try {
      const payload = { features: Object.fromEntries(FIELDS.map(([key]) => [key, Number(features[key])])), measurement: { test_type:'glucose_meter', value:Number(glucose), unit:'mg/dL' }, save_history:save };
      const data = await api('/api/assess', {method:'POST', body:JSON.stringify(payload)});
      setResult(data.result); setLastInput({features:payload.features, measurement:payload.measurement}); setExplanation(null); setExplainConsent(false); setPage('result');
    } catch (e) { setError(e.message); } finally { setBusy(false); }
  }
  async function submitChat(event) {
    event.preventDefault(); setError('');
    if (!question.trim() || !share) { setError('Hãy nhập câu hỏi và xác nhận đồng ý gửi dữ liệu tới Gemini.'); return; }
    setBusy(true); setConversation(null);
    try { const data = await api('/api/chat', {method:'POST', body:JSON.stringify({question:question.trim(), share_with_llm:share})}); setConversation({question, ...data.result}); }
    catch (e) { setError(e.message); } finally { setBusy(false); }
  }
  async function requestExplanation() {
    setError('');
    if (!lastInput || !explainConsent) { setError('Hãy xác nhận đồng ý trước khi gửi kết quả tới Gemini.'); return; }
    setBusy(true); setExplanation(null);
    try { const data = await api('/api/explain', {method:'POST', body:JSON.stringify({...lastInput, share_with_llm:true})}); setExplanation(data.result); }
    catch (e) { setError(e.message); } finally { setBusy(false); }
  }
  async function clearHistory() {
    if (!window.confirm('Xóa tất cả lịch sử của trình duyệt này? Thao tác này không thể hoàn tác.')) return;
    setError('');
    try { await api('/api/history', {method:'DELETE'}); setHistory([]); }
    catch (e) { setError(e.message); }
  }

  return <div className="app-shell"><aside className="sidebar"><div className="brand"><div className="brand-mark"><Icon name="heart" size={22}/></div><div><strong>đường nét</strong><span>CHĂM SÓC TỪ HIỂU BIẾT</span></div></div><div className="side-caption">KHÔNG GIAN CỦA BẠN</div><nav aria-label="Điều hướng chính">{SECTIONS.map(([id, label, glyph]) => <button key={id} onClick={() => navigate(id)} className={page === id ? 'nav-item active':'nav-item'} aria-current={page === id ? 'page':undefined}><span className="nav-icon">{glyph}</span>{label}</button>)}</nav><div className="sidebar-bottom"><div className="side-note-icon"><Icon name="shield"/></div><strong>Thông tin của bạn</strong><p>Dữ liệu chỉ được lưu khi bạn đồng ý.</p><span className="local-pill"><i/>Ứng dụng cục bộ</span></div></aside>
  <div className="main-area"><header className="topbar"><div className="crumb">Không gian sức khỏe <span>/</span> <strong>{SECTIONS.find(x => x[0] === page)?.[1]}</strong></div><div className="top-tag"><Icon name="shield" size={16}/> Riêng tư theo lựa chọn</div></header><main className="content"><div className="mobile-brand">đường nét <span>· hỗ trợ sức khỏe</span></div>
  {page === 'assessment' && <><div className="page-heading"><div><div className="eyebrow"><span className="dot"/> GÓC SỨC KHỎE CỦA BẠN</div><h1>Hiểu hơn về <em>nguy cơ của bạn.</em></h1><p>Kéo các thanh để chọn chỉ số có sẵn và nhận thông tin tham khảo từ mô hình.</p></div><div className="heading-icon"><Icon name="heart" size={29}/></div></div><div className="info-banner"><div className="banner-icon"><Icon name="shield"/></div><div><strong>Một lưu ý nhỏ trước khi bắt đầu</strong><p>Đây là công cụ học tập và hỗ trợ tham khảo, không thay thế chẩn đoán hay tư vấn từ bác sĩ.</p></div></div><form onSubmit={submitAssessment}><section className="card form-card"><div className="card-heading"><div className="section-icon"><Icon name="spark"/></div><div><h2>Thông tin sức khỏe</h2><p>Kéo hoặc nhấn vào từng thanh để chọn đúng chỉ số của bạn.</p></div><span className="required-badge">Tất cả đều bắt buộc</span></div><div className="divider"/><div className="fields-grid">{FIELDS.map(([key, label, unit, min, max, step]) => <RangeField key={key} label={label} unit={unit} min={min} max={max} step={step} value={features[key]} onChange={value => setFeatures(previous => ({...previous, [key]:value}))}/>)}</div><div className="helper">Phạm vi thanh kéo chỉ phục vụ nhập liệu, không phải giới hạn y khoa. Nếu chỉ số của bạn nằm ngoài phạm vi, không chọn giá trị gần nhất hay dùng kết quả đánh giá. Một số giá trị 0 trong bộ Pima được xử lý là dữ liệu thiếu.</div><div className="divider"/><div className="subheading"><div><h3>Kiểm tra an toàn trước đánh giá</h3><p>Chọn kết quả glucose đo cá nhân để kiểm tra cảnh báo thấp.</p></div><span className="mini-shield"><Icon name="shield"/></span></div><div className="safety-field"><RangeField label="Glucose đo cá nhân" unit="mg/dL" min={0.01} max={600} step={0.01} value={glucose} onChange={setGlucose}/></div><div className="divider"/><label className="consent"><input type="checkbox" checked={save} onChange={e=>setSave(e.target.checked)}/><span><strong>Lưu bản tóm tắt vào lịch sử</strong><small>Không lưu các chỉ số đầu vào. Lịch sử lưu cục bộ, chưa mã hóa; người có quyền truy cập máy có thể đọc.</small></span></label>{error && <div className="form-error" role="alert">{error}</div>}<div className="form-footer"><span><Icon name="shield" size={16}/> Thông tin chỉ được xử lý theo lựa chọn của bạn</span><button className="primary-button" disabled={busy}>{busy ? 'Đang đánh giá…' : 'Xem đánh giá'}</button></div></section></form></>}
  {page === 'result' && <><div className="page-heading compact"><div><div className="eyebrow"><span className="dot"/> KẾT QUẢ CỦA BẠN</div><h1>Thông tin <em>tham khảo.</em></h1><p>Một góc nhìn để bạn chuẩn bị cho cuộc trao đổi với nhân viên y tế.</p></div></div><ResultCard result={result}/>{result && <section className="card answer-card"><div className="answer-head"><div className="section-icon"><Icon name="spark"/></div><div><span className="eyebrow">GIẢI THÍCH CÓ DẪN NGUỒN</span><h2>Hiểu thêm về kết quả</h2></div></div><p className="muted">Tìm tài liệu liên quan và yêu cầu Gemini giải thích ý nghĩa, giới hạn của kết quả tham khảo.</p><label className="consent chat-consent"><input type="checkbox" checked={explainConsent} onChange={e=>setExplainConsent(e.target.checked)}/><span><strong>Tôi đồng ý gửi kết quả đánh giá và tài liệu tới Google Gemini</strong><small>Kết quả suy ra từ thông tin sức khỏe là dữ liệu nhạy cảm. Chỉ chọn nếu bạn chấp nhận chia sẻ với dịch vụ bên ngoài.</small></span></label>{error && <div className="form-error" role="alert">{error}</div>}<button className="outline-button" onClick={requestExplanation} disabled={busy}>{busy ? 'Đang tìm tài liệu…' : 'Giải thích kết quả'}</button>{explanation && <><p className="answer-text">{explanation.answer || 'Chưa thể tạo giải thích lúc này.'}</p>{(!explanation.valid || explanation.status !== 'draft') && <div className="alert alert-warning"><strong>Chưa có giải thích được kiểm tra</strong><p>Trạng thái: {explanation.status}.</p></div>}<div className="divider"/><h3>Nguồn tham khảo</h3><SourceList sources={explanation.sources}/></>}</section>}<div className="action-row"><button className="outline-button" onClick={()=>navigate('assessment')}>Cập nhật thông tin</button><button className="primary-button" onClick={()=>navigate('chat')}>Đặt câu hỏi kiến thức</button></div></>}
  {page === 'chat' && <><div className="page-heading compact"><div><div className="eyebrow"><span className="dot"/> KHÔNG GIAN HỎI ĐÁP</div><h1>Cùng tìm hiểu <em>rõ hơn.</em></h1><p>Đặt câu hỏi chung về bệnh tiểu đường và xem các nguồn được truy xuất.</p></div></div><section className="card chat-card"><div className="chat-intro"><div className="section-icon"><Icon name="spark"/></div><div><h2>Hỏi đáp kiến thức</h2><p>Trợ lý tìm tài liệu liên quan trước khi tổng hợp câu trả lời.</p></div></div><div className="info-inline">Không nhập tên, số điện thoại hoặc thông tin sức khỏe cá nhân. Câu hỏi và đoạn tài liệu sẽ được gửi tới Google Gemini khi bạn đồng ý.</div><form onSubmit={submitChat}><label className="field"><span>Câu hỏi của bạn</span><textarea value={question} onChange={e=>setQuestion(e.target.value)} maxLength={1000} placeholder="Ví dụ: Tài liệu nói gì về những dấu hiệu thường gặp?" rows="4"/></label><label className="consent chat-consent"><input type="checkbox" checked={share} onChange={e=>setShare(e.target.checked)}/><span><strong>Tôi đồng ý gửi câu hỏi và tài liệu tới Google Gemini</strong><small>Không gửi nếu bạn không muốn chia sẻ nội dung với dịch vụ bên ngoài.</small></span></label>{error && <div className="form-error" role="alert">{error}</div>}<button className="primary-button" disabled={busy}>{busy ? 'Đang tìm tài liệu…' : 'Gửi câu hỏi'}</button></form></section>{conversation && <section className="card answer-card"><div className="answer-head"><div className="section-icon"><Icon name="spark"/></div><div><span className="eyebrow">PHẢN HỒI THAM KHẢO</span><h2>{conversation.question}</h2></div></div><p className="answer-text">{conversation.answer || 'Chưa thể tạo câu trả lời lúc này.'}</p>{(!conversation.valid || conversation.status !== 'draft') && <div className="alert alert-warning"><strong>Chưa có câu trả lời được xác thực</strong><p>Dịch vụ AI hoặc bước kiểm tra có thể chưa hoàn tất. Trạng thái: {conversation.status}.</p></div>}<div className="divider"/><h3>Nguồn tham khảo</h3><SourceList sources={conversation.sources}/></section>}</>}
  {page === 'history' && <><div className="page-heading compact"><div><div className="eyebrow"><span className="dot"/> DỮ LIỆU CỦA BẠN</div><h1>Nhìn lại <em>hành trình.</em></h1><p>Các bản tóm tắt bạn đã chọn lưu trên trình duyệt này.</p></div></div><section className="card history-card"><div className="card-heading"><div className="section-icon"><span className="nav-icon">◷</span></div><div><h2>Lịch sử đánh giá</h2><p>Tối đa 100 bản gần nhất. Không bao gồm chỉ số đầu vào.</p></div></div><div className="divider"/>{error ? <div className="form-error" role="alert">{error}</div> : !history.length ? <div className="empty"><div className="empty-icon">◷</div><h3>Chưa có lịch sử</h3><p>Khi chọn lưu bản tóm tắt, bạn sẽ thấy kết quả tại đây.</p><button className="outline-button" onClick={()=>navigate('assessment')}>Bắt đầu đánh giá</button></div> : <><div className="history-list">{history.map(row=><div className="history-row" key={row.id}><div className="history-symbol"><Icon name="heart" size={17}/></div><div className="history-date"><strong>Đánh giá tham khảo</strong><span>{new Date(row.created_at).toLocaleString('vi-VN')}</span></div><div className="history-value">{typeof row.summary.probability === 'number' ? `${(row.summary.probability*100).toFixed(1)}%` : 'Chưa có điểm'}<small>{row.summary.alerts?.length ? 'Có cảnh báo' : 'Bản tóm tắt'}</small></div></div>)}</div><div className="action-row"><button className="outline-button" onClick={clearHistory}>Xóa lịch sử trình duyệt này</button></div></>}</section><p className="privacy-footnote"><Icon name="shield" size={15}/> Lịch sử gắn với mã lưu trên trình duyệt; nếu xóa dữ liệu trình duyệt, bạn có thể không truy cập lại được.</p></>}
  <footer><span>ĐƯỜNG NÉT <b>·</b> CHĂM SÓC TỪ HIỂU BIẾT</span><span>Thông tin tham khảo, không thay thế bác sĩ.</span></footer></main></div></div>;
}

createRoot(document.getElementById('root')).render(<App/>);

'use client';

import { useCallback, useEffect, useRef, useState, type FormEvent } from 'react';
import { safeEvidenceUrl } from '@/src/admin/aiSearchWeeklyUrl';
import './weekly.css';

type Evidence = Record<string, unknown>;
type Batch = { id: string; display_number: string; grouping_status: string; document: Evidence };
type Contact = { channel: string; status: string; actor: string; checked_at?: string; sent_at?: string; replied_at?: string; evidence_url?: string; evidence_reference?: string; cumulative_count?: number; reason?: string };
type Evaluation = Evidence & { candidate_name?: string; candidate_name_reason?: string; education?: string; experience?: string; key_experience?: string; profile_url?: string; score?: number; score_status: string; why_fit?: string[]; human_followup?: string; source_reported_score?: number; source_message_id: string };
type Row = { candidate_id: string; position_id: string; week_id: string; company: string; position: string; evaluation: Evaluation; batches: Batch[]; contacts: Contact[]; confirmed_uncontacted?: boolean };
type Weekly = { rows: Row[]; total: number; complete: boolean; summary: Record<string, number | string | null> };
type Week = { week_id: string; start_date: string; end_date: string };
type Index = { weeks: Week[]; high_score_threshold: number | null };
type Collection = { complete: boolean; run: { last_success_at?: string; scopes?: Record<string, { pages: number; exhausted: boolean; message_ids?: string[] }> } | null; review_count: number; failed_count: number };
const CHANNELS = ['SARAMIN','JOBKOREA','LINKEDIN','GMAIL'] as const;
const LABELS: Record<string,string> = { SARAMIN: '사람인', JOBKOREA: '잡코리아', LINKEDIN: 'LinkedIn', GMAIL: 'Gmail/JD', CONTACTED: '발송 확인', REPLIED: '회신 확인', CONFIRMED_NOT_CONTACTED: '미발송 확인', NOT_RUN: '확인 필요', REVIEW_REQUIRED: '연결 대기', FAILED: '조회 실패' };
const API = '/api/admin/ai-search/';

async function read<T>(path: string, signal?: AbortSignal): Promise<T> {
  const response = await fetch(API + path, { cache: 'no-store', ...(signal ? { signal } : {}) });
  if (!response.ok) throw new Error(response.status === 401 ? '관리자 로그인이 필요합니다.' : `자료 조회 실패 (HTTP ${response.status})`);
  return response.json() as Promise<T>;
}
function value(item: unknown): string {
  if (item === null || item === undefined || item === '') return 'NOT_RUN · 원문 근거 없음';
  return typeof item === 'object' ? JSON.stringify(item, null, 2) : String(item);
}
function date(value?: string) { return value ? new Date(value).toLocaleString('ko-KR', { timeZone: 'Asia/Seoul' }) : '미확인'; }
function EvidenceLink({ href, children }: { href: unknown; children: React.ReactNode }) {
  const safe = safeEvidenceUrl(href);
  return safe ? <a href={safe} target="_blank" rel="noopener noreferrer">{children}</a> : <span>프로필 확인 필요</span>;
}
function ContactCell({ row, channel }: { row: Row; channel: string }) {
  const events = row.contacts.filter(c => c.channel === channel);
  const ranked = [...events].sort((a,b) => {
    const order = ['REPLIED','CONTACTED','FAILED','REVIEW_REQUIRED','CONFIRMED_NOT_CONTACTED','NOT_RUN'];
    return order.indexOf(a.status) - order.indexOf(b.status);
  });
  const last = ranked[0];
  if (!last) return <td className="pending">확인 필요<small>NOT_RUN · 채널 이력 미확인</small></td>;
  const positives = events.filter(e => ['CONTACTED','REPLIED'].includes(e.status));
  return <td data-status={last.status}>
    {LABELS[last.status]} · {last.actor === 'OWNER' ? '대표님' : last.actor}
    <small>확인 {date(last.checked_at)}</small><small>발송 {date(last.sent_at)} · 누적 {positives.length}건</small>
    {last.evidence_url && <EvidenceLink href={last.evidence_url}>근거 ↗</EvidenceLink>}
    <small>{last.evidence_reference}</small>
  </td>;
}

function RawDetail({ detail }: { detail: Evidence }) {
  const evaluations = detail.evaluations as Evaluation[] | null;
  const contacts = detail.contacts as Contact[] | null;
  const messages = detail.source_messages as Evidence[] | null;
  return <div className="raw-content">
    <h3>후보 식별과 정규화</h3><pre>{value(detail.candidate)}</pre>
    {evaluations?.map((e,i) => <section key={i}>
      <h3>포지션별 평가 · {value(e.position_id)}</h3>
      <dl className="raw-fields">{[
        ['후보명 상태',e.candidate_name_status],['후보명',e.candidate_name],['후보명 사유',e.candidate_name_reason],
        ['학력',e.education],['전체 경력',e.experience],['핵심 경력',e.key_experience],
        ['필수요건별 근거',e.requirements_evidence],['적합 근거',e.why_fit],
        ['더 적합한 포지션 검토',e.better_position_exists],['대안 포지션',e.better_position],
        ['검토 사유',e.better_position_reason],['검증 점수',e.score],['점수 상태',e.score_status],
        ['누락 항목',e.missing_components],['점수 근거',e.score_reason],
        ['메일 원본 점수',e.source_reported_score],['메일 점수 라벨',e.source_score_label],['메일 점수 rubric',e.source_score_rubric],
        ['평가 버전',e.evaluation_version],['계산 버전',e.calculation_version],['입력 hash',e.score_input_hash],
        ['평가시각',e.evaluated_at],['사람 후속 조치',e.human_followup],['후속 조치 확인',e.human_followup_reason],
        ['컨택 의견 근거',e.contact_opinion_evidence],
      ].map(([label,entry]) => <div key={String(label)}><dt>{String(label)}</dt><dd>{value(entry)}</dd></div>)}</dl>
      <EvidenceLink href={e.profile_url}>프로필 ↗</EvidenceLink>
      <h4>계약 점수 구성 4개</h4>
      <dl className="raw-fields">{['education','job_fit','difficult_work','job_description_logic'].map(axis =>
        <div key={axis}><dt>{axis}</dt><dd>{value((e.score_components as Evidence | null)?.[axis])}</dd></div>)}</dl>
      <h4>후보 관련 원문 구간</h4><pre>{value(e.source_segment)}</pre>
    </section>)}
    <h3>모든 고객사·포지션 이력</h3><pre>{value(detail.positions)}</pre>
    <h3>모든 Batch · 실행 주체 · 실행시각 · 수신시각</h3><pre>{value(detail.batches)}</pre>
    {CHANNELS.map(channel => <section key={channel}><h3>{LABELS[channel]} 컨택 이력·출처·확인시각</h3>
      <pre>{value(contacts?.filter(c => c.channel === channel))}</pre></section>)}
    <h3>Gmail 원문 · parser version</h3>
    {messages?.map((m,i) => <section key={i}><EvidenceLink href={m.gmail_url}>Gmail 원문 ↗</EvidenceLink>
      <p>parser {value(m.parser_version)} · 수신 {value(m.received_at)}</p></section>)}
    <h3>검토 대기 사유</h3><pre>{value(detail.review_queue)}</pre>
  </div>;
}

export default function AiSearchWeekly() {
  const [index,setIndex] = useState<Index | null>(null);
  const [collection,setCollection] = useState<Collection | null>(null);
  const [week,setWeek] = useState('');
  const [filters,setFilters] = useState('');
  const [offset,setOffset] = useState(0);
  const [data,setData] = useState<Weekly | null>(null);
  const [error,setError] = useState('');
  const [loading,setLoading] = useState(true);
  const [modal,setModal] = useState<{ title: string; detail?: Evidence; rows?: Row[]; error?: string } | null>(null);
  const dialog = useRef<HTMLDialogElement>(null);
  const loadIndex = useCallback(async () => {
    try {
      const [weeks,status] = await Promise.all([read<Index>('weeks'),read<Collection>('collection-status')]);
      setIndex(weeks); setCollection(status);
      setWeek(current => current === '' ? (weeks.weeks[0]?.week_id || '') : current);
    } catch (e) { setError(e instanceof Error ? e.message : '조회 실패'); setLoading(false); }
  },[]);
  useEffect(() => { void loadIndex(); },[loadIndex]);
  useEffect(() => {
    if (!week) return;
    const controller = new AbortController();
    setLoading(true); setError(''); setData(null);
    read<Weekly>(`weekly/${week}?limit=50&offset=${offset}&${filters}`,controller.signal)
      .then(setData).catch((e: unknown) => { if (!controller.signal.aborted) setError(e instanceof Error ? e.message : '조회 실패'); })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  },[week,filters,offset]);
  useEffect(() => { if (modal) dialog.current?.showModal(); },[modal]);
  const selected = index?.weeks.find(w => w.week_id === week);
  function filter(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); const form = new FormData(event.currentTarget); const query = new URLSearchParams();
    for (const [key,entry] of form) if (typeof entry === 'string' && entry) query.set(key,entry);
    setFilters(query.toString()); setOffset(0);
  }
  async function raw(candidate: string) {
    setModal({ title: '후보 상세 Raw' });
    try { setModal({ title: '후보 상세 Raw', detail: await read<Evidence>(`candidates/${candidate}`) }); }
    catch(e) { setModal({ title: '후보 상세 Raw', error: e instanceof Error ? e.message : '조회 실패' }); }
  }
  async function highScore() {
    setModal({ title: '고점수 미컨택자' });
    try {
      const result = await read<Weekly>(`high-score-uncontacted?week=${week}&${filters}`);
      setModal({ title: '고점수 미컨택자', rows: result.rows,
        ...(!result.complete || result.summary.high_score_uncontacted === null ? { error: 'NOT_RUN · 점수 또는 채널별 이력 확인이 완료되지 않았습니다.' } : {}) });
    } catch(e) { setModal({ title: '고점수 미컨택자', error: e instanceof Error ? e.message : '조회 실패' }); }
  }
  return <main className="ai-weekly" aria-busy={loading}>
    <header className="ai-weekly-heading"><div><p className="eyebrow">WEEKLY OPERATIONS / ASIA·SEOUL</p>
      <h1>AI Search 주간 운영표</h1><p>실행과 후보, 채널별 컨택을 원문 근거로 확인합니다.</p></div>
      <div className="collection-note"><strong>{collection?.complete ? '수집 완료' : '수집 확인 필요'}</strong>
        <span>마지막 성공 {date(collection?.run?.last_success_at)}</span>
        <span>Inbox ∪ 02aisearch · 검토 {collection?.review_count === undefined ? '미확인' : collection.review_count} · 실패 {collection?.failed_count === undefined ? '미확인' : collection.failed_count}</span>
        {collection?.run?.scopes && Object.entries(collection.run.scopes).map(([scope,s]) => <span key={scope}>{scope} · pagination {s.exhausted ? '종료' : '미종료'} · {s.pages}페이지</span>)}
      </div></header>
    <nav className="week-buttons" aria-label="최근 4개 운영 주차">{index?.weeks.map(w =>
      <button type="button" key={w.week_id} aria-pressed={week === w.week_id} onClick={() => { setWeek(w.week_id); setOffset(0); }}>
        {w.week_id.replace('-',' ')}<small>{w.start_date.slice(5).replace('-','.')}~{w.end_date.slice(5).replace('-','.')}</small>
      </button>)}</nav>
    <p className="week-range">{selected && `${selected.week_id} · ${selected.start_date}~${selected.end_date} · 일요일 00:00 이상, 다음 일요일 00:00 미만`}</p>
    <div className="weekly-summary" aria-label="선택 범위 집계">
      {([['batches','Batch'],['positions','포지션'],['candidates','총 후보'],['jd_sent','JD 발송']] as const).map(([key,label]) =>
        <div key={key}><span>{label}</span><strong>{typeof data?.summary[key] === 'number' ? data.summary[key].toLocaleString() : '미확인'}</strong></div>)}
      <button type="button" onClick={() => void highScore()}><span>고점수 미컨택자{index?.high_score_threshold ? ` · ${index.high_score_threshold}점 이상` : ''}</span>
        <strong>{typeof data?.summary.high_score_uncontacted === 'number' ? data.summary.high_score_uncontacted.toLocaleString() : '미확인'} ↗</strong></button>
    </div>
    {data?.summary.reason && <p className="status-note">NOT_RUN · {data.summary.reason}</p>}
    <form className="ai-filters" onSubmit={filter}>
      <input name="q" aria-label="후보 고객사 포지션 검색" placeholder="후보·고객사·포지션 검색" />
      <select name="actor" aria-label="검색 AI"><option value="">전체 AI</option>{['GROK','CLAUDE_CODE','CHATGPT','AI_SEARCH','OTHER'].map(a => <option key={a}>{a}</option>)}</select>
      <input name="company" aria-label="고객사 필터" placeholder="고객사" /><input name="position" aria-label="포지션 필터" placeholder="포지션" />
      <select name="channel" aria-label="컨택 채널"><option value="">전체 채널</option>{CHANNELS.map(c => <option value={c} key={c}>{LABELS[c]}</option>)}</select>
      <select name="contact_status" aria-label="컨택 상태"><option value="">전체 상태</option>{['CONTACTED','REPLIED','CONFIRMED_NOT_CONTACTED','NOT_RUN','REVIEW_REQUIRED','FAILED'].map(s => <option value={s} key={s}>{LABELS[s]}</option>)}</select>
      <select name="sort" aria-label="정렬"><option value="">고객사순</option><option value="score">검증 점수순</option></select><button>검색 적용</button>
    </form>
    {loading && <p role="status">운영 자료를 불러오는 중입니다.</p>}
    {error && <div role="alert" className="error-state">{error} <button onClick={() => window.location.reload()}>다시 조회</button></div>}
    <div className="weekly-scroll" tabIndex={0} aria-label="후보 표, 가로 스크롤 가능"><table>
      <thead><tr>{['주차','Batch','고객사','포지션','후보자 이름','학력','경력','프로필','검증 점수','잘 맞는 이유','사람인 컨택','잡코리아 컨택','LinkedIn 컨택','Gmail/JD 발송','사람 후속 조치','상세 Raw'].map(h => <th key={h}>{h}</th>)}</tr></thead>
      <tbody>{data?.rows.map(row => <tr key={`${row.candidate_id}:${row.position_id}`}>
        <td>{row.week_id}</td><td><details><summary>{row.batches.map(b => b.display_number).join(', ')}</summary>
          {row.batches.map(b => <div key={b.id}>{b.display_number} · {value(b.document.actor)}<small>실행 {value(b.document.executed_at)}</small><small>수신 {value(b.document.received_at)}</small><small>{value(b.document.execution_time_source)}</small></div>)}</details></td>
        <td>{row.company}</td><td>{row.position}</td><td>{row.evaluation.candidate_name || '후보명 미확인'}<small>{row.evaluation.candidate_name_reason}</small></td>
        <td>{row.evaluation.education || '미확인'}</td><td>{row.evaluation.experience || '미확인'}</td>
        <td><EvidenceLink href={row.evaluation.profile_url}>프로필 ↗</EvidenceLink></td>
        <td>{row.evaluation.score_status === 'PASS' ? row.evaluation.score : 'NOT_RUN'}<small>{row.evaluation.source_reported_score !== undefined && row.evaluation.source_reported_score !== null ? `메일 원본 점수 ${row.evaluation.source_reported_score}` : ''}</small></td>
        <td>{row.evaluation.why_fit?.join(' · ') || '근거 미확인'}</td>
        {CHANNELS.map(c => <ContactCell key={c} row={row} channel={c} />)}
        <td>{row.evaluation.human_followup || '미확인'}</td><td><button type="button" onClick={() => void raw(row.candidate_id)}>상세 Raw</button></td>
      </tr>)}</tbody></table></div>
    {!loading && !error && data?.rows.length === 0 && <div className="empty-state">{data.complete ? '선택 범위에 확인된 후보가 없습니다.' : '수집·검증이 진행 중입니다. 후보가 0명이라고 확정할 수 없습니다.'}</div>}
    <footer className="weekly-pagination"><span>{data ? `${offset + (data.rows.length ? 1 : 0)}~${offset + data.rows.length} / ${data.total.toLocaleString()}행` : '—'}</span>
      <button disabled={offset === 0 || loading} onClick={() => setOffset(n => Math.max(0,n-50))}>이전</button>
      <button disabled={!data || offset + 50 >= data.total || loading} onClick={() => setOffset(n => n+50)}>다음</button></footer>
    <dialog ref={dialog} className="ai-raw-dialog" onClose={() => setModal(null)}>
      <header><h2>{modal?.title}</h2><button aria-label="모달 닫기" onClick={() => dialog.current?.close()}>닫기 ×</button></header>
      {modal?.error && <p role="alert">{modal.error}</p>}
      {!modal?.detail && !modal?.rows && !modal?.error && <p>원문을 불러오는 중입니다.</p>}
      {modal?.detail && <RawDetail detail={modal.detail} />}
      {modal?.rows?.map(row => <section key={`${row.candidate_id}:${row.position_id}`}><h3>{row.evaluation.candidate_name || '후보명 미확인'} · {row.company} · {row.position}</h3>
        <p>검증 점수 {row.evaluation.score} · 전체 채널 조회 범위 종료 및 미발송 근거 확인</p>
        {CHANNELS.map(c => <p key={c}>{LABELS[c]}: {value(row.contacts.filter(e => e.channel === c))}</p>)}
        <button onClick={() => void raw(row.candidate_id)}>후보 상세 이동</button></section>)}
      {modal?.rows?.length === 0 && <p>확정된 고점수 미컨택자가 없습니다. 미확인 자료는 집계에 포함하지 않습니다.</p>}
    </dialog>
  </main>;
}

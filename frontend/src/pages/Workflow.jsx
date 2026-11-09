import { useState } from 'react'
import { api } from '../services/api.js'
import { useLoad } from '../hooks.js'
import { useStore } from '../store.jsx'
import { ErrorBox, Loading, Modal } from '../components/ui.jsx'

export const STAGES = {
  receipt: { title: 'Sample Receipt', from: 'Sample Created', hint: 'Receive samples that have been logged.' },
  allocation: { title: 'Work Allocation', from: 'Sample Received', hint: 'Assign a received sample to an analyst.' },
  observation: { title: 'Observation Entry', from: 'Testing Assigned', hint: 'Record the observed test result for each sample assigned to you.' },
  testing: { title: 'Sample Testing', from: 'Testing Assigned', hint: 'Complete the analysis once a result has been entered. Only a Quality Analyst or Admin can complete it.' },
  review: { title: 'Review & Approve', from: 'Analysis Completed', hint: 'Approve or reject completed analyses. Admin only.' },
}

function Item({ s, stage, users, done }) {
  const S = useStore()
  const [analyst, setAnalyst] = useState(s.analyst || '')
  const [res, setRes] = useState(s.result || '')
  const [ask, setAsk] = useState(null); const [note, setNote] = useState('')
  const act = async (fn, msg) => {
    try { await fn(); S.notify(msg); S.bump(); done() } catch (e) { S.notify(e.message, 'err') }
  }
  const base = `/samples/${s.id}`
  const canComplete = S.user.role !== 'Lab Technician'
  return (
    <tr>
      <td>{s.lab_no}</td><td>{s.material_name}</td><td>{s.batch_no}</td><td>{s.quantity} {s.unit}</td>
      <td>{stage === 'allocation'
        ? <select name="analyst" value={analyst} onChange={e => setAnalyst(e.target.value)}><option value="">-- Select analyst --</option>{users.map(u => <option key={u.id} value={u.username}>{u.full_name} ({u.username})</option>)}</select>
        : stage === 'observation'
          ? <input name="result" placeholder="Result / observation" value={res} onChange={e => setRes(e.target.value)} />
          : [s.analyst_name || s.analyst, s.result].filter(Boolean).join(' - ')}</td>
      <td className="right">
        {stage === 'receipt' && <button className="btn sm primary" onClick={() => act(() => api.post(`${base}/receive`), `${s.lab_no} received`)}>Receive</button>}
        {stage === 'allocation' && <button className="btn sm primary" disabled={!analyst} onClick={() => act(() => api.post(`${base}/assign`, { analyst }), `${s.lab_no} assigned to ${analyst}`)}>Assign</button>}
        {stage === 'observation' && <button className="btn sm primary" onClick={() => act(() => api.post(`${base}/observe`, { result: res, complete: false }), `Result saved for ${s.lab_no}`)}>Save Result</button>}
        {stage === 'testing' && <button className="btn sm primary" disabled={!canComplete} title={canComplete ? '' : 'Only a Quality Analyst or Admin can complete the analysis'}
          onClick={() => (s.result ? act(() => api.post(`${base}/observe`, { result: s.result, complete: true }), `Analysis completed for ${s.lab_no}`) : S.notify('Enter a result in Observation Entry first', 'err'))}>Complete Analysis</button>}
        {stage === 'review' && <>
          <button className="btn sm primary" onClick={() => { setNote(''); setAsk('approve') }}>Approve</button>{' '}
          <button className="btn sm danger" onClick={() => { setNote(''); setAsk('reject') }}>Reject</button></>}
        {ask && (
          <Modal title={ask === 'approve' ? `Approve ${s.lab_no}` : `Reject ${s.lab_no}`} onClose={() => setAsk(null)}
            foot={<><button className={'btn ' + (ask === 'approve' ? 'primary' : 'danger')}
              onClick={() => act(() => api.post(`${base}/${ask}`, ask === 'approve' ? { remarks: note } : { reason: note }), `${s.lab_no} ${ask === 'approve' ? 'approved' : 'rejected'}`)}>
              {ask === 'approve' ? 'Approve' : 'Reject'}</button><button className="btn" onClick={() => setAsk(null)}>Cancel</button></>}>
            <div className="row"><label>{ask === 'approve' ? 'Remarks (optional)' : 'Reason (required)'}</label>
              <div className="ctl"><textarea name="note" rows="3" value={note} onChange={e => setNote(e.target.value)} /></div></div>
          </Modal>)}
      </td>
    </tr>
  )
}

export default function Workflow({ stage }) {
  const S = useStore(); const c = STAGES[stage]
  const list = useLoad(() => api.get('/samples', { status: c.from, per_page: 200, sort: 'lab_no' }), [stage, S.version])
  const users = useLoad(() => (stage === 'allocation' ? api.get('/users', { is_active: true, per_page: 200, sort: 'full_name' }) : Promise.resolve(null)), [stage])
  const assignable = users.data ? users.data.items.filter(u => u.role !== 'Admin') : []
  const rows = list.data ? list.data.items : []
  return (
    <div className="page"><p className="hint">{c.hint}</p>
      {list.error && <ErrorBox message={list.error} onRetry={list.reload} />}
      <div className="card"><table className="data">
        <thead><tr><th>Lab No</th><th>Material</th><th>Batch No</th><th>Qty</th><th>{stage === 'allocation' ? 'Analyst' : 'Details'}</th><th /></tr></thead>
        <tbody>{rows.map(s => <Item key={s.id + s.status} s={s} stage={stage} users={assignable} done={list.reload} />)}
          {list.data && !rows.length && <tr><td className="empty" colSpan="6">Nothing is waiting at this step.</td></tr>}</tbody></table>
        {list.loading && !list.data && <Loading />}
      </div></div>
  )
}

export function Sap() {
  return (
    <div className="page"><div className="card">
      <h3>Receipt From SAP</h3>
      <p>The connection to SAP is not set up yet. Until it is, log samples with <b>Sample Login → Create</b>, entering the SAP batch and lot numbers by hand.</p>
    </div></div>
  )
}

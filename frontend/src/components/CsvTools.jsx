import { useRef, useState } from 'react'
import { api, ApiError } from '../services/api.js'
import { useStore } from '../store.jsx'
import { Modal } from './ui.jsx'

// Export CSV / Export PDF buttons, plus (for Admin) a checked CSV import.
export default function CsvTools({ exportPath, exportQuery, importPath, canImport, onImported, name }) {
  const S = useStore()
  const input = useRef(null)
  const [imp, setImp] = useState(null) // { text, fileName, mode, check, problems, busy }

  const exportAs = async format => {
    try { await api.download(exportPath, { ...exportQuery, format }, `${name}.${format}`) }
    catch (e) { S.notify(e.message, 'err') }
  }
  const check = async (text, mode, fileName) => {
    setImp({ text, fileName, mode, check: null, problems: null, busy: true })
    try {
      const data = await api.importCsv(importPath, text, { dry_run: true, mode })
      setImp({ text, fileName, mode, check: data, problems: null, busy: false })
    } catch (e) {
      const problems = Array.isArray(e.errors) ? e.errors : null
      setImp({ text, fileName, mode, check: null, problems, message: e.message, busy: false })
    }
  }
  const pickFile = async e => {
    const file = e.target.files[0]
    e.target.value = ''
    if (file) check(await file.text(), 'create', file.name)
  }
  const run = async () => {
    setImp(i => ({ ...i, busy: true }))
    try {
      const data = await api.importCsv(importPath, imp.text, { mode: imp.mode })
      S.notify(`Imported: ${data.to_create} created, ${data.to_update} updated`); S.bump(); setImp(null); onImported && onImported()
    } catch (e) { S.notify(e.message, 'err'); setImp(i => ({ ...i, busy: false })) }
  }

  return (
    <>
      <button className="btn" onClick={() => exportAs('csv')}>Export CSV</button>
      <button className="btn" onClick={() => exportAs('pdf')}>Export PDF</button>
      {canImport && <>
        <button className="btn" onClick={() => input.current.click()}>Import CSV</button>
        <input ref={input} type="file" accept=".csv,text/csv" hidden data-testid="csv-file" onChange={pickFile} />
      </>}
      {imp && (
        <Modal title={`Import ${imp.fileName}`} onClose={() => setImp(null)}
          foot={<>
            <button className="btn primary" disabled={!imp.check || imp.busy} onClick={run}>Import</button>
            <button className="btn" onClick={() => setImp(null)}>Cancel</button></>}>
          <div className="row"><label>Existing codes</label><div className="ctl">
            <select value={imp.mode} onChange={e => check(imp.text, e.target.value, imp.fileName)}>
              <option value="create">Reject (every code must be new)</option>
              <option value="upsert">Update them, and add the new ones</option></select></div></div>
          {imp.busy && <p className="muted">Checking the file…</p>}
          {imp.check && <p className="note ok">File is valid: {imp.check.to_create} to create, {imp.check.to_update} to update.
            {imp.check.ignored_columns && imp.check.ignored_columns.length > 0 && ` Ignored columns: ${imp.check.ignored_columns.join(', ')}.`}</p>}
          {imp.message && !imp.check && !imp.busy && <p className="note err">{imp.message}</p>}
          {imp.problems && (
            <table className="data"><thead><tr><th>Row</th><th>Code</th><th>Problem</th></tr></thead><tbody>
              {imp.problems.slice(0, 30).map(p => (
                <tr key={p.row}><td>{p.row}</td><td>{p.code || p.material_code}</td>
                  <td>{Object.entries(p.errors).map(([k, v]) => `${k}: ${typeof v === 'string' ? v : JSON.stringify(v)}`).join('; ')}</td></tr>))}
            </tbody></table>)}
        </Modal>
      )}
    </>
  )
}
export { ApiError }

import React, { useState, useEffect } from 'react';
import { api, getActiveRoom, getSession } from '../api';

export default function Settings() {
  const isSuperAdmin = getSession()?.user?.role === 'SUPER_ADMIN';
  const activeRoom = getActiveRoom();
  const [startingBudget, setStartingBudget] = useState('700');
  const [importResult, setImportResult] = useState(null);
  const [importLoading, setImportLoading] = useState(false);
  const [saveMsg, setSaveMsg] = useState(null);
  const [errorMsg, setErrorMsg] = useState(null);
  const [auditLogs, setAuditLogs] = useState([]);
  const [logsLoading, setLogsLoading] = useState(true);

  const loadAuditLogs = async () => {
    setLogsLoading(true);
    try {
      setAuditLogs(await api.getAuditLog(200));
    } catch (err) {
      setErrorMsg(err.message);
    } finally {
      setLogsLoading(false);
    }
  };

  const handleResetRoom = async () => {
    if (!window.confirm(`Reset all auction activity in Room ${activeRoom}? This cannot be undone.`)) return;
    try {
      await api.resetRoom();
      setSaveMsg(`✓ Room ${activeRoom} auction reset successfully.`);
      setErrorMsg(null);
      await loadAuditLogs();
    } catch (err) {
      setErrorMsg(err.message);
    }
  };

  useEffect(() => {
    const loadSettings = async () => {
      try {
        const s = await api.getSettings();
        if (s.starting_budget) setStartingBudget(s.starting_budget);
      } catch (err) {
        console.error(err);
      }
    };
    loadSettings();
    loadAuditLogs();
  }, []);

  const handleSaveSettings = async (e) => {
    e.preventDefault();
    setSaveMsg(null);
    setErrorMsg(null);
    try {
      await api.updateSettings({ starting_budget: startingBudget });
      setSaveMsg('✓ Settings updated successfully!');
      await loadAuditLogs();
    } catch (err) {
      setErrorMsg(err.message);
    }
  };

  const handleFileUpload = async (e) => {
    if (!isSuperAdmin) return;
    const file = e.target.files[0];
    if (!file) return;

    setImportLoading(true);
    setImportResult(null);
    setErrorMsg(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const result = await api.importExcel(formData);
      setImportResult(result);
      await loadAuditLogs();
    } catch (err) {
      setErrorMsg(err.message);
    } finally {
      setImportLoading(false);
    }
  };

  return (
    <div>
      <div style={{ marginBottom: '24px' }}>
        <h1 style={{ fontSize: '2rem', fontWeight: 900, margin: 0 }}>⚙️ Admin & System Settings</h1>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.95rem' }}>
          Import Excel player data, export database backups & configure tournament rules
        </p>
      </div>

      {saveMsg && (
        <div className="badge badge-green" style={{ width: '100%', padding: '12px', marginBottom: '20px', fontSize: '0.9rem' }}>
          {saveMsg}
        </div>
      )}

      {errorMsg && (
        <div className="badge badge-red" style={{ width: '100%', padding: '12px', marginBottom: '20px', fontSize: '0.9rem' }}>
          ⚠️ {errorMsg}
        </div>
      )}

      <div className="settings-grid">
        {/* Left Column: Excel Import & Backup */}
        <div className="glass-card">
          <h2 style={{ fontSize: '1.25rem', fontWeight: 800, marginBottom: '14px', color: '#ffffff' }}>
            📊 Excel Data Management
          </h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.88rem', marginBottom: '20px' }}>
            {isSuperAdmin
              ? `Upload a player dataset specifically to Room ${activeRoom}. Imports never affect the other room.`
              : 'Dataset imports are restricted to the super admin. Room backups remain available below.'}
          </p>

          {/* Upload Box */}
          <div style={{
            border: '2px dashed var(--border-color)',
            borderRadius: '12px',
            padding: '30px',
            textAlign: 'center',
            background: 'var(--bg-dark)',
            marginBottom: '20px'
          }}>
            <div style={{ fontSize: '2.5rem', marginBottom: '10px' }}>📁</div>
            <div style={{ fontWeight: 800, marginBottom: '6px' }}>
              {importLoading ? 'Validating and Importing...' : 'Select Excel / CSV File'}
            </div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '16px' }}>
              Supports .xlsx, .xls, .csv format
            </div>

            <input
              type="file"
              accept=".xlsx,.xls,.csv"
              style={{ display: 'none' }}
              id="excel-file-input"
              onChange={handleFileUpload}
              disabled={importLoading || !isSuperAdmin}
            />
            <label htmlFor="excel-file-input" className={`btn ${isSuperAdmin ? 'btn-primary' : 'btn-secondary'}`} style={{ cursor: isSuperAdmin ? 'pointer' : 'not-allowed' }}>
              {isSuperAdmin ? `Upload to Room ${activeRoom}` : 'Super Admin Only'}
            </label>
          </div>

          {/* Download Sample & Export Backup buttons */}
          <div className="settings-actions">
            <button type="button" className="btn btn-secondary" style={{ flex: 1 }} onClick={() => api.downloadSampleTemplate().catch((err) => setErrorMsg(err.message))}>
              📥 Download Import Template
            </button>
            <button type="button" className="btn btn-secondary" style={{ flex: 1 }} onClick={() => api.downloadBackup().catch((err) => setErrorMsg(err.message))}>
              💾 Export Room {activeRoom} Backup
            </button>
          </div>

          <div style={{ marginTop: '12px', display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(190px, 1fr))', gap: '10px' }}>
            <button type="button" className="btn btn-primary" onClick={() => api.downloadResultsExcel().catch((err) => setErrorMsg(err.message))}>
              🏆 Export Ranked Results Excel
            </button>
            <button type="button" className="btn btn-primary" onClick={() => api.downloadAuditExcel().then(loadAuditLogs).catch((err) => setErrorMsg(err.message))}>
              📜 Export Full Audit Log Excel
            </button>
          </div>

          {/* Import Result Feedback */}
          {importResult && (
            <div style={{ marginTop: '20px', padding: '16px', borderRadius: '10px', background: importResult.success ? 'rgba(16,185,129,0.15)' : 'rgba(239,68,68,0.15)', border: `1px solid ${importResult.success ? 'var(--accent-green)' : 'var(--accent-red)'}` }}>
              <h4 style={{ fontWeight: 800, color: importResult.success ? 'var(--accent-green)' : 'var(--accent-red)', marginBottom: '8px' }}>
                {importResult.message}
              </h4>
              {importResult.success ? (
                <div style={{ fontSize: '0.88rem' }}>
                  Loaded: {importResult.player_count} players (GK: {importResult.gk_count}, DEF: {importResult.def_count}, MID: {importResult.mid_count}, ATT: {importResult.att_count}) across 20 teams.
                </div>
              ) : (
                <div style={{ fontSize: '0.82rem', maxHeight: '200px', overflowY: 'auto', background: 'var(--bg-dark)', padding: '10px', borderRadius: '6px' }}>
                  <div style={{ fontWeight: 800, color: 'var(--accent-red)', marginBottom: '6px' }}>Validation Errors:</div>
                  <ul style={{ paddingLeft: '16px', margin: 0 }}>
                    {importResult.errors.map((err, i) => (
                      <li key={i} style={{ color: 'var(--accent-red)' }}>{err}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Right Column: Settings Form & Rules */}
        <div className="glass-card">
          <h2 style={{ fontSize: '1.25rem', fontWeight: 800, marginBottom: '14px', color: '#ffffff' }}>
            ⚙️ Tournament Rules & Configuration
          </h2>

          <form onSubmit={handleSaveSettings}>
            <div style={{ marginBottom: '20px' }}>
              <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-muted)', fontWeight: 700, marginBottom: '6px' }}>
                STARTING BUDGET PER TEAM (€M)
              </label>
              <input
                type="number"
                step="5"
                min="10"
                className="input-field"
                value={startingBudget}
                onChange={(e) => setStartingBudget(e.target.value)}
              />
              <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                Default is 700M. Updating this will adjust starting budget across all 20 teams.
              </span>
            </div>

            <button type="submit" className="btn btn-primary" style={{ marginBottom: '24px' }}>
              Save Configuration
            </button>
          </form>

          <hr style={{ borderColor: 'var(--border-color)', margin: '20px 0' }} />

          <h3 style={{ fontSize: '1rem', fontWeight: 800, color: 'var(--accent-red)', marginBottom: '8px' }}>Danger Zone — Room {activeRoom}</h3>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginBottom: '10px' }}>
            Reset sales, captains, and unsold statuses in this room only. Audit and transaction history is preserved for safety.
          </p>
          <button type="button" className="btn btn-danger" onClick={handleResetRoom}>Reset Room {activeRoom} Auction</button>

          <hr style={{ borderColor: 'var(--border-color)', margin: '20px 0' }} />

          <h3 style={{ fontSize: '1rem', fontWeight: 800, marginBottom: '10px', color: '#ffffff' }}>
            📋 Required Formation Rules (Single Source of Truth)
          </h3>
          <ul style={{ fontSize: '0.88rem', color: 'var(--text-muted)', lineHeight: 1.8, paddingLeft: '20px' }}>
            <li><strong>Goalkeepers (GK):</strong> Minimum 1 required (Top 1 counts for Best 8)</li>
            <li><strong>Defenders (DEF):</strong> Minimum 3 required (Top 3 count for Best 8)</li>
            <li><strong>Midfielders (MID):</strong> Minimum 2 required (Top 2 count for Best 8)</li>
            <li><strong>Attackers (ATT):</strong> Minimum 2 required (Top 2 count for Best 8)</li>
            <li><strong>Best 8 Score:</strong> Sum of top 1 GK + 3 DEF + 2 MID + 2 ATT scores.</li>
            <li><strong>Captain Bonus:</strong> +100% of Captain's score if Captain is in Best 8.</li>
            <li><strong>Leaderboard Tie-Breaker:</strong> Final Score DESC → Base Score DESC → Spent ASC.</li>
          </ul>
        </div>
      </div>

      <div className="glass-card" style={{ marginTop: '24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', gap: '12px', alignItems: 'center', marginBottom: '14px' }}>
          <div>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 800, margin: 0, color: '#ffffff' }}>📜 Room {activeRoom} Audit Log</h2>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.84rem', margin: '5px 0 0' }}>
              Permanent record of auction and administrative actions. It is not deleted when the room is reset.
            </p>
          </div>
          <button type="button" className="btn btn-secondary" onClick={loadAuditLogs}>🔄 Refresh Logs</button>
        </div>
        <div style={{ overflowX: 'auto', maxHeight: '430px', overflowY: 'auto' }}>
          <table className="squad-table" style={{ minWidth: '850px' }}>
            <thead>
              <tr><th>Time (UTC)</th><th>Action</th><th>Admin</th><th>Description</th><th>Amount</th></tr>
            </thead>
            <tbody>
              {logsLoading ? (
                <tr><td colSpan="5">Loading logs...</td></tr>
              ) : auditLogs.length === 0 ? (
                <tr><td colSpan="5">No new audit entries yet. Historical auction transactions remain available in the Excel export.</td></tr>
              ) : auditLogs.map((log) => (
                <tr key={log.id}>
                  <td>{new Date(`${log.timestamp}${log.timestamp.endsWith('Z') ? '' : 'Z'}`).toLocaleString()}</td>
                  <td><strong>{log.action.replaceAll('_', ' ')}</strong></td>
                  <td>{log.actor_username}</td>
                  <td>{log.description}</td>
                  <td>{log.amount == null ? '—' : `€${log.amount.toFixed(2)}M`}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

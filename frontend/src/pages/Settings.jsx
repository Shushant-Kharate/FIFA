import React, { useState, useEffect } from 'react';
import { api } from '../api';

export default function Settings() {
  const [startingBudget, setStartingBudget] = useState('700');
  const [importResult, setImportResult] = useState(null);
  const [importLoading, setImportLoading] = useState(false);
  const [saveMsg, setSaveMsg] = useState(null);
  const [errorMsg, setErrorMsg] = useState(null);

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
  }, []);

  const handleSaveSettings = async (e) => {
    e.preventDefault();
    setSaveMsg(null);
    setErrorMsg(null);
    try {
      await api.updateSettings({ starting_budget: startingBudget });
      setSaveMsg('✓ Settings updated successfully!');
    } catch (err) {
      setErrorMsg(err.message);
    }
  };

  const handleFileUpload = async (e) => {
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

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
        {/* Left Column: Excel Import & Backup */}
        <div className="glass-card">
          <h2 style={{ fontSize: '1.25rem', fontWeight: 800, marginBottom: '14px', color: '#ffffff' }}>
            📊 Excel Data Management
          </h2>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.88rem', marginBottom: '20px' }}>
            Upload your player list Excel file (.xlsx or .csv). Headers must include: <code>player_code</code>, <code>name</code>, <code>position</code>, <code>p1</code>, <code>p2</code>, <code>p3</code>, <code>base_price</code>.
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
              disabled={importLoading}
            />
            <label htmlFor="excel-file-input" className="btn btn-primary" style={{ cursor: 'pointer' }}>
              Upload Excel File
            </label>
          </div>

          {/* Download Sample & Export Backup buttons */}
          <div style={{ display: 'flex', gap: '12px' }}>
            <a
              href={api.getSampleTemplateUrl()}
              className="btn btn-secondary"
              style={{ flex: 1, textDecoration: 'none' }}
              download
            >
              📥 Download Sample Template (192 Players)
            </a>
            <a
              href={api.getBackupUrl()}
              className="btn btn-secondary"
              style={{ flex: 1, textDecoration: 'none' }}
              download
            >
              💾 Export DB Backup (JSON)
            </a>
          </div>

          {/* Import Result Feedback */}
          {importResult && (
            <div style={{ marginTop: '20px', padding: '16px', borderRadius: '10px', background: importResult.success ? 'rgba(16,185,129,0.15)' : 'rgba(239,68,68,0.15)', border: `1px solid ${importResult.success ? 'var(--accent-green)' : 'var(--accent-red)'}` }}>
              <h4 style={{ fontWeight: 800, color: importResult.success ? 'var(--accent-green)' : 'var(--accent-red)', marginBottom: '8px' }}>
                {importResult.message}
              </h4>
              {importResult.success ? (
                <div style={{ fontSize: '0.88rem' }}>
                  Loaded: {importResult.player_count} players (GK: {importResult.gk_count}, DEF: {importResult.def_count}, MID: {importResult.mid_count}, ATT: {importResult.att_count}) across 25 teams.
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
                STARTING BUDGET PER TEAM ($M)
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
                Default is 700M. Updating this will adjust starting budget across all 25 teams.
              </span>
            </div>

            <button type="submit" className="btn btn-primary" style={{ marginBottom: '24px' }}>
              Save Configuration
            </button>
          </form>

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
    </div>
  );
}

import React from 'react';

export default function PlayerSearch({ 
  search, setSearch, 
  position, setPosition, 
  status, setStatus, 
  sort, setSort 
}) {
  const positions = ['ALL', 'GK', 'DEF', 'MID', 'ATT'];
  return (
    <div className="glass-card" style={{ marginBottom: '20px' }}>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '16px', alignItems: 'center' }}>
        {/* Search Input */}
        <div style={{ flex: '1 1 240px' }}>
          <input
            type="text"
            className="input-field"
            placeholder="🔍 Search player by name or code (e.g. Mbappe, P001)..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>

        {/* Position filter buttons */}
        <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 700, marginRight: '4px' }}>POS:</span>
          {positions.map((pos) => (
            <button
              key={pos}
              type="button"
              className={`btn ${position === pos ? 'btn-primary' : 'btn-secondary'}`}
              style={{ padding: '6px 12px', fontSize: '0.8rem' }}
              onClick={() => setPosition(pos)}
            >
              {pos}
            </button>
          ))}
        </div>

        {/* Status filter buttons */}
        <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 700, marginRight: '4px' }}>STATUS:</span>
          {['ALL', 'AVAILABLE', 'SOLD', 'UNSOLD'].map((st) => (
            <button
              key={st}
              type="button"
              className={`btn ${status === st ? 'btn-primary' : 'btn-secondary'}`}
              style={{ padding: '6px 12px', fontSize: '0.8rem' }}
              onClick={() => setStatus(st)}
            >
              {st}
            </button>
          ))}
        </div>

        {/* Sort dropdown */}
        <div style={{ display: 'flex', gap: '6px', alignItems: 'center' }}>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 700 }}>SORT:</span>
          <select
            className="input-field"
            style={{ width: 'auto', padding: '6px 12px', fontSize: '0.85rem' }}
            value={sort}
            onChange={(e) => setSort(e.target.value)}
          >
            <option value="code_asc">Code (Asc)</option>
            <option value="score_desc">Score (High → Low)</option>
            <option value="score_asc">Score (Low → High)</option>
            <option value="price_desc">Base Price (High → Low)</option>
            <option value="price_asc">Base Price (Low → High)</option>
            <option value="name_asc">Name (A → Z)</option>
          </select>
        </div>
      </div>
    </div>
  );
}

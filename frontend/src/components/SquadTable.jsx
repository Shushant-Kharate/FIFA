import React from 'react';

export default function SquadTable({ players = [], onSetCaptain = null }) {
  if (players.length === 0) {
    return (
      <div style={{ textAlign: 'center', padding: '32px', color: 'var(--text-muted)' }}>
        No players bought by this team yet.
      </div>
    );
  }

  return (
    <div className="table-container">
      <table className="custom-table">
        <thead>
          <tr>
            <th>LINEUP</th>
            <th>CODE</th>
            <th>NAME</th>
            <th>POS</th>
            <th>P1</th>
            <th>P2</th>
            <th>P3</th>
            <th>SCORE</th>
            <th>BASE PRICE</th>
            <th>SOLD PRICE</th>
            <th>ROLE</th>
          </tr>
        </thead>
        <tbody>
          {players.map((p) => (
            <tr key={p.id}>
              <td>
                {p.is_best_8 ? (
                  <span className="lineup-best8">STARTER ✓</span>
                ) : (
                  <span className="lineup-bench">BENCH</span>
                )}
              </td>
              <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 700 }}>{p.player_code}</td>
              <td style={{ fontWeight: 800 }}>
                {p.name}
                {p.is_captain && (
                  <span style={{ marginLeft: '8px', color: 'var(--accent-green)', fontWeight: 800 }}>
                    ★ CAPTAIN
                  </span>
                )}
              </td>
              <td>
                <span className={`badge ${
                  p.position === 'GK' ? 'badge-amber' :
                  p.position === 'DEF' ? 'badge-blue' :
                  p.position === 'MID' ? 'badge-green' : 'badge-red'
                }`}>
                  {p.position}
                </span>
              </td>
              <td>{p.p1}</td>
              <td>{p.p2}</td>
              <td>{p.p3}</td>
              <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 800, color: 'var(--accent-green)' }}>
                {p.score}
              </td>
              <td>₹{p.base_price?.toFixed(2)} Cr</td>
              <td style={{ fontWeight: 700 }}>
                {p.sold_price ? `₹${p.sold_price.toFixed(2)} Cr` : '-'}
              </td>
              <td>
                {onSetCaptain && (
                  p.is_best_8 ? (
                    p.is_captain ? (
                      <span className="badge badge-green">CAPTAIN</span>
                    ) : (
                      <button
                        type="button"
                        className="btn btn-secondary"
                        style={{ padding: '4px 10px', fontSize: '0.75rem' }}
                        onClick={() => onSetCaptain(p.id)}
                      >
                        Make Captain
                      </button>
                    )
                  ) : (
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Bench (N/A)</span>
                  )
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

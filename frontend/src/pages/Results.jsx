import React, { useEffect, useState } from 'react';
import { api } from '../api';

export default function Results() {
  const [leaderboard, setLeaderboard] = useState([]);
  const [showOnlyQualified, setShowOnlyQualified] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const data = await api.getResults();
        setLeaderboard(data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const displayList = showOnlyQualified 
    ? leaderboard.filter(t => t.qualified)
    : leaderboard;

  const champion = leaderboard.find(t => t.qualified) || leaderboard[0];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <div>
          <h1 style={{ fontSize: '2.2rem', fontWeight: 900, margin: 0, letterSpacing: '-0.5px' }}>
            🏆 FIFA Auction Tournament Leaderboard
          </h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.95rem' }}>
            Official ranked leaderboard determined by Best 8 Base Score + Captain Boost (Tie-breakers applied)
          </p>
        </div>

        <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
          <label style={{ fontSize: '0.88rem', color: 'var(--text-muted)', fontWeight: 700 }}>
            <input
              type="checkbox"
              checked={showOnlyQualified}
              onChange={(e) => setShowOnlyQualified(e.target.checked)}
              style={{ marginRight: '8px', accentColor: 'var(--accent-green)' }}
            />
            Show Qualified Teams Only
          </label>
        </div>
      </div>

      {/* Champion Spotlight Banner */}
      {champion && (
        <div style={{
          background: 'linear-gradient(135deg, rgba(16,185,129,0.25), rgba(14,15,18,0.95))',
          border: '2px solid var(--accent-green)',
          borderRadius: '16px',
          padding: '28px',
          marginBottom: '28px',
          boxShadow: '0 12px 36px rgba(16,185,129,0.2)',
          display: 'flex',
          justify: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '20px'
        }}>
          <div>
            <span className="badge badge-green" style={{ fontSize: '0.85rem', padding: '6px 12px', marginBottom: '8px' }}>
              👑 CURRENT LEADER / CHAMPION
            </span>
            <h2 style={{ fontSize: '2.5rem', fontWeight: 900, margin: '4px 0 0 0', color: '#ffffff' }}>
              TEAM {String(champion.team_number).padStart(2, '0')}
            </h2>
            <div style={{ color: 'var(--text-muted)', fontSize: '0.95rem', marginTop: '4px' }}>
              Spent: ₹{champion.spent.toFixed(2)} Cr • Squad Size: {champion.players.length} Players
              {champion.captain_name && ` • Captain: ${champion.captain_name}`}
            </div>
          </div>

          <div style={{ textAlign: 'right' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--accent-green)', fontWeight: 800 }}>CHAMPIONSHIP SCORE</span>
            <div style={{ fontSize: '3.2rem', fontWeight: 900, fontFamily: 'var(--font-mono)', color: 'var(--accent-green)', lineHeight: 1 }}>
              {champion.final_score}
            </div>
            <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
              Base: {champion.base_score} + Captain: {champion.captain_score}
            </div>
          </div>
        </div>
      )}

      {/* Leaderboard Table */}
      <div className="table-container">
        <table className="custom-table" style={{ fontSize: '1rem' }}>
          <thead>
            <tr>
              <th style={{ width: '80px' }}>RANK</th>
              <th>TEAM</th>
              <th>QUALIFICATION</th>
              <th>FORMATION COUNTS (GK/DEF/MID/ATT)</th>
              <th>SPENT (CR)</th>
              <th>BASE SCORE</th>
              <th>CAPTAIN BOOST</th>
              <th>FINAL SCORE</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan="8" style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
                  Calculating rankings...
                </td>
              </tr>
            ) : displayList.length === 0 ? (
              <tr>
                <td colSpan="8" style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
                  No teams found.
                </td>
              </tr>
            ) : (
              displayList.map((t, idx) => (
                <tr key={t.team_id} style={{
                  background: idx === 0 ? 'rgba(16,185,129,0.06)' : 'transparent',
                }}>
                  <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 900, fontSize: '1.2rem', color: idx === 0 ? 'var(--accent-green)' : '#ffffff' }}>
                    #{idx + 1}
                  </td>
                  <td style={{ fontWeight: 900, fontSize: '1.1rem' }}>
                    TEAM {String(t.team_number).padStart(2, '0')}
                  </td>
                  <td>
                    {t.qualified ? (
                      <span className="badge badge-green">✓ QUALIFIED</span>
                    ) : (
                      <span className="badge badge-red">✕ DISQUALIFIED</span>
                    )}
                  </td>
                  <td style={{ fontSize: '0.88rem', fontFamily: 'var(--font-mono)' }}>
                    GK:{t.counts.GK} | DEF:{t.counts.DEF} | MID:{t.counts.MID} | ATT:{t.counts.ATT}
                  </td>
                  <td style={{ fontWeight: 700 }}>
                    ₹{t.spent.toFixed(2)} Cr
                  </td>
                  <td>{t.base_score}</td>
                  <td style={{ color: 'var(--accent-green)', fontWeight: 700 }}>
                    +{t.captain_score}
                  </td>
                  <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 900, fontSize: '1.4rem', color: 'var(--accent-green)' }}>
                    {t.final_score}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

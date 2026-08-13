import React, { useEffect, useState } from 'react';
import { api } from '../api';
import TeamCard from '../components/TeamCard';

export default function Teams() {
  const [teams, setTeams] = useState([]);
  const [filter, setFilter] = useState('ALL'); // ALL, QUALIFIED, AT_RISK, DISQUALIFIED
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const data = await api.getTeams();
        setTeams(data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const filteredTeams = teams.filter((t) => {
    if (filter === 'QUALIFIED') return t.qualified;
    if (filter === 'AT_RISK') return t.formation_at_risk;
    if (filter === 'DISQUALIFIED') return !t.qualified;
    return true;
  });

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <div>
          <h1 style={{ fontSize: '2rem', fontWeight: 900, margin: 0 }}>🛡️ Teams Overview</h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.95rem' }}>
            Formation compliance, budget tracking & squad health across all 25 franchises
          </p>
        </div>

        {/* Filter buttons */}
        <div style={{ display: 'flex', gap: '8px' }}>
          {['ALL', 'QUALIFIED', 'AT_RISK', 'DISQUALIFIED'].map((f) => (
            <button
              key={f}
              type="button"
              className={`btn ${filter === f ? 'btn-primary' : 'btn-secondary'}`}
              style={{ padding: '6px 14px', fontSize: '0.85rem' }}
              onClick={() => setFilter(f)}
            >
              {f.replace('_', ' ')}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
          Loading teams...
        </div>
      ) : (
        <div className="teams-grid">
          {filteredTeams.map((t) => (
            <TeamCard key={t.team_id} team={t} />
          ))}
        </div>
      )}
    </div>
  );
}

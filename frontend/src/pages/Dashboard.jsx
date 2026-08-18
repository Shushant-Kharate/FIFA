import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api';
import TeamCard from '../components/TeamCard';

export default function Dashboard() {
  const navigate = useNavigate();
  const [teams, setTeams] = useState([]);
  const [players, setPlayers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadData = async () => {
    try {
      setLoading(true);
      const [teamsData, playersData] = await Promise.all([
        api.getTeams(),
        api.getPlayers()
      ]);
      setTeams(teamsData);
      setPlayers(playersData);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const totalPlayers = players.length;
  const soldPlayers = players.filter((p) => p.status === 'SOLD').length;
  const unsoldPlayers = players.filter((p) => p.status === 'UNSOLD').length;
  const availablePlayers = players.filter((p) => p.status === 'AVAILABLE').length;

  const totalSpent = teams.reduce((acc, t) => acc + (t.spent || 0), 0);
  const qualifiedTeamsCount = teams.filter((t) => t.qualified).length;

  return (
    <div>
      {/* Top Banner & Title */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <div>
          <h1 style={{ fontSize: '2rem', fontWeight: 900, margin: 0, letterSpacing: '-0.5px' }}>
            Auction Control Dashboard
          </h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.95rem' }}>
            Real-time status overview of 20 competing teams & {totalPlayers} players
          </p>
        </div>

        <div style={{ display: 'flex', gap: '12px' }}>
          <button type="button" className="btn btn-secondary" onClick={loadData}>
            🔄 Refresh
          </button>
          <button type="button" className="btn btn-primary" onClick={() => navigate('/auction')}>
            ⚡ Launch Live Auction
          </button>
        </div>
      </div>

      {error && (
        <div className="badge badge-red" style={{ width: '100%', padding: '12px', marginBottom: '20px', fontSize: '0.9rem' }}>
          ⚠️ Error loading data: {error}
        </div>
      )}

      {/* Metric Stats Cards */}
      <div className="stats-grid">
        <div className="stat-box">
          <div className="stat-icon">🏃</div>
          <div>
            <div className="stat-value">{totalPlayers}</div>
            <div className="stat-label">Total Players</div>
          </div>
        </div>

        <div className="stat-box">
          <div className="stat-icon" style={{ background: 'rgba(16,185,129,0.15)', color: 'var(--accent-green)' }}>✓</div>
          <div>
            <div className="stat-value" style={{ color: 'var(--accent-green)' }}>{soldPlayers}</div>
            <div className="stat-label">Sold Players</div>
          </div>
        </div>

        <div className="stat-box">
          <div className="stat-icon" style={{ background: 'rgba(59,130,246,0.15)', color: 'var(--accent-blue)' }}>📋</div>
          <div>
            <div className="stat-value" style={{ color: 'var(--accent-blue)' }}>{availablePlayers}</div>
            <div className="stat-label">In Pool</div>
          </div>
        </div>

        <div className="stat-box">
          <div className="stat-icon" style={{ background: 'rgba(245,158,11,0.15)', color: 'var(--accent-amber)' }}>⏳</div>
          <div>
            <div className="stat-value" style={{ color: 'var(--accent-amber)' }}>{unsoldPlayers}</div>
            <div className="stat-label">Unsold</div>
          </div>
        </div>

        <div className="stat-box">
          <div className="stat-icon" style={{ background: 'rgba(139,92,246,0.15)', color: 'var(--accent-purple)' }}>🏆</div>
          <div>
            <div className="stat-value" style={{ color: 'var(--accent-purple)' }}>{qualifiedTeamsCount} / {teams.length}</div>
            <div className="stat-label">Teams Qualified</div>
          </div>
        </div>

        <div className="stat-box">
          <div className="stat-icon" style={{ background: 'rgba(16,185,129,0.15)', color: 'var(--accent-green)' }}>💰</div>
          <div>
            <div className="stat-value" style={{ color: 'var(--accent-green)' }}>€{totalSpent.toFixed(1)}M</div>
            <div className="stat-label">Total Spent</div>
          </div>
        </div>
      </div>

      {/* Teams Grid */}
      <h2 style={{ fontSize: '1.3rem', fontWeight: 800, marginBottom: '16px', color: '#ffffff' }}>
        🛡️ 20 Teams Overview
      </h2>

      {loading ? (
        <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
          Loading team state...
        </div>
      ) : (
        <div className="teams-grid">
          {teams.map((t) => (
            <TeamCard key={t.team_id} team={t} />
          ))}
        </div>
      )}
    </div>
  );
}

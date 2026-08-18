import React from 'react';
import { useNavigate } from 'react-router-dom';
import BudgetBar from './BudgetBar';

export default function TeamCard({ team }) {
  const navigate = useNavigate();

  const counts = team.counts || { GK: 0, DEF: 0, MID: 0, ATT: 0 };
  const totalSquad = (team.players || []).length;

  return (
    <div 
      className="glass-card"
      style={{ cursor: 'pointer' }}
      onClick={() => navigate(`/teams/${team.team_id}`)}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
        <h3 style={{ fontSize: '1.15rem', fontWeight: 800, margin: 0, color: '#ffffff' }}>
          TEAM {String(team.team_number).padStart(2, '0')}
        </h3>

        {team.qualified ? (
          <span className="badge badge-green">✓ QUALIFIED</span>
        ) : team.formation_at_risk ? (
          <span className="badge badge-amber">⚠ AT RISK</span>
        ) : (
          <span className="badge badge-red">✕ DISQUALIFIED</span>
        )}
      </div>

      {/* Formation slots */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '6px', marginBottom: '14px' }}>
        <div style={{ background: 'rgba(255,255,255,0.03)', padding: '6px', borderRadius: '6px', textAlign: 'center' }}>
          <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', fontWeight: 700 }}>GK</div>
          <div style={{ fontSize: '0.9rem', fontWeight: 800, color: counts.GK >= 1 ? 'var(--accent-green)' : 'var(--accent-red)' }}>
            {counts.GK}/1
          </div>
        </div>

        <div style={{ background: 'rgba(255,255,255,0.03)', padding: '6px', borderRadius: '6px', textAlign: 'center' }}>
          <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', fontWeight: 700 }}>DEF</div>
          <div style={{ fontSize: '0.9rem', fontWeight: 800, color: counts.DEF >= 3 ? 'var(--accent-green)' : 'var(--accent-red)' }}>
            {counts.DEF}/3
          </div>
        </div>

        <div style={{ background: 'rgba(255,255,255,0.03)', padding: '6px', borderRadius: '6px', textAlign: 'center' }}>
          <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', fontWeight: 700 }}>MID</div>
          <div style={{ fontSize: '0.9rem', fontWeight: 800, color: counts.MID >= 2 ? 'var(--accent-green)' : 'var(--accent-red)' }}>
            {counts.MID}/2
          </div>
        </div>

        <div style={{ background: 'rgba(255,255,255,0.03)', padding: '6px', borderRadius: '6px', textAlign: 'center' }}>
          <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', fontWeight: 700 }}>ATT</div>
          <div style={{ fontSize: '0.9rem', fontWeight: 800, color: counts.ATT >= 2 ? 'var(--accent-green)' : 'var(--accent-red)' }}>
            {counts.ATT}/2
          </div>
        </div>
      </div>

      {/* Score and squad size */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
        <div>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 700 }}>TOTAL SCORE</span>
          <div style={{ fontSize: '1.4rem', fontWeight: 900, fontFamily: 'var(--font-mono)', color: 'var(--accent-green)' }}>
            {team.final_score} <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>(Base: {team.base_score})</span>
          </div>
        </div>
        <div style={{ textAlign: 'right' }}>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 700 }}>SQUAD</span>
          <div style={{ fontSize: '1.1rem', fontWeight: 800 }}>{totalSquad} Players</div>
        </div>
      </div>

      {/* Captain tag if set */}
      {team.captain_name && (
        <div style={{ fontSize: '0.78rem', color: 'var(--accent-green)', background: 'rgba(16,185,129,0.1)', padding: '4px 8px', borderRadius: '4px', marginBottom: '8px', fontWeight: 700 }}>
          ★ Captain: {team.captain_name} (+{team.captain_score})
        </div>
      )}

      {team.qualified && (
        <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '8px' }}>
          Chemistry: <strong style={{ color: 'var(--accent-blue)' }}>+{team.nationality_bonus} nationality</strong>
          {' • '}
          <strong style={{ color: 'var(--accent-purple)' }}>+{team.club_bonus} club</strong>
        </div>
      )}

      {/* Budget Bar */}
      <BudgetBar 
        spent={team.spent}
        startingBudget={team.starting_budget}
        remainingBudget={team.remaining_budget}
      />
    </div>
  );
}

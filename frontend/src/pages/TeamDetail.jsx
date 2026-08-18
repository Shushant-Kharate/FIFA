import React, { useCallback, useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { api } from '../api';
import SquadTable from '../components/SquadTable';
import BudgetBar from '../components/BudgetBar';

export default function TeamDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [team, setTeam] = useState(null);
  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState(null);
  const [captainMsg, setCaptainMsg] = useState(null);

  const loadTeam = useCallback(async () => {
    try {
      setLoading(true);
      const data = await api.getTeam(id);
      setTeam(data);
      setErrorMsg(null);
    } catch (err) {
      setErrorMsg(err.message);
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    loadTeam();
  }, [loadTeam]);

  const handleSetCaptain = async (playerId) => {
    try {
      setCaptainMsg(null);
      setErrorMsg(null);
      const updated = await api.setCaptain(team.team_id, playerId);
      setTeam(updated);
      setCaptainMsg('★ Captain set successfully!');
    } catch (err) {
      setErrorMsg(err.message);
    }
  };

  if (loading) {
    return <div style={{ textAlign: 'center', padding: '60px', color: 'var(--text-muted)' }}>Loading team details...</div>;
  }

  if (errorMsg && !team) {
    return (
      <div style={{ textAlign: 'center', padding: '40px' }}>
        <div className="badge badge-red" style={{ fontSize: '1rem', padding: '12px 24px', marginBottom: '16px' }}>
          ⚠️ {errorMsg}
        </div>
        <div>
          <button className="btn btn-secondary" onClick={() => navigate('/teams')}>← Back to Teams</button>
        </div>
      </div>
    );
  }

  const missingList = Object.entries(team.missing || {}).map(([pos, count]) => `${count} ${pos}`);
  const nationalityGroups = Object.entries(team.nationality_bonus_breakdown || {});
  const clubGroups = Object.entries(team.club_bonus_breakdown || {});

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <button type="button" className="btn btn-secondary" onClick={() => navigate('/teams')}>
          ← Back to Teams
        </button>

        <div style={{ display: 'flex', gap: '10px' }}>
          {team.qualified ? (
            <span className="badge badge-green" style={{ fontSize: '0.9rem', padding: '8px 16px' }}>✓ QUALIFIED FOR LEADERBOARD</span>
          ) : team.formation_at_risk ? (
            <span className="badge badge-amber" style={{ fontSize: '0.9rem', padding: '8px 16px' }}>⚠ FORMATION AT RISK</span>
          ) : (
            <span className="badge badge-red" style={{ fontSize: '0.9rem', padding: '8px 16px' }}>✕ DISQUALIFIED (INCOMPLETE FORMATION)</span>
          )}
        </div>
      </div>

      {captainMsg && (
        <div className="badge badge-green" style={{ width: '100%', padding: '10px', marginBottom: '16px', fontSize: '0.9rem' }}>
          {captainMsg}
        </div>
      )}

      {errorMsg && (
        <div className="badge badge-red" style={{ width: '100%', padding: '10px', marginBottom: '16px', fontSize: '0.9rem' }}>
          ⚠️ {errorMsg}
        </div>
      )}

      {/* Header Banner Card */}
      <div className="glass-card" style={{ marginBottom: '24px' }}>
        <div style={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'space-between', alignItems: 'center', gap: '20px' }}>
          <div>
            <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)', fontWeight: 800, textTransform: 'uppercase' }}>
              FRANCHISE DETAILS
            </span>
            <h1 style={{ fontSize: '2.4rem', fontWeight: 900, margin: '2px 0 0 0', color: '#ffffff' }}>
              TEAM {String(team.team_number).padStart(2, '0')}
            </h1>
            <div style={{ fontSize: '0.9rem', color: 'var(--text-muted)', marginTop: '4px' }}>
              Squad Size: <strong style={{ color: '#ffffff' }}>{team.players.length} Players</strong> • Best 8 ID Count: <strong style={{ color: 'var(--accent-green)' }}>{team.best_8_ids.length}</strong>
            </div>
          </div>

          {/* Scores Breakdown */}
          <div style={{ display: 'flex', gap: '24px', alignItems: 'center', flexWrap: 'wrap', justifyContent: 'flex-end' }}>
            <div style={{ textAlign: 'center', background: 'var(--bg-dark)', padding: '12px 20px', borderRadius: '10px' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 800 }}>BASE SCORE</div>
              <div style={{ fontSize: '1.8rem', fontWeight: 800 }}>{team.base_score}</div>
            </div>

            <div style={{ textAlign: 'center', background: 'var(--bg-dark)', padding: '12px 20px', borderRadius: '10px' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 800 }}>CAPTAIN BOOST</div>
              <div style={{ fontSize: '1.8rem', fontWeight: 800, color: 'var(--accent-green)' }}>
                +{team.captain_score}
              </div>
            </div>

            <div style={{ textAlign: 'center', background: 'var(--bg-dark)', padding: '12px 20px', borderRadius: '10px' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 800 }}>NATIONALITY</div>
              <div style={{ fontSize: '1.8rem', fontWeight: 800, color: 'var(--accent-blue)' }}>
                +{team.nationality_bonus}
              </div>
            </div>

            <div style={{ textAlign: 'center', background: 'var(--bg-dark)', padding: '12px 20px', borderRadius: '10px' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 800 }}>CLUB</div>
              <div style={{ fontSize: '1.8rem', fontWeight: 800, color: 'var(--accent-purple)' }}>
                +{team.club_bonus}
              </div>
            </div>

            <div style={{ textAlign: 'center', background: 'linear-gradient(135deg, rgba(16,185,129,0.2), rgba(5,150,105,0.1))', border: '1px solid var(--accent-green)', padding: '12px 20px', borderRadius: '10px' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--accent-green)', fontWeight: 800 }}>FINAL SCORE</div>
              <div style={{ fontSize: '2.2rem', fontWeight: 900, fontFamily: 'var(--font-mono)', color: 'var(--accent-green)', lineHeight: 1 }}>
                {team.final_score}
              </div>
            </div>
          </div>
        </div>

        <hr style={{ borderColor: 'var(--border-color)', margin: '20px 0' }} />

        {/* Formation Status Grid */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px', marginBottom: '16px' }}>
          <div style={{ background: 'var(--bg-dark)', padding: '12px', borderRadius: '8px', textAlign: 'center' }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 700 }}>GOALKEEPER (GK)</span>
            <div style={{ fontSize: '1.2rem', fontWeight: 800, color: team.counts.GK >= 1 ? 'var(--accent-green)' : 'var(--accent-red)' }}>
              {team.counts.GK} / 1 Required
            </div>
          </div>
          <div style={{ background: 'var(--bg-dark)', padding: '12px', borderRadius: '8px', textAlign: 'center' }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 700 }}>DEFENDERS (DEF)</span>
            <div style={{ fontSize: '1.2rem', fontWeight: 800, color: team.counts.DEF >= 3 ? 'var(--accent-green)' : 'var(--accent-red)' }}>
              {team.counts.DEF} / 3 Required
            </div>
          </div>
          <div style={{ background: 'var(--bg-dark)', padding: '12px', borderRadius: '8px', textAlign: 'center' }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 700 }}>MIDFIELDERS (MID)</span>
            <div style={{ fontSize: '1.2rem', fontWeight: 800, color: team.counts.MID >= 2 ? 'var(--accent-green)' : 'var(--accent-red)' }}>
              {team.counts.MID} / 2 Required
            </div>
          </div>
          <div style={{ background: 'var(--bg-dark)', padding: '12px', borderRadius: '8px', textAlign: 'center' }}>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 700 }}>ATTACKERS (ATT)</span>
            <div style={{ fontSize: '1.2rem', fontWeight: 800, color: team.counts.ATT >= 2 ? 'var(--accent-green)' : 'var(--accent-red)' }}>
              {team.counts.ATT} / 2 Required
            </div>
          </div>
        </div>

        {/* Warnings */}
        {missingList.length > 0 && (
          <div style={{ background: 'rgba(239,68,68,0.12)', border: '1px solid var(--accent-red)', color: 'var(--accent-red)', padding: '10px 16px', borderRadius: '8px', fontSize: '0.88rem', fontWeight: 700, marginBottom: '16px' }}>
            ⚠️ Disqualified for Leaderboard: Missing {missingList.join(', ')} to complete formation.
          </div>
        )}

        {team.formation_at_risk && (
          <div style={{ background: 'rgba(245,158,11,0.12)', border: '1px solid var(--accent-amber)', color: 'var(--accent-amber)', padding: '10px 16px', borderRadius: '8px', fontSize: '0.88rem', fontWeight: 700, marginBottom: '16px' }}>
            ⚠️ FORMATION AT RISK: Remaining budget (€{team.remaining_budget.toFixed(2)}M) is less than estimated cost needed to purchase remaining missing slots!
          </div>
        )}

        {team.qualified && (nationalityGroups.length > 0 || clubGroups.length > 0) && (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '16px' }}>
            <div style={{ background: 'rgba(59,130,246,0.1)', border: '1px solid var(--accent-blue)', padding: '12px', borderRadius: '8px' }}>
              <div style={{ fontWeight: 800, color: 'var(--accent-blue)', marginBottom: '6px' }}>🌍 Nationality Bonuses</div>
              {nationalityGroups.length ? nationalityGroups.map(([name, bonus]) => (
                <div key={name} style={{ fontSize: '0.85rem' }}>{name}: +{bonus}</div>
              )) : <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>No qualifying group</div>}
            </div>
            <div style={{ background: 'rgba(139,92,246,0.1)', border: '1px solid var(--accent-purple)', padding: '12px', borderRadius: '8px' }}>
              <div style={{ fontWeight: 800, color: 'var(--accent-purple)', marginBottom: '6px' }}>🏟️ Club Bonuses</div>
              {clubGroups.length ? clubGroups.map(([name, bonus]) => (
                <div key={name} style={{ fontSize: '0.85rem' }}>{name}: +{bonus}</div>
              )) : <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>No qualifying group</div>}
            </div>
          </div>
        )}

        {/* Budget Bar */}
        <BudgetBar
          spent={team.spent}
          startingBudget={team.starting_budget}
          remainingBudget={team.remaining_budget}
        />
      </div>

      {/* Squad Roster */}
      <div className="glass-card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <h3 style={{ fontSize: '1.2rem', fontWeight: 800, margin: 0, color: '#ffffff' }}>
            📋 Squad Roster & Lineup Breakdown
          </h3>

          {team.captain_name ? (
            <div style={{ fontSize: '0.9rem', color: 'var(--accent-green)', fontWeight: 800 }}>
              ★ Current Captain: {team.captain_name} (+{team.captain_score} pts)
            </div>
          ) : (
            <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
              Assign a Captain from the Best 8 players below to gain bonus points!
            </div>
          )}
        </div>

        <SquadTable players={team.players} onSetCaptain={handleSetCaptain} />
      </div>
    </div>
  );
}

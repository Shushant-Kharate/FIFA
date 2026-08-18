import React from 'react';

export default function ConfirmModal({ isOpen, onClose, onConfirm, player, team, price }) {
  if (!isOpen || !player || !team) return null;

  const currentBudget = team.remaining_budget;
  const newBudget = currentBudget - price;

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <h2 style={{ fontSize: '1.3rem', fontWeight: 900, marginBottom: '16px', color: '#ffffff' }}>
          ⚽ Confirm Auction Sale
        </h2>

        <div style={{ background: 'var(--bg-dark)', padding: '16px', borderRadius: '10px', marginBottom: '20px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
            <span style={{ color: 'var(--text-muted)' }}>Player:</span>
            <span style={{ fontWeight: 800 }}>{player.name} ({player.position})</span>
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
            <span style={{ color: 'var(--text-muted)' }}>Score:</span>
            <span style={{ fontWeight: 800, color: 'var(--accent-green)' }}>{player.score}</span>
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
            <span style={{ color: 'var(--text-muted)' }}>Selling To:</span>
            <span style={{ fontWeight: 800, color: 'var(--accent-blue)' }}>
              TEAM {String(team.team_number).padStart(2, '0')}
            </span>
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
            <span style={{ color: 'var(--text-muted)' }}>Sale Price:</span>
            <span style={{ fontWeight: 800, fontSize: '1.1rem', color: 'var(--accent-green)' }}>
              €{parseFloat(price).toFixed(2)}M
            </span>
          </div>

          <hr style={{ borderColor: 'var(--border-color)', margin: '12px 0' }} />

          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px', fontSize: '0.85rem' }}>
            <span style={{ color: 'var(--text-muted)' }}>Current Remaining Budget:</span>
            <span>€{currentBudget.toFixed(2)}M</span>
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.9rem', fontWeight: 800 }}>
            <span>New Remaining Budget:</span>
            <span style={{ color: newBudget < 0 ? 'var(--accent-red)' : 'var(--accent-green)' }}>
              €{newBudget.toFixed(2)}M
            </span>
          </div>
        </div>

        {newBudget < 0 && (
          <div className="badge badge-red" style={{ width: '100%', padding: '10px', marginBottom: '16px', justifyContent: 'center' }}>
            ⚠️ ERROR: Sale price exceeds team's remaining budget!
          </div>
        )}

        <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
          <button type="button" className="btn btn-secondary" onClick={onClose}>
            Cancel
          </button>
          <button 
            type="button" 
            className="btn btn-primary" 
            disabled={newBudget < 0}
            onClick={onConfirm}
          >
            Confirm Sale
          </button>
        </div>
      </div>
    </div>
  );
}

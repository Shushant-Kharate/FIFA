import React from 'react';

export default function BudgetBar({ spent, startingBudget, remainingBudget }) {
  const percentSpent = Math.min(100, Math.max(0, (spent / startingBudget) * 100));
  
  // Color determination based on remaining budget
  let fillColor = 'var(--accent-green)';
  if (remainingBudget < 10) {
    fillColor = 'var(--accent-amber)';
  }
  if (remainingBudget < 5) {
    fillColor = 'var(--accent-red)';
  }

  return (
    <div style={{ marginTop: '8px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600 }}>
        <span>Spent: ₹{spent.toFixed(2)} Cr</span>
        <span style={{ color: remainingBudget < 5 ? 'var(--accent-red)' : 'var(--text-main)', fontWeight: 800 }}>
          Rem: ₹{remainingBudget.toFixed(2)} Cr
        </span>
      </div>
      <div className="budget-bar-track">
        <div 
          className="budget-bar-fill"
          style={{ width: `${percentSpent}%`, backgroundColor: fillColor }}
        />
      </div>
    </div>
  );
}

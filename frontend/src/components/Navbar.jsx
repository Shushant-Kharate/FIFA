import React from 'react';
import { NavLink } from 'react-router-dom';

export default function Navbar() {
  return (
    <nav className="navbar">
      <div className="nav-container">
        <NavLink to="/" className="nav-brand">
          <span style={{ fontSize: '1.5rem' }}>⚽</span>
          <span>FIFA AUCTION</span>
          <span className="nav-brand-badge">PRO LIVE</span>
        </NavLink>

        <div className="nav-links">
          <NavLink to="/" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            📊 Dashboard
          </NavLink>
          <NavLink to="/auction" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            ⚡ Live Auction
          </NavLink>
          <NavLink to="/players" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            🏃 Players
          </NavLink>
          <NavLink to="/teams" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            🛡️ Teams
          </NavLink>
          <NavLink to="/results" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            🏆 Leaderboard
          </NavLink>
          <NavLink to="/settings" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
            ⚙️ Settings
          </NavLink>
        </div>
      </div>
    </nav>
  );
}

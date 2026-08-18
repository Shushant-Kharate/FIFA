import React from 'react';
import { NavLink } from 'react-router-dom';
import { getActiveRoom, setActiveRoom } from '../api';

export default function Navbar({ session, onLogout }) {
  const activeRoom = getActiveRoom();

  const switchRoom = (roomId) => {
    setActiveRoom(roomId);
    window.location.assign('/');
  };

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
          {session.user.role === 'SUPER_ADMIN' && [1, 2].map((room) => (
            <button key={room} type="button" className={`btn ${activeRoom === room ? 'btn-primary' : 'btn-secondary'}`} style={{ padding: '6px 10px' }} onClick={() => switchRoom(room)}>
              Room {room}
            </button>
          ))}
          <div style={{ marginLeft: '8px', textAlign: 'right', fontSize: '0.75rem' }}>
            <div style={{ fontWeight: 800 }}>{session.user.username}</div>
            <div style={{ color: 'var(--text-muted)' }}>Room {activeRoom}</div>
          </div>
          <button type="button" className="btn btn-secondary" style={{ padding: '6px 10px' }} onClick={onLogout}>Logout</button>
        </div>
      </div>
    </nav>
  );
}

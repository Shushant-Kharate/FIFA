import React, { useState } from 'react';
import { BrowserRouter, Navigate, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import Dashboard from './pages/Dashboard';
import LiveAuction from './pages/LiveAuction';
import Players from './pages/Players';
import Teams from './pages/Teams';
import TeamDetail from './pages/TeamDetail';
import Results from './pages/Results';
import Settings from './pages/Settings';
import Login from './pages/Login';
import { clearSession, getSession } from './api';

export default function App() {
  const [session, setSessionState] = useState(getSession());

  if (!session) {
    return <Login onLogin={setSessionState} />;
  }

  const logout = () => {
    clearSession();
    setSessionState(null);
  };

  return (
    <BrowserRouter>
      <div className="app-container">
        <Navbar session={session} onLogout={logout} />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/auction" element={<LiveAuction />} />
            <Route path="/players" element={<Players />} />
            <Route path="/teams" element={<Teams />} />
            <Route path="/teams/:id" element={<TeamDetail />} />
            <Route path="/results" element={<Results />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

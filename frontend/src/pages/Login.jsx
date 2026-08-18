import React, { useState } from 'react';
import { api, setActiveRoom, setSession } from '../api';


export default function Login({ onLogin }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const submit = async (event) => {
    event.preventDefault();
    try {
      setLoading(true);
      setError(null);
      const session = await api.login(username.trim(), password);
      setSession(session);
      setActiveRoom(session.user.room_id || 1);
      onLogin(session);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ minHeight: '100vh', display: 'grid', placeItems: 'center', padding: '24px', background: 'radial-gradient(circle at top, #16223a, var(--bg-dark) 55%)' }}>
      <form className="glass-card" onSubmit={submit} style={{ width: '100%', maxWidth: '430px', padding: '34px' }}>
        <div style={{ fontSize: '2.6rem', textAlign: 'center' }}>⚽</div>
        <h1 style={{ textAlign: 'center', fontSize: '1.9rem', margin: '8px 0 4px' }}>FIFA Auction Login</h1>
        <p style={{ textAlign: 'center', color: 'var(--text-muted)', marginBottom: '26px' }}>
          Sign in to your assigned auction room
        </p>
        {error && <div className="badge badge-red" style={{ width: '100%', padding: '10px', marginBottom: '16px' }}>{error}</div>}
        <label htmlFor="login-username" style={{ display: 'block', fontWeight: 700, marginBottom: '6px' }}>Username</label>
        <input id="login-username" className="input-field" value={username} onChange={(e) => setUsername(e.target.value)} autoComplete="username" required />
        <label htmlFor="login-password" style={{ display: 'block', fontWeight: 700, margin: '16px 0 6px' }}>Password</label>
        <input id="login-password" className="input-field" type="password" value={password} onChange={(e) => setPassword(e.target.value)} autoComplete="current-password" required />
        <button className="btn btn-primary" type="submit" disabled={loading} style={{ width: '100%', marginTop: '24px', padding: '12px' }}>
          {loading ? 'Signing in…' : 'Sign In'}
        </button>
      </form>
    </div>
  );
}

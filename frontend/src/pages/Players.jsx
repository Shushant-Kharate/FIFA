import React, { useEffect, useState } from 'react';
import { api } from '../api';
import PlayerSearch from '../components/PlayerSearch';

export default function Players() {
  const [players, setPlayers] = useState([]);
  const [teams, setTeams] = useState([]);
  const [search, setSearch] = useState('');
  const [position, setPosition] = useState('ALL');
  const [status, setStatus] = useState('ALL');
  const [sort, setSort] = useState('code_asc');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const [pData, tData] = await Promise.all([
          api.getPlayers({ search, position, status, sort }),
          api.getTeams()
        ]);
        setPlayers(pData);
        setTeams(tData);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [search, position, status, sort]);

  const teamMap = teams.reduce((acc, t) => {
    acc[t.team_id] = t.team_number;
    return acc;
  }, {});

  return (
    <div>
      <div style={{ marginBottom: '24px' }}>
        <h1 style={{ fontSize: '2rem', fontWeight: 900, margin: 0 }}>🏃 Player Directory</h1>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.95rem' }}>
          Inspect all {players.length} players, performance metrics, base values & auction status
        </p>
      </div>

      <PlayerSearch
        search={search} setSearch={setSearch}
        position={position} setPosition={setPosition}
        status={status} setStatus={setStatus}
        sort={sort} setSort={setSort}
      />

      <div className="table-container">
        <table className="custom-table">
          <thead>
            <tr>
              <th>CODE</th>
              <th>NAME</th>
              <th>POSITION</th>
              <th>NATIONALITY</th>
              <th>CLUB</th>
              <th>P1</th>
              <th>P2</th>
              <th>P3</th>
              <th>SCORE</th>
              <th>BASE PRICE</th>
              <th>STATUS</th>
              <th>SOLD PRICE</th>
              <th>TEAM</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan="13" style={{ textAlign: 'center', padding: '30px', color: 'var(--text-muted)' }}>
                  Loading players...
                </td>
              </tr>
            ) : players.length === 0 ? (
              <tr>
                <td colSpan="13" style={{ textAlign: 'center', padding: '30px', color: 'var(--text-muted)' }}>
                  No players match criteria.
                </td>
              </tr>
            ) : (
              players.map((p) => (
                <tr key={p.id}>
                  <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 700 }}>{p.player_code}</td>
                  <td style={{ fontWeight: 800 }}>{p.name}</td>
                  <td>
                    <span className={`badge ${
                      p.position === 'GK' ? 'badge-amber' :
                      p.position === 'DEF' ? 'badge-blue' :
                      p.position === 'MID' ? 'badge-green' : 'badge-red'
                    }`}>
                      {p.position}
                    </span>
                  </td>
                  <td>{p.nationality || '-'}</td>
                  <td style={{ maxWidth: '220px' }}>{p.club || '-'}</td>
                  <td>{p.p1}</td>
                  <td>{p.p2}</td>
                  <td>{p.p3}</td>
                  <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 800, color: 'var(--accent-green)' }}>
                    {p.score}
                  </td>
                  <td>€{p.base_price?.toFixed(2)}M</td>
                  <td>
                    <span className={`badge ${
                      p.status === 'SOLD' ? 'badge-green' :
                      p.status === 'UNSOLD' ? 'badge-red' : 'badge-blue'
                    }`}>
                      {p.status}
                    </span>
                  </td>
                  <td style={{ fontWeight: 700 }}>
                    {p.sold_price ? `€${p.sold_price.toFixed(2)}M` : '-'}
                  </td>
                  <td>
                    {p.team_id ? `Team ${String(teamMap[p.team_id] || p.team_id).padStart(2, '0')}` : '-'}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

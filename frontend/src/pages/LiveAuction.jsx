import React, { useEffect, useState } from 'react';
import { api } from '../api';
import PlayerSearch from '../components/PlayerSearch';
import ConfirmModal from '../components/ConfirmModal';

export default function LiveAuction() {
  const [players, setPlayers] = useState([]);
  const [teams, setTeams] = useState([]);
  const [history, setHistory] = useState([]);
  
  const [search, setSearch] = useState('');
  const [position, setPosition] = useState('ALL');
  const [status, setStatus] = useState('AVAILABLE');
  const [sort, setSort] = useState('score_desc');

  const [selectedPlayer, setSelectedPlayer] = useState(null);
  const [selectedTeamId, setSelectedTeamId] = useState('');
  const [priceInput, setPriceInput] = useState('');
  
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [lastAction, setLastAction] = useState(null); // { message, playerId }
  const [errorMsg, setErrorMsg] = useState(null);
  const [loading, setLoading] = useState(false);

  const loadData = async () => {
    try {
      setLoading(true);
      const [pData, tData, hData] = await Promise.all([
        api.getPlayers({ search, position, status, sort }),
        api.getTeams(),
        api.getAuctionHistory(15)
      ]);
      setPlayers(pData);
      setTeams(tData);
      setHistory(hData);
      
      // Auto select first player if none selected or current selection not in list
      if (pData.length > 0 && !selectedPlayer) {
        setSelectedPlayer(pData[0]);
        setPriceInput(pData[0].base_price ? String(pData[0].base_price) : '1.0');
      }
      if (tData.length > 0 && !selectedTeamId) {
        setSelectedTeamId(String(tData[0].team_id));
      }
    } catch (err) {
      setErrorMsg(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [search, position, status, sort]);

  const handleSelectPlayer = (player) => {
    setSelectedPlayer(player);
    setPriceInput(player.base_price ? String(player.base_price) : '1.0');
    setErrorMsg(null);
  };

  const handleSellClick = () => {
    if (!selectedPlayer || !selectedTeamId || !priceInput) return;
    setErrorMsg(null);
    setIsModalOpen(true);
  };

  const handleConfirmSell = async () => {
    setIsModalOpen(false);
    if (!selectedPlayer || !selectedTeamId) return;

    try {
      const price = parseFloat(priceInput);
      const teamId = parseInt(selectedTeamId, 10);
      const updatedTeam = await api.sellPlayer(selectedPlayer.id, teamId, price);

      const selTeam = teams.find((t) => t.team_id === teamId);
      const teamNum = selTeam ? selTeam.team_number : teamId;

      setLastAction({
        type: 'SOLD',
        message: `✓ Sold ${selectedPlayer.name} to Team ${teamNum} for $${price.toFixed(2)}M!`,
        playerId: selectedPlayer.id
      });

      setSelectedPlayer(null);
      await loadData();
    } catch (err) {
      setErrorMsg(err.message);
    }
  };

  const handleMarkUnsold = async () => {
    if (!selectedPlayer) return;
    try {
      await api.markUnsold(selectedPlayer.id);
      setLastAction({
        type: 'UNSOLD',
        message: `⚠️ Marked ${selectedPlayer.name} as UNSOLD`,
        playerId: selectedPlayer.id
      });
      setSelectedPlayer(null);
      await loadData();
    } catch (err) {
      setErrorMsg(err.message);
    }
  };

  const handleReturnToPool = async () => {
    if (!selectedPlayer) return;
    try {
      await api.returnToPool(selectedPlayer.id);
      setLastAction({
        type: 'RETURN',
        message: `🔄 Returned ${selectedPlayer.name} back to AVAILABLE pool`,
        playerId: selectedPlayer.id
      });
      await loadData();
    } catch (err) {
      setErrorMsg(err.message);
    }
  };

  const handleUndo = async (playerId) => {
    try {
      await api.undoLastSale(playerId);
      setLastAction({
        type: 'UNDO',
        message: `↩️ Undid sale for player`,
        playerId: null
      });
      await loadData();
    } catch (err) {
      setErrorMsg(err.message);
    }
  };

  const targetTeam = teams.find((t) => t.team_id === parseInt(selectedTeamId, 10));

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <div>
          <h1 style={{ fontSize: '2rem', fontWeight: 900, margin: 0 }}>⚡ Live Auction Console</h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '0.95rem' }}>
            Fast-paced player bidding, instant team budget updates & undo safety
          </p>
        </div>
      </div>

      {/* Toast Notification for recent action */}
      {lastAction && (
        <div style={{
          background: lastAction.type === 'SOLD' ? 'rgba(16,185,129,0.2)' : 'rgba(245,158,11,0.2)',
          border: `1px solid ${lastAction.type === 'SOLD' ? 'var(--accent-green)' : 'var(--accent-amber)'}`,
          padding: '12px 20px',
          borderRadius: '10px',
          marginBottom: '20px',
          display: 'flex',
          justify: 'space-between',
          alignItems: 'center'
        }}>
          <span style={{ fontWeight: 800, fontSize: '1rem' }}>{lastAction.message}</span>
          {lastAction.playerId && (
            <button
              type="button"
              className="btn btn-secondary"
              style={{ padding: '6px 14px', fontSize: '0.85rem' }}
              onClick={() => handleUndo(lastAction.playerId)}
            >
              ↩️ UNDO LAST ACTION
            </button>
          )}
        </div>
      )}

      {errorMsg && (
        <div className="badge badge-red" style={{ width: '100%', padding: '12px', marginBottom: '20px', fontSize: '0.9rem' }}>
          ⚠️ {errorMsg}
        </div>
      )}

      {/* Filter Component */}
      <PlayerSearch
        search={search} setSearch={setSearch}
        position={position} setPosition={setPosition}
        status={status} setStatus={setStatus}
        sort={sort} setSort={setSort}
      />

      <div className="auction-console">
        {/* Left Column: Player List */}
        <div className="glass-card" style={{ maxHeight: '600px', display: 'flex', flexDirection: 'column' }}>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 800, marginBottom: '12px', color: '#ffffff' }}>
            📋 Player Pool ({players.length})
          </h3>

          <div style={{ flex: 1, overflowY: 'auto', paddingRight: '4px' }}>
            {players.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '40px', color: 'var(--text-muted)' }}>
                No matching players found.
              </div>
            ) : (
              players.map((p) => (
                <div
                  key={p.id}
                  onClick={() => handleSelectPlayer(p)}
                  style={{
                    padding: '12px 16px',
                    borderRadius: '8px',
                    marginBottom: '8px',
                    cursor: 'pointer',
                    background: selectedPlayer?.id === p.id ? 'rgba(16,185,129,0.15)' : 'var(--bg-dark)',
                    border: `1px solid ${selectedPlayer?.id === p.id ? 'var(--accent-green)' : 'var(--border-color)'}`,
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    transition: 'all 0.15s ease'
                  }}
                >
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                        {p.player_code}
                      </span>
                      <span style={{ fontWeight: 800, color: '#ffffff' }}>{p.name}</span>
                      <span className={`badge ${
                        p.position === 'GK' ? 'badge-amber' :
                        p.position === 'DEF' ? 'badge-blue' :
                        p.position === 'MID' ? 'badge-green' : 'badge-red'
                      }`}>
                        {p.position}
                      </span>
                    </div>
                    <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                      P1: {p.p1} | P2: {p.p2} | P3: {p.p3} • Base: ${p.base_price?.toFixed(2)}M
                    </div>
                  </div>

                  <div style={{ textAlign: 'right' }}>
                    <div className="score-pill" style={{ fontSize: '1.4rem' }}>
                      {p.score}
                    </div>
                    <span className={`badge ${
                      p.status === 'SOLD' ? 'badge-green' :
                      p.status === 'UNSOLD' ? 'badge-amber' : 'badge-blue'
                    }`} style={{ fontSize: '0.7rem' }}>
                      {p.status}
                    </span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Right Column: Selected Player Console */}
        <div>
          {selectedPlayer ? (
            <div className="player-highlight-card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px' }}>
                <div>
                  <span className={`badge ${
                    selectedPlayer.position === 'GK' ? 'badge-amber' :
                    selectedPlayer.position === 'DEF' ? 'badge-blue' :
                    selectedPlayer.position === 'MID' ? 'badge-green' : 'badge-red'
                  }`} style={{ fontSize: '0.85rem', padding: '6px 12px' }}>
                    {selectedPlayer.position}
                  </span>
                  <h2 style={{ fontSize: '1.8rem', fontWeight: 900, margin: '6px 0 0 0', color: '#ffffff' }}>
                    {selectedPlayer.name}
                  </h2>
                  <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-muted)', fontSize: '0.9rem' }}>
                    Code: {selectedPlayer.player_code}
                  </span>
                </div>

                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 800 }}>OVERALL SCORE</div>
                  <div className="score-pill">{selectedPlayer.score}</div>
                </div>
              </div>

              {/* Ratings Breakdown Grid */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '10px', background: 'var(--bg-dark)', padding: '12px', borderRadius: '10px', marginBottom: '20px' }}>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontWeight: 700 }}>P1 RATING</div>
                  <div style={{ fontSize: '1.2rem', fontWeight: 800 }}>{selectedPlayer.p1}</div>
                </div>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontWeight: 700 }}>P2 RATING</div>
                  <div style={{ fontSize: '1.2rem', fontWeight: 800 }}>{selectedPlayer.p2}</div>
                </div>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontWeight: 700 }}>P3 RATING</div>
                  <div style={{ fontSize: '1.2rem', fontWeight: 800 }}>{selectedPlayer.p3}</div>
                </div>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', fontWeight: 700 }}>BASE PRICE</div>
                  <div style={{ fontSize: '1.2rem', fontWeight: 800, color: 'var(--accent-green)' }}>
                    ${selectedPlayer.base_price?.toFixed(2)}M
                  </div>
                </div>
              </div>

              {/* Bidding Controls */}
              <div style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border-color)', padding: '20px', borderRadius: '12px', marginBottom: '20px' }}>
                <h4 style={{ fontSize: '1rem', fontWeight: 800, marginBottom: '14px', color: '#ffffff' }}>
                  🔨 Execute Bidding Action
                </h4>

                <div style={{ marginBottom: '14px' }}>
                  <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-muted)', fontWeight: 700, marginBottom: '6px' }}>
                    SELECT BUYING TEAM
                  </label>
                  <select
                    className="input-field"
                    value={selectedTeamId}
                    onChange={(e) => setSelectedTeamId(e.target.value)}
                  >
                    {teams.map((t) => (
                      <option key={t.team_id} value={t.team_id}>
                        Team {String(t.team_number).padStart(2, '0')} — Rem: ${t.remaining_budget.toFixed(2)}M ({t.players.length} players)
                      </option>
                    ))}
                  </select>
                </div>

                <div style={{ marginBottom: '18px' }}>
                  <label style={{ display: 'block', fontSize: '0.85rem', color: 'var(--text-muted)', fontWeight: 700, marginBottom: '6px' }}>
                    SALE PRICE ($M)
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    min="0.1"
                    className="input-field"
                    style={{ fontSize: '1.2rem', fontWeight: 800, fontFamily: 'var(--font-mono)' }}
                    value={priceInput}
                    onChange={(e) => setPriceInput(e.target.value)}
                  />
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '12px' }}>
                  <button
                    type="button"
                    className="btn btn-primary"
                    style={{ padding: '12px', fontSize: '1.05rem' }}
                    onClick={handleSellClick}
                    disabled={selectedPlayer.status === 'SOLD'}
                  >
                    🤝 SELL PLAYER
                  </button>

                  {selectedPlayer.status === 'UNSOLD' ? (
                    <button
                      type="button"
                      className="btn btn-secondary"
                      onClick={handleReturnToPool}
                    >
                      🔄 POOL
                    </button>
                  ) : (
                    <button
                      type="button"
                      className="btn btn-danger"
                      onClick={handleMarkUnsold}
                      disabled={selectedPlayer.status === 'SOLD'}
                    >
                      ⚠️ UNSOLD
                    </button>
                  )}
                </div>
              </div>

              {selectedPlayer.status === 'SOLD' && (
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'rgba(16,185,129,0.12)', padding: '12px 16px', borderRadius: '8px' }}>
                  <div>
                    <span style={{ fontSize: '0.85rem', color: 'var(--accent-green)', fontWeight: 800 }}>
                      SOLD to Team {teams.find(t => t.team_id === selectedPlayer.team_id)?.team_number} for ${selectedPlayer.sold_price?.toFixed(2)}M
                    </span>
                  </div>
                  <button
                    type="button"
                    className="btn btn-secondary"
                    style={{ padding: '4px 10px', fontSize: '0.8rem' }}
                    onClick={() => handleUndo(selectedPlayer.id)}
                  >
                    ↩️ Undo Sale
                  </button>
                </div>
              )}
            </div>
          ) : (
            <div className="glass-card" style={{ padding: '60px', textAlign: 'center', color: 'var(--text-muted)' }}>
              Select a player from the list to begin auctioning.
            </div>
          )}
        </div>
      </div>

      {/* Transaction Feed */}
      <div className="glass-card" style={{ marginTop: '24px' }}>
        <h3 style={{ fontSize: '1.1rem', fontWeight: 800, marginBottom: '14px', color: '#ffffff' }}>
          📜 Recent Auction Activity Log
        </h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {history.map((tx) => (
            <div 
              key={tx.id} 
              style={{ 
                display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                padding: '10px 14px', background: 'var(--bg-dark)', borderRadius: '6px', fontSize: '0.88rem' 
              }}
            >
              <div>
                <span className={`badge ${
                  tx.event_type === 'SOLD' ? 'badge-green' :
                  tx.event_type === 'UNSOLD' ? 'badge-red' :
                  tx.event_type === 'UNDO' ? 'badge-amber' : 'badge-blue'
                }`} style={{ marginRight: '10px' }}>
                  {tx.event_type}
                </span>
                <span>
                  Player #{tx.player_id} {tx.team_id ? `→ Team #${tx.team_id}` : ''} {tx.amount ? `for $${tx.amount.toFixed(2)}M` : ''}
                </span>
              </div>
              <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem', fontFamily: 'var(--font-mono)' }}>
                {new Date(tx.timestamp).toLocaleTimeString()}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Confirm Modal */}
      <ConfirmModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onConfirm={handleConfirmSell}
        player={selectedPlayer}
        team={targetTeam}
        price={parseFloat(priceInput || '0')}
      />
    </div>
  );
}

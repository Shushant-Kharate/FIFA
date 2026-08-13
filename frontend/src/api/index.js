const API_BASE = "http://localhost:8000/api";

export async function fetchApi(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;
  const response = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
    ...options,
  });

  if (!response.ok) {
    let errorDetail = `Error ${response.status}: ${response.statusText}`;
    try {
      const errorJson = await response.json();
      if (errorJson.detail) {
        errorDetail = typeof errorJson.detail === "string" 
          ? errorJson.detail 
          : JSON.stringify(errorJson.detail);
      }
    } catch (e) {
      // JSON parse error fallback
    }
    throw new Error(errorDetail);
  }

  return response.json();
}

export const api = {
  // Players
  getPlayers: (params = {}) => {
    const query = new URLSearchParams();
    if (params.search) query.append("search", params.search);
    if (params.position && params.position !== "ALL") query.append("position", params.position);
    if (params.status && params.status !== "ALL") query.append("status", params.status);
    if (params.sort) query.append("sort", params.sort);
    return fetchApi(`/players?${query.toString()}`);
  },
  getPlayer: (id) => fetchApi(`/players/${id}`),

  // Teams
  getTeams: () => fetchApi("/teams"),
  getTeam: (id) => fetchApi(`/teams/${id}`),
  setCaptain: (teamId, playerId) =>
    fetchApi(`/teams/${teamId}/captain`, {
      method: "POST",
      body: JSON.stringify({ player_id: playerId }),
    }),

  // Auction
  sellPlayer: (playerId, teamId, price) =>
    fetchApi("/auction/sell", {
      method: "POST",
      body: JSON.stringify({ player_id: playerId, team_id: teamId, price: parseFloat(price) }),
    }),
  markUnsold: (playerId) =>
    fetchApi("/auction/unsold", {
      method: "POST",
      body: JSON.stringify({ player_id: playerId }),
    }),
  undoLastSale: (playerId) =>
    fetchApi("/auction/undo", {
      method: "POST",
      body: JSON.stringify({ player_id: playerId }),
    }),
  returnToPool: (playerId) =>
    fetchApi("/auction/return-to-pool", {
      method: "POST",
      body: JSON.stringify({ player_id: playerId }),
    }),
  getAuctionHistory: (limit = 20) => fetchApi(`/auction/history?limit=${limit}`),

  // Results
  getResults: () => fetchApi("/results"),

  // Admin & Settings
  getSettings: () => fetchApi("/settings"),
  updateSettings: (settings) =>
    fetchApi("/settings", {
      method: "PUT",
      body: JSON.stringify(settings),
    }),
  importExcel: async (formData) => {
    const response = await fetch(`${API_BASE}/admin/import`, {
      method: "POST",
      body: formData,
    });
    if (!response.ok) {
      const err = await response.json();
      throw new Error(err.detail || "Import failed");
    }
    return response.json();
  },
  getSampleTemplateUrl: () => `${API_BASE}/admin/sample-template`,
  getBackupUrl: () => `${API_BASE}/admin/backup`,
};

const API_BASE = import.meta.env.VITE_API_BASE || "/api";
const SESSION_KEY = "fifa_auction_session";
const ROOM_KEY = "fifa_auction_room";

export const getSession = () => {
  try {
    return JSON.parse(localStorage.getItem(SESSION_KEY));
  } catch {
    return null;
  }
};

export const setSession = (session) => localStorage.setItem(SESSION_KEY, JSON.stringify(session));
export const clearSession = () => {
  localStorage.removeItem(SESSION_KEY);
  localStorage.removeItem(ROOM_KEY);
};
export const getActiveRoom = () => Number(localStorage.getItem(ROOM_KEY) || getSession()?.user?.room_id || 1);
export const setActiveRoom = (roomId) => localStorage.setItem(ROOM_KEY, String(roomId));

function authHeaders() {
  const session = getSession();
  return session ? {
    Authorization: `Bearer ${session.access_token}`,
    "X-Room-ID": String(getActiveRoom()),
  } : {};
}

export async function fetchApi(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;
  const response = await fetch(url, {
    headers: {
      "Content-Type": "application/json",
      ...authHeaders(),
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
    } catch {
      // JSON parse error fallback
    }
    if (response.status === 401 && endpoint !== "/auth/login") {
      clearSession();
      window.location.reload();
    }
    throw new Error(errorDetail);
  }

  return response.json();
}

export const api = {
  login: (username, password) => fetchApi("/auth/login", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  }),
  getMe: () => fetchApi("/auth/me"),

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
      headers: authHeaders(),
      body: formData,
    });
    if (!response.ok) {
      const err = await response.json();
      throw new Error(err.detail || "Import failed");
    }
    return response.json();
  },
  downloadFile: async (endpoint, filename) => {
    const response = await fetch(`${API_BASE}${endpoint}`, { headers: authHeaders() });
    if (!response.ok) throw new Error("Download failed");
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = filename;
    anchor.click();
    URL.revokeObjectURL(url);
  },
  downloadSampleTemplate: () => api.downloadFile("/admin/sample-template", "fifa_players.xlsx"),
  downloadBackup: () => api.downloadFile("/admin/backup", `fifa_room_${getActiveRoom()}_backup.json`),
  getAuditLog: (limit = 200) => fetchApi(`/admin/audit-log?limit=${limit}`),
  downloadResultsExcel: () => api.downloadFile("/admin/export-results", `fifa_room_${getActiveRoom()}_ranked_results.xlsx`),
  downloadAuditExcel: () => api.downloadFile("/admin/export-audit-log", `fifa_room_${getActiveRoom()}_audit_log.xlsx`),
  resetRoom: () => fetchApi("/admin/reset", { method: "POST" }),
};

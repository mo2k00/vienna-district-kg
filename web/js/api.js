async function request(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = await response.json();
      detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
    } catch {
      /* keep status text */
    }
    throw new Error(detail);
  }
  return response.json();
}

let shapes;

export const api = {
  meta: () => request("/api/meta"),
  stations: (query) => request(`/api/stations?q=${encodeURIComponent(query)}`),
  recommend: (body) => request("/api/recommend", { method: "POST", body: JSON.stringify(body) }),
  district: (id) => request(`/api/districts/${id}`),
  similar: (id, source, k = 5) =>
    request(`/api/districts/${id}/similar?source=${encodeURIComponent(source)}&k=${k}`),
  shapes: async () => (shapes ??= await request("/data/districts.geojson")),
};

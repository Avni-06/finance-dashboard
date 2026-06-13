const BASE = "http://localhost:5000/api";

const getToken = () => localStorage.getItem("token");

export const api = {
  post: async (path, body, isFormData = false) => {
    const headers = { Authorization: `Bearer ${getToken()}` };
    if (!isFormData) headers["Content-Type"] = "application/json";
    const res = await fetch(`${BASE}${path}`, {
      method: "POST",
      headers,
      body: isFormData ? body : JSON.stringify(body),
    });
    if (!res.ok) throw await res.json();
    return res.json();
  },
  get: async (path) => {
    const res = await fetch(`${BASE}${path}`, {
      headers: { Authorization: `Bearer ${getToken()}` },
    });
    if (!res.ok) throw await res.json();
    return res.json();
  },
};
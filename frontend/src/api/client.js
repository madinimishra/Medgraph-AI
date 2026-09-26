const API_URL = import.meta.env.VITE_API_URL;

function getToken() {
  return localStorage.getItem("medgraph_token");
}

async function request(path, options = {}) {
  const headers = {
    ...(options.headers || {}),
  };

  const token = getToken();
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const isFormLike =
    options.body instanceof URLSearchParams ||
    options.body instanceof FormData;

  if (options.body && !isFormLike) {
    headers["Content-Type"] = "application/json";
  }

  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let detail = response.statusText;
    try {
      const data = await response.json();
      detail = data.detail || JSON.stringify(data);
    } catch {
      // ignore, use statusText
    }
    throw new Error(detail);
  }

  const contentType = response.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    return response.json();
  }
  return response.text();
}

export const api = {
  get: (path) => request(path, { method: "GET" }),
  post: (path, body) =>
    request(path, { method: "POST", body: JSON.stringify(body) }),
  patch: (path, body) =>
    request(path, { method: "PATCH", body: JSON.stringify(body) }),
  del: (path) => request(path, { method: "DELETE" }),
  postForm: (path, formBody) =>
    request(path, { method: "POST", body: formBody }),
  postFile: (path, file, extraFields = {}) => {
    const formData = new FormData();
    formData.append("file", file);
    for (const [key, value] of Object.entries(extraFields)) {
      formData.append(key, value);
    }
    return request(path, { method: "POST", body: formData });
  },
  // Plain <a href> / window.open can't send an Authorization header, so
  // authenticated file downloads/views fetch the bytes here and the
  // caller turns them into an object URL instead.
  getBlob: async (path) => {
    const token = getToken();
    const response = await fetch(`${API_URL}${path}`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (!response.ok) {
      let detail = response.statusText;
      try {
        const data = await response.json();
        detail = data.detail || JSON.stringify(data);
      } catch {
        // ignore, use statusText
      }
      throw new Error(detail);
    }
    return response.blob();
  },
};

export function setToken(token) {
  localStorage.setItem("medgraph_token", token);
}

export function clearToken() {
  localStorage.removeItem("medgraph_token");
}

export function hasToken() {
  return Boolean(getToken());
}

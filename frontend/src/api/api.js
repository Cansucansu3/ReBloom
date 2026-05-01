const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

export function getToken() {
  return localStorage.getItem("token");
}

export function setToken(token) {
  localStorage.setItem("token", token);
}

export function clearToken() {
  localStorage.removeItem("token");
}

async function request(path, options = {}) {
  const token = getToken();
  const headers = {
    "Content-Type": "application/json",
    ...options.headers,
  };

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let message = "Request failed";
    try {
      const errorData = await response.json();
      message = errorData.detail || message;
    } catch {
      message = response.statusText || message;
    }
    throw new Error(message);
  }

  return response.json();
}

export async function getProducts({ query } = {}) {
  const params = new URLSearchParams();

  if (query) {
    params.set("q", query);
  }

  const suffix = params.toString() ? `?${params.toString()}` : "";
  return request(`/products/${suffix}`);
}

export async function createProduct(product) {
  return request("/products/", {
    method: "POST",
    body: JSON.stringify(product),
  });
}

export async function addToCart(productId) {
  return request(`/cart/add/${productId}`, {
    method: "POST",
  });
}

export async function login(email, password) {
  const data = await request("/users/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
  setToken(data.access_token);
  return data;
}

export async function register(user) {
  return request("/users/register", {
    method: "POST",
    body: JSON.stringify(user),
  });
}

export async function getMe() {
  return request("/users/me");
}

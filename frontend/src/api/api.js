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
  const isFormData = options.body instanceof FormData;
  const headers = {
    ...(isFormData ? {} : { "Content-Type": "application/json" }),
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
    const error = new Error(message);
    error.status = response.status;
    throw error;
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

export async function getMyProducts() {
  return request("/products/mine");
}

export async function addToCart(productId) {
  return request(`/cart/add/${productId}`, {
    method: "POST",
  });
}

export async function recordProductView(productId) {
  return request(`/interactions/view/${productId}`, {
    method: "POST",
  });
}

export async function likeProduct(productId) {
  return request(`/interactions/like/${productId}`, {
    method: "POST",
  });
}

export async function recordSearch(query) {
  return request(`/search/?query=${encodeURIComponent(query)}`, {
    method: "POST",
  });
}

export async function visualSearchProducts(file) {
  const formData = new FormData();
  formData.append("file", file);

  return request("/search/visual", {
    method: "POST",
    body: formData,
  });
}

export async function getHomeRecommendations() {
  return request("/recommendations/home");
}

export async function getLikedSimilarRecommendations() {
  return request("/recommendations/liked-similar");
}

export async function getSimilarProducts(productId) {
  return request(`/products/${productId}/similar`);
}

export async function getOutfitRecommendations(productId) {
  return request(`/products/${productId}/outfit`);
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

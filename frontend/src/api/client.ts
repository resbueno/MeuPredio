import axios from "axios";

const TOKEN_STORAGE_KEY = "meupredio_token";

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? "http://localhost:8000",
});

export function getStoredToken(): string | null {
  return localStorage.getItem(TOKEN_STORAGE_KEY);
}

export function setStoredToken(token: string | null): void {
  if (token) {
    localStorage.setItem(TOKEN_STORAGE_KEY, token);
  } else {
    localStorage.removeItem(TOKEN_STORAGE_KEY);
  }
}

apiClient.interceptors.request.use((config) => {
  const token = getStoredToken();
  if (token) {
    config.headers.set("Authorization", `Bearer ${token}`);
  }
  return config;
});

// window.location.assign (não navigate do react-router) porque este
// interceptor roda fora de qualquer componente - mas precisa respeitar o
// BASE_URL configurado no Vite (/meupredio/), senão o redirect "escapa"
// para a raiz do domínio em vez de /meupredio/login.
const LOGIN_PATH = `${import.meta.env.BASE_URL}login`.replace(/\/{2,}/g, "/");

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (axios.isAxiosError(error) && error.response?.status === 401) {
      setStoredToken(null);
      if (!window.location.pathname.endsWith("/login")) {
        window.location.assign(LOGIN_PATH);
      }
    }
    return Promise.reject(error);
  }
);

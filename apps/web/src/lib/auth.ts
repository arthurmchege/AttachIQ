// Minimal token storage helper. Not httpOnly — deliberate MVP tradeoff,
// documented in SESSION_NOTES.md. Revisit with a Next.js Route Handler
// proxy + httpOnly cookie post-MVP if this ships beyond the demo.

const TOKEN_KEY = "attachiq_token";

export function saveToken(token: string) {
  localStorage.setItem(TOKEN_KEY, token);
}

export function getToken(): string | null {
  if (typeof window === "undefined") return null; // guards server-side render
  return localStorage.getItem(TOKEN_KEY);
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}

export function authHeader(): Record<string, string> {
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

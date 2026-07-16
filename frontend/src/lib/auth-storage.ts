// Token lives in localStorage, not an httpOnly cookie — the backend issues a
// plain Bearer JWT (no cookie-based auth support), so this is the pragmatic
// match for it. Trade-off worth knowing: localStorage is readable by any JS
// that runs on the page, so an XSS bug elsewhere in the app could steal the
// token. A production system with stricter requirements would instead have
// the backend set an httpOnly cookie, trading that risk for CSRF protection
// work instead.
const TOKEN_KEY = "url_shortener_token";

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY);
}

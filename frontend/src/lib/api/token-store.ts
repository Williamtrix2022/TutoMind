const TOKEN_KEY = "tm-token";

let memoryToken: string | null = null;

export function getToken(): string | null {
  if (memoryToken) return memoryToken;
  try {
    memoryToken = window.localStorage.getItem(TOKEN_KEY);
  } catch {
    /* almacenamiento no disponible */
  }
  return memoryToken;
}

export function setToken(token: string | null): void {
  memoryToken = token;
  try {
    if (token) window.localStorage.setItem(TOKEN_KEY, token);
    else window.localStorage.removeItem(TOKEN_KEY);
  } catch {
    /* almacenamiento no disponible */
  }
}

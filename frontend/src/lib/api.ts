/**
 * Client HTTP vers l'API FastAPI.
 *
 * Centralise : l'URL du backend, l'ajout du token JWT, la conversion des erreurs
 * de l'API en messages lisibles, et la déconnexion automatique si la session expire.
 */

import { clearToken, getToken } from "./auth";

// Variable définie dans .env.local (local) et dans les réglages Vercel (production)
const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

/** Erreur levée quand l'API répond avec un code d'erreur. */
export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

type ApiOptions = {
  method?: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
  body?: unknown;
  /** false pour les routes publiques (ex. /login) : pas de token envoyé. */
  auth?: boolean;
};

/** Extrait un message lisible du corps d'erreur FastAPI ({ detail: ... }). */
async function readErrorMessage(response: Response): Promise<string> {
  try {
    const data = await response.json();
    if (typeof data.detail === "string") return data.detail;
    // Erreur de validation (422) : FastAPI renvoie une liste d'erreurs
    if (Array.isArray(data.detail)) return "Les données envoyées sont invalides.";
  } catch {
    // Corps vide ou non JSON : on retombe sur le message générique ci-dessous
  }
  return `Une erreur est survenue (code ${response.status}).`;
}

export async function apiFetch<T>(path: string, options: ApiOptions = {}): Promise<T> {
  const { method = "GET", body, auth = true } = options;

  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (auth) {
    const token = getToken();
    if (token) headers.Authorization = `Bearer ${token}`;
  }

  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}`, {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  } catch {
    // fetch ne lève une exception qu'en cas de problème réseau (API éteinte, CORS…)
    throw new ApiError(
      "Impossible de joindre le serveur. Vérifiez votre connexion et réessayez.",
      0,
    );
  }

  if (!response.ok) {
    // Session expirée ou token invalide sur une route protégée : retour à la connexion
    if (response.status === 401 && auth) {
      clearToken();
      // apiFetch n'est pas un composant React : useRouter n'y est pas disponible,
      // on redirige donc via le navigateur (rechargement complet volontaire).
      // eslint-disable-next-line @next/next/no-location-assign-relative-destination
      window.location.href = "/login";
    }
    throw new ApiError(await readErrorMessage(response), response.status);
  }

  return (await response.json()) as T;
}

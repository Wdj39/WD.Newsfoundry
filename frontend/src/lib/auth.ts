/**
 * Gestion du token JWT dans le localStorage du navigateur.
 *
 * `localStorage` n'existe pas côté serveur : ces fonctions ne doivent être
 * appelées que côté client (gestionnaire d'événement, effet, ou via `useHasToken`).
 */

import { useSyncExternalStore } from "react";

const TOKEN_KEY = "newsfoundry_token";

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function saveToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken(): void {
  localStorage.removeItem(TOKEN_KEY);
}

/** Réagit aux modifications du localStorage faites dans un autre onglet. */
function subscribe(onChange: () => void): () => void {
  window.addEventListener("storage", onChange);
  return () => window.removeEventListener("storage", onChange);
}

/**
 * Hook React : indique si un token est enregistré.
 * Retourne `null` pendant le rendu serveur, quand la réponse n'est pas encore connue.
 */
export function useHasToken(): boolean | null {
  return useSyncExternalStore(
    subscribe,
    () => getToken() !== null,
    () => null,
  );
}

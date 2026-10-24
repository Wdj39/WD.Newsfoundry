/** Formatage des dates pour l'affichage (fuseau horaire du navigateur). */

/** 10/12/2026 */
export function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("fr-FR");
}

/** 10:31 */
export function formatTime(iso: string): string {
  return new Date(iso).toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" });
}

/** mardi 30 septembre 2025 à 09:00 */
export function formatLongDateTime(iso: string): string {
  const date = new Date(iso);
  const day = date.toLocaleDateString("fr-FR", {
    weekday: "long",
    day: "numeric",
    month: "long",
    year: "numeric",
  });
  return `${day} à ${formatTime(iso)}`;
}

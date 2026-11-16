/**
 * Page jamais affichée : la redirection de "/" vers "/chat" est déclarée dans
 * next.config.ts (redirects), avant même le rendu des pages.
 */
export default function HomePage() {
  return null;
}

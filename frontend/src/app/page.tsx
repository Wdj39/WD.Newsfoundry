import { redirect } from "next/navigation";

/** La page d'accueil renvoie vers le chat (qui redirige vers /login si besoin). */
export default function HomePage() {
  redirect("/chat");
}

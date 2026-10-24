"use client";

import { LoaderCircle } from "lucide-react";
import { useRouter } from "next/navigation";
import { ReactNode, useEffect } from "react";

import { useHasToken } from "@/lib/auth";

/**
 * Protège une page : redirige vers /login si aucun token n'est enregistré.
 *
 * La validité réelle du token est vérifiée par le backend à chaque appel API :
 * en cas de 401, `apiFetch` supprime le token et renvoie vers /login.
 */
export default function AuthGuard({ children }: { children: ReactNode }) {
  const router = useRouter();
  const hasToken = useHasToken();

  useEffect(() => {
    if (hasToken === false) router.replace("/login");
  }, [hasToken, router]);

  if (!hasToken) {
    return (
      <div className="flex min-h-screen items-center justify-center" aria-busy="true">
        <LoaderCircle className="animate-spin text-primary" aria-label="Chargement" />
      </div>
    );
  }

  return <>{children}</>;
}

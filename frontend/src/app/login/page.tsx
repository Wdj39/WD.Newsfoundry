"use client";

import { LoaderCircle } from "lucide-react";
import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";

import Logo from "@/components/Logo";
import { ApiError, apiFetch } from "@/lib/api";
import { getToken, saveToken } from "@/lib/auth";

type TokenResponse = {
  access_token: string;
  token_type: string;
};

const inputClass =
  "w-full rounded-md border border-transparent bg-gray-200 px-3 py-2 text-sm text-gray-900 " +
  "placeholder:text-gray-700 outline-none transition focus:border-primary focus:bg-white " +
  "focus:ring-2 focus:ring-primary/20";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  // Déjà connecté : inutile d'afficher le formulaire
  useEffect(() => {
    if (getToken()) router.replace("/chat");
  }, [router]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      const data = await apiFetch<TokenResponse>("/login", {
        method: "POST",
        body: { email, password },
        auth: false,
      });
      saveToken(data.access_token);
      router.replace("/chat");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Une erreur inattendue est survenue.");
      setIsLoading(false);
    }
  }

  return (
    <main className="bg-grid flex min-h-screen items-center justify-center px-4">
      <div className="w-full max-w-sm rounded-xl bg-white px-6 py-8 shadow-lg">
        <div className="text-center">
          <h1>
            <Logo size="lg" />
          </h1>
          <p className="mt-3 text-xs text-gray-700">
            Connectez-vous pour accéder à votre assistant d&apos;actualités IA
          </p>
        </div>

        <form onSubmit={handleSubmit} className="mt-6 space-y-4" noValidate>
          <div>
            <label htmlFor="email" className="mb-1.5 block text-sm text-gray-900">
              Adresse email
            </label>
            <input
              id="email"
              type="email"
              autoComplete="email"
              required
              placeholder="votre.email@exemple.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className={inputClass}
            />
          </div>

          <div>
            <label htmlFor="password" className="mb-1.5 block text-sm text-gray-900">
              Mot de passe
            </label>
            <input
              id="password"
              type="password"
              autoComplete="current-password"
              required
              placeholder="Votre mot de passe"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className={inputClass}
            />
          </div>

          {/* role="alert" : le message est lu automatiquement par les lecteurs d'écran */}
          {error && (
            <p role="alert" className="rounded-md bg-red-50 px-3 py-2 text-sm text-danger">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={isLoading || !email || !password}
            className="flex w-full items-center justify-center gap-2 rounded-md bg-gray-900 px-4 py-2.5 text-sm text-white transition hover:bg-black disabled:cursor-not-allowed disabled:opacity-60"
          >
            {isLoading && <LoaderCircle size={16} className="animate-spin" aria-hidden="true" />}
            {isLoading ? "Connexion…" : "Se connecter"}
          </button>
        </form>
      </div>
    </main>
  );
}

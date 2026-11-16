import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // La racine renvoie vers le chat (qui redirige vers /login si besoin).
  // Fait ici plutôt qu'avec redirect() dans page.tsx : avec cacheComponents,
  // un redirect() au prérendu déclenche une erreur de validation en dev.
  async redirects() {
    return [{ source: "/", destination: "/chat", permanent: false }];
  },
  cacheComponents: true,
  partialPrefetching: true,
  turbopack: {
    rules: {
      "*.css": {
        loaders: ["@tailwindcss/turbopack"],
        as: "*.css",
      },
    },
  },
};

export default nextConfig;

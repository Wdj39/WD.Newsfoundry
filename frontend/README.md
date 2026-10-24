# NewsFoundry — Frontend

Application Next.js (TypeScript, Tailwind CSS) de NewsFoundry.
Documentation complète : [`../docs/DOCUMENTATION.md`](../docs/DOCUMENTATION.md).

```bash
npm install
npm run dev      # http://localhost:3000
npm run lint     # vérification du code
npm run build    # build de production
```

L'URL du backend est lue dans `NEXT_PUBLIC_API_URL` (défaut : `http://localhost:8000`) ;
voir `.env.example`. En production (Vercel), cette variable est définie dans les réglages du projet.

## Structure

- `src/app/` — pages : `login/`, `(app)/chat/[[...chatId]]/` (discussions), `(app)/reviews/` (revues de presse)
- `src/components/` — composants d'interface (barre latérale, chat, revues de presse)
- `src/lib/` — appels à l'API (`api.ts`, `chats.ts`, `reviews.ts`), token (`auth.ts`), formatage des dates

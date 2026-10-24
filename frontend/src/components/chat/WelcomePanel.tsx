import { Bot } from "lucide-react";

const EXAMPLES = [
  "Quelles sont les dernières nouvelles en politique ?",
  "Génère une revue de presse sur la technologie",
  "Résume l'actualité économique de la semaine",
];

/** Écran d'accueil d'une nouvelle discussion (maquette Figma). */
export default function WelcomePanel({ onPickExample }: { onPickExample: (text: string) => void }) {
  return (
    <div className="mx-auto mt-16 max-w-md rounded-xl bg-white px-8 py-10 text-center shadow-sm">
      <Bot size={56} className="mx-auto text-primary" aria-hidden="true" />
      <h1 className="mt-4 text-2xl text-primary">Assistant Revue de Presse IA</h1>
      <p className="mt-6 text-sm text-gray-700">
        Posez-moi des questions sur l&apos;actualité récente ou demandez-moi de générer une revue de
        presse sur un sujet spécifique.
      </p>

      <h2 className="mt-6 text-xs font-medium text-gray-900">Exemples :</h2>
      <ul className="mt-2 space-y-1">
        {EXAMPLES.map((example) => (
          <li key={example}>
            <button
              type="button"
              onClick={() => onPickExample(example)}
              className="text-xs text-gray-700 underline-offset-2 transition hover:text-primary hover:underline"
            >
              • &quot;{example}&quot;
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}

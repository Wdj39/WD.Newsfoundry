import { Bot } from "lucide-react";

/** Loader affiché pendant que l'agent génère sa réponse (appel API lent). */
export default function TypingIndicator() {
  return (
    <div className="flex items-start gap-3" role="status" aria-live="polite">
      <span
        className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-gray-100"
        aria-hidden="true"
      >
        <Bot size={16} />
      </span>
      <div className="flex items-center gap-2 rounded-lg bg-gray-100 px-4 py-3 text-sm text-gray-700">
        <span className="flex gap-1" aria-hidden="true">
          <span className="h-2 w-2 animate-bounce rounded-full bg-gray-500 [animation-delay:-0.3s]" />
          <span className="h-2 w-2 animate-bounce rounded-full bg-gray-500 [animation-delay:-0.15s]" />
          <span className="h-2 w-2 animate-bounce rounded-full bg-gray-500" />
        </span>
        L&apos;assistant rédige sa réponse…
      </div>
    </div>
  );
}

"use client";

import { LoaderCircle } from "lucide-react";
import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useRef, useState } from "react";

import { ApiError } from "@/lib/api";
import { generateReview } from "@/lib/reviews";

type ReviewModalProps = {
  chatId: number;
  onClose: () => void;
};

/** Fenêtre « Générer une revue de presse » (maquette Figma). */
export default function ReviewModal({ chatId, onClose }: ReviewModalProps) {
  const router = useRouter();
  const [topic, setTopic] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Focus sur le champ à l'ouverture ; Échap ferme la fenêtre (sauf pendant la génération)
  useEffect(() => {
    inputRef.current?.focus();
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape" && !isGenerating) onClose();
    }
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isGenerating, onClose]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!topic.trim() || isGenerating) return;

    setError(null);
    setIsGenerating(true);
    try {
      await generateReview(chatId, topic.trim());
      router.push("/reviews");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Une erreur inattendue est survenue.");
      setIsGenerating(false);
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4"
      onClick={() => !isGenerating && onClose()}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="review-modal-title"
        className="w-full max-w-lg rounded-xl bg-white px-8 py-6 shadow-xl md:px-14"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="flex justify-end">
          <button
            type="button"
            onClick={onClose}
            disabled={isGenerating}
            className="text-sm text-gray-700 transition hover:text-gray-900 disabled:opacity-50"
          >
            Fermer
          </button>
        </div>

        <h2 id="review-modal-title" className="mt-4 text-center text-lg font-semibold text-gray-900">
          Générer une revue de presse
        </h2>
        <p className="mt-1 text-center text-sm text-gray-700">
          Donner un titre à votre revue de presse
        </p>

        <form onSubmit={handleSubmit} className="mt-8 space-y-4">
          <div>
            <label htmlFor="review-topic" className="mb-2 block text-gray-900">
              Thème de la revue de presse
            </label>
            <input
              id="review-topic"
              ref={inputRef}
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              maxLength={200}
              placeholder="Ex. : la mobilisation sociale du 24 octobre"
              disabled={isGenerating}
              className="w-full rounded-md border border-transparent bg-gray-200 px-3 py-2.5 text-sm text-gray-900 placeholder:text-gray-700 outline-none transition focus:border-primary focus:bg-white focus:ring-2 focus:ring-primary/20"
            />
          </div>

          {error && (
            <p role="alert" className="rounded-md bg-red-50 px-3 py-2 text-sm text-danger">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={isGenerating || !topic.trim()}
            className="flex w-full items-center justify-center gap-2 rounded-md bg-gray-900 px-4 py-2.5 text-white transition hover:bg-black disabled:cursor-not-allowed disabled:opacity-60"
          >
            {isGenerating && <LoaderCircle size={16} className="animate-spin" aria-hidden="true" />}
            {isGenerating ? "Génération en cours…" : "Générer"}
          </button>

          {isGenerating && (
            <p className="text-center text-xs text-gray-700" role="status">
              L&apos;IA rédige votre revue de presse, cela peut prendre quelques dizaines de secondes.
            </p>
          )}
        </form>
      </div>
    </div>
  );
}

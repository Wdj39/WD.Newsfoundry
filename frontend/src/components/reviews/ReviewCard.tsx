"use client";

import { Calendar, Check } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import ReactMarkdown from "react-markdown";

import { formatLongDateTime } from "@/lib/format";
import { Review, reviewToMarkdown } from "@/lib/reviews";

/** Carte d'une revue de presse (maquette Figma) avec bouton « Copier ». */
export default function ReviewCard({ review }: { review: Review }) {
  const [copyState, setCopyState] = useState<"idle" | "copied" | "error">("idle");

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(reviewToMarkdown(review));
      setCopyState("copied");
    } catch {
      // Le presse-papiers peut être refusé par le navigateur (permissions, page non sécurisée)
      setCopyState("error");
    }
    setTimeout(() => setCopyState("idle"), 2000);
  }

  return (
    <article className="rounded-xl bg-white px-6 py-8 md:px-10">
      <header className="flex items-start justify-between gap-4">
        <div>
          <h2 className="uppercase text-gray-900">{review.title}</h2>
          {review.generated_at && (
            <p className="mt-1 flex items-center gap-2 text-sm text-gray-700">
              <Calendar size={14} aria-hidden="true" />
              <time dateTime={review.generated_at}>{formatLongDateTime(review.generated_at)}</time>
            </p>
          )}
          <p className="mt-1 text-xs text-gray-700">
            Thème : {review.topic} ·{" "}
            <Link href={`/chat/${review.chat_id}`} className="underline hover:text-primary">
              voir la discussion
            </Link>
          </p>
        </div>
        <button
          type="button"
          onClick={handleCopy}
          className="inline-flex shrink-0 items-center gap-1.5 rounded-md bg-gray-900 px-4 py-2 text-sm text-white transition hover:bg-black"
        >
          {copyState === "copied" && <Check size={14} aria-hidden="true" />}
          {copyState === "copied" ? "Copié" : copyState === "error" ? "Échec de la copie" : "Copier"}
        </button>
      </header>

      <div className="markdown mt-6 px-0 text-sm text-gray-900 md:px-6">
        <ReactMarkdown>{review.summary}</ReactMarkdown>
      </div>

      {review.articles.length > 0 && (
        <section className="mt-6 px-0 md:px-6" aria-label="Articles cités">
          <h3 className="text-sm font-semibold text-gray-900">Articles</h3>
          <ul className="mt-3 space-y-4">
            {review.articles.map((article) => (
              <li key={article.url || article.title} className="text-sm">
                <a
                  href={article.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="font-medium text-gray-900 underline-offset-2 hover:text-primary hover:underline"
                >
                  {article.title}
                </a>
                <span className="text-gray-700"> · {article.source}</span>
                <p className="mt-1 text-gray-700">{article.summary}</p>
              </li>
            ))}
          </ul>
        </section>
      )}
    </article>
  );
}

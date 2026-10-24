/** Types et appels API des revues de presse. */

import { apiFetch } from "./api";
import { formatLongDateTime } from "./format";

export type ReviewArticle = {
  title: string;
  source: string;
  url: string;
  summary: string;
};

export type Review = {
  chat_id: number;
  topic: string;
  title: string;
  summary: string;
  articles: ReviewArticle[];
  generated_at: string | null;
};

export function listReviews(): Promise<Review[]> {
  return apiFetch<Review[]>("/reviews");
}

export function generateReview(chatId: number, topic: string): Promise<Review> {
  return apiFetch<Review>(`/chats/${chatId}/review`, { method: "POST", body: { topic } });
}

/** Version texte (Markdown) de la revue, pour le bouton « Copier ». */
export function reviewToMarkdown(review: Review): string {
  const lines = [`# ${review.title}`];
  if (review.generated_at) lines.push(`_${formatLongDateTime(review.generated_at)}_`);
  lines.push("", review.summary);
  if (review.articles.length > 0) {
    lines.push("", "## Articles");
    for (const article of review.articles) {
      lines.push("", `### [${article.title}](${article.url})`, `*${article.source}*`, "", article.summary);
    }
  }
  return lines.join("\n");
}

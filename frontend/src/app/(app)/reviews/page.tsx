"use client";

import { FileText, LoaderCircle } from "lucide-react";
import { useEffect, useState } from "react";

import AppTabs from "@/components/AppTabs";
import ReviewCard from "@/components/reviews/ReviewCard";
import { ApiError } from "@/lib/api";
import { listReviews, Review } from "@/lib/reviews";

/** Page « Revues de Presse » : revues générées à partir de toutes les discussions. */
export default function ReviewsPage() {
  const [reviews, setReviews] = useState<Review[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    listReviews()
      .then((data) => {
        if (!cancelled) setReviews(data);
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : "Impossible de charger les revues de presse.");
        }
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="flex h-full flex-col">
      <AppTabs />
      <section className="flex-1 overflow-y-auto bg-gray-300 px-6 py-8 md:px-16 lg:px-24">
        <div className="mx-auto max-w-5xl">
          <h1 className="text-2xl text-gray-900">Revues de Presse</h1>
          <p className="text-gray-700">Consultez et gérez vos revues de presse générées par l&apos;IA</p>

          <div className="mt-6 space-y-4">
            {isLoading && (
              <div className="flex justify-center pt-12" aria-busy="true">
                <LoaderCircle className="animate-spin text-primary" aria-label="Chargement des revues de presse" />
              </div>
            )}

            {error && (
              <p role="alert" className="rounded-md bg-red-50 px-4 py-3 text-sm text-danger">
                {error}
              </p>
            )}

            {!isLoading && !error && reviews.length === 0 && (
              <div className="flex flex-col items-center rounded-xl bg-white px-8 py-12 text-center">
                <FileText size={40} className="text-gray-500" aria-hidden="true" />
                <p className="mt-4 text-sm text-gray-700">
                  Aucune revue de presse pour le moment. Ouvrez une discussion et cliquez sur
                  « Générer une revue de presse ».
                </p>
              </div>
            )}

            {reviews.map((review) => (
              <ReviewCard key={review.chat_id} review={review} />
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}

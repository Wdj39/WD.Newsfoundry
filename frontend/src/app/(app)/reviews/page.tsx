import { FileText } from "lucide-react";

import AppTabs from "@/components/AppTabs";

/** Page provisoire : la génération de revues de presse arrive à l'étape 7. */
export default function ReviewsPage() {
  return (
    <div className="flex h-full flex-col">
      <AppTabs />
      <section className="flex-1 overflow-y-auto bg-gray-300 px-6 py-8 md:px-16">
        <h1 className="text-xl text-gray-900">Revues de Presse</h1>
        <p className="text-sm text-gray-700">Consultez et gérez vos revues de presse générées par l&apos;IA</p>
        <div className="mt-6 flex flex-col items-center rounded-xl bg-white px-8 py-12 text-center">
          <FileText size={40} className="text-gray-500" aria-hidden="true" />
          <p className="mt-4 text-sm text-gray-700">Aucune revue de presse pour le moment.</p>
        </div>
      </section>
    </div>
  );
}

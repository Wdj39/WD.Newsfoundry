"use client";

import { FileText, MessageSquare } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

const TABS = [
  { href: "/chat", label: "Chat", icon: MessageSquare },
  { href: "/reviews", label: "Revue de presse", icon: FileText },
];

/** Onglets « Chat » / « Revue de presse » en haut de l'écran (maquette Figma). */
export default function AppTabs() {
  const pathname = usePathname();

  return (
    <nav aria-label="Sections" className="flex h-[88px] shrink-0 items-center gap-2 border-b border-gray-200 bg-gray-50 px-6">
      {TABS.map(({ href, label, icon: Icon }) => {
        const isActive = pathname.startsWith(href);
        return (
          <Link
            key={href}
            href={href}
            aria-current={isActive ? "page" : undefined}
            className={`inline-flex items-center gap-2 rounded-md px-3 py-1.5 text-sm transition ${
              isActive ? "bg-primary font-medium text-white" : "text-gray-900 hover:bg-gray-200"
            }`}
          >
            <Icon size={16} aria-hidden="true" />
            {label}
          </Link>
        );
      })}
    </nav>
  );
}

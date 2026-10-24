"use client";

import AuthGuard from "@/components/AuthGuard";
import { ChatsProvider } from "@/components/ChatsProvider";
import Sidebar from "@/components/Sidebar";

/** Mise en page des écrans connectés : barre latérale + contenu. */
export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <AuthGuard>
      <ChatsProvider>
        <div className="flex h-screen overflow-hidden">
          <Sidebar />
          <main className="flex min-w-0 flex-1 flex-col">{children}</main>
        </div>
      </ChatsProvider>
    </AuthGuard>
  );
}

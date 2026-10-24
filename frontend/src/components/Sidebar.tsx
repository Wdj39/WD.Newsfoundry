"use client";

import { LoaderCircle, LogOut } from "lucide-react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";

import Logo from "@/components/Logo";
import { useChats } from "@/components/ChatsProvider";
import { clearToken } from "@/lib/auth";
import { formatDate } from "@/lib/format";

/** Barre latérale : logo, liste des discussions et déconnexion (maquette Figma). */
export default function Sidebar() {
  const router = useRouter();
  const params = useParams<{ chatId?: string[] }>();
  const activeChatId = params.chatId?.[0] ? Number(params.chatId[0]) : null;
  const { chats, isLoading, error } = useChats();

  function handleLogout() {
    clearToken();
    router.replace("/login");
  }

  return (
    <aside className="flex h-screen w-64 shrink-0 flex-col border-r border-gray-200 bg-gray-50 md:w-80">
      <div className="flex h-[88px] items-center border-b border-gray-200 px-6">
        <Link href="/chat" aria-label="NewsFoundry, nouvelle discussion">
          <Logo />
        </Link>
      </div>

      <nav aria-label="Discussions" className="flex-1 overflow-y-auto">
        {isLoading && (
          <div className="flex justify-center p-6" aria-busy="true">
            <LoaderCircle className="animate-spin text-primary" aria-label="Chargement des discussions" />
          </div>
        )}

        {error && (
          <p role="alert" className="m-4 rounded-md bg-red-50 px-3 py-2 text-sm text-danger">
            {error}
          </p>
        )}

        {!isLoading && !error && chats.length === 0 && (
          <p className="p-6 text-sm text-gray-700">Aucune discussion pour le moment.</p>
        )}

        <ul>
          {chats.map((chat) => {
            const isActive = chat.id === activeChatId;
            return (
              <li key={chat.id}>
                <Link
                  href={`/chat/${chat.id}`}
                  aria-current={isActive ? "page" : undefined}
                  className={`block border-b border-gray-200 px-6 py-4 transition hover:bg-white ${
                    isActive ? "bg-gray-200 hover:bg-gray-200" : ""
                  }`}
                >
                  <span className="block text-gray-900">Discussion du</span>
                  <span className="block text-xs text-gray-700">{formatDate(chat.created_at)}</span>
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      <div className="p-6">
        <button
          type="button"
          onClick={handleLogout}
          className="inline-flex items-center gap-2 text-sm text-gray-900 transition hover:text-primary"
        >
          <LogOut size={18} aria-hidden="true" />
          Se déconnecter
        </button>
      </div>
    </aside>
  );
}

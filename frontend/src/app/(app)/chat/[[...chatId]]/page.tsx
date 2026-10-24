"use client";

import { useParams } from "next/navigation";

import ChatView from "@/components/chat/ChatView";

/**
 * /chat      → nouvelle discussion
 * /chat/{id} → discussion existante
 */
export default function ChatPage() {
  const params = useParams<{ chatId?: string[] }>();
  const rawId = params.chatId?.[0];
  const chatId = rawId && /^\d+$/.test(rawId) ? Number(rawId) : null;

  // key : chaque discussion a son propre état (messages, saisie, erreurs)
  return <ChatView key={chatId ?? "new"} chatId={chatId} />;
}

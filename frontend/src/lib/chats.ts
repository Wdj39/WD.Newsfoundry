/** Types et appels API des discussions. */

import { apiFetch } from "./api";

export type MessageRole = "user" | "assistant";

export type Message = {
  role: MessageRole;
  content: string;
  created_at: string;
};

export type ChatSummary = {
  id: number;
  created_at: string;
  updated_at: string;
};

export type ChatDetail = ChatSummary & {
  messages: Message[];
};

export function listChats(): Promise<ChatSummary[]> {
  return apiFetch<ChatSummary[]>("/chats");
}

export function createChat(): Promise<ChatSummary> {
  return apiFetch<ChatSummary>("/chats", { method: "POST" });
}

export function getChat(chatId: number): Promise<ChatDetail> {
  return apiFetch<ChatDetail>(`/chats/${chatId}`);
}

export function sendMessage(chatId: number, content: string): Promise<Message> {
  return apiFetch<Message>(`/chats/${chatId}/messages`, {
    method: "POST",
    body: { content },
  });
}

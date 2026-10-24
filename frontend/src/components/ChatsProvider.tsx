"use client";

import { createContext, ReactNode, useCallback, useContext, useEffect, useState } from "react";

import { ApiError } from "@/lib/api";
import { ChatSummary, listChats } from "@/lib/chats";

type ChatsContextValue = {
  chats: ChatSummary[];
  isLoading: boolean;
  error: string | null;
  /** Recharge la liste (ex. après la création d'une discussion). */
  refreshChats: () => Promise<void>;
};

const ChatsContext = createContext<ChatsContextValue | null>(null);

/**
 * Partage la liste des discussions entre la barre latérale et la zone de chat,
 * pour que la barre latérale se mette à jour quand une discussion est créée.
 */
export function ChatsProvider({ children }: { children: ReactNode }) {
  const [chats, setChats] = useState<ChatSummary[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refreshChats = useCallback(async () => {
    try {
      setChats(await listChats());
      setError(null);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Impossible de charger les discussions.");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    // Chargement initial : les mises à jour d'état ont lieu après la réponse de l'API
    // eslint-disable-next-line react-hooks/set-state-in-effect
    refreshChats();
  }, [refreshChats]);

  return (
    <ChatsContext.Provider value={{ chats, isLoading, error, refreshChats }}>
      {children}
    </ChatsContext.Provider>
  );
}

export function useChats(): ChatsContextValue {
  const context = useContext(ChatsContext);
  if (!context) throw new Error("useChats doit être utilisé dans un <ChatsProvider>.");
  return context;
}

"use client";

import { ArrowLeft, FileText, LoaderCircle } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";

import AppTabs from "@/components/AppTabs";
import { useChats } from "@/components/ChatsProvider";
import ChatInput from "@/components/chat/ChatInput";
import MessageBubble from "@/components/chat/MessageBubble";
import TypingIndicator from "@/components/chat/TypingIndicator";
import WelcomePanel from "@/components/chat/WelcomePanel";
import ReviewModal from "@/components/reviews/ReviewModal";
import { ApiError } from "@/lib/api";
import { createChat, getChat, Message, sendMessage } from "@/lib/chats";

/**
 * Historique des discussions tout juste créées dans cet onglet.
 * Après le premier message d'une nouvelle discussion, on navigue vers /chat/{id} :
 * ce cache évite de recharger depuis l'API un historique qu'on connaît déjà.
 */
const freshHistories = new Map<number, Message[]>();

function errorMessage(err: unknown): string {
  return err instanceof ApiError ? err.message : "Une erreur inattendue est survenue.";
}

/** Zone de chat : nouvelle discussion (chatId = null) ou discussion existante. */
export default function ChatView({ chatId }: { chatId: number | null }) {
  const router = useRouter();
  const { refreshChats } = useChats();

  const cached = chatId !== null ? freshHistories.get(chatId) : undefined;
  const [messages, setMessages] = useState<Message[]>(cached ?? []);
  const [isLoadingHistory, setIsLoadingHistory] = useState(chatId !== null && !cached);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [input, setInput] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [sendError, setSendError] = useState<string | null>(null);
  const [isReviewModalOpen, setIsReviewModalOpen] = useState(false);

  // Discussion créée lors d'un envoi qui a ensuite échoué : on la réutilise au
  // prochain essai pour ne pas créer de discussions vides en double.
  const createdChatId = useRef<number | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Chargement de l'historique d'une discussion existante
  useEffect(() => {
    if (chatId === null || freshHistories.has(chatId)) return;

    let cancelled = false;
    getChat(chatId)
      .then((chat) => {
        if (!cancelled) setMessages(chat.messages);
      })
      .catch((err) => {
        if (!cancelled) setLoadError(errorMessage(err));
      })
      .finally(() => {
        if (!cancelled) setIsLoadingHistory(false);
      });

    return () => {
      cancelled = true;
    };
  }, [chatId]);

  // Défilement automatique vers le dernier message
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages.length, isSending]);

  async function handleSend() {
    const content = input.trim();
    if (!content || isSending) return;

    // Affichage immédiat du message (mise à jour « optimiste »)
    const userMessage: Message = { role: "user", content, created_at: new Date().toISOString() };
    const previousMessages = messages;
    setMessages([...previousMessages, userMessage]);
    setInput("");
    setSendError(null);
    setIsSending(true);

    try {
      let targetId = chatId ?? createdChatId.current;
      if (targetId === null) {
        targetId = (await createChat()).id;
        createdChatId.current = targetId;
      }

      const reply = await sendMessage(targetId, content);
      const updatedMessages = [...previousMessages, userMessage, reply];
      setMessages(updatedMessages);
      refreshChats();

      if (chatId === null) {
        freshHistories.set(targetId, updatedMessages);
        router.replace(`/chat/${targetId}`);
      }
    } catch (err) {
      // Échec : on retire le message et on le remet dans le champ pour pouvoir réessayer
      setMessages(previousMessages);
      setInput(content);
      setSendError(errorMessage(err));
      // La discussion a pu être créée avant l'échec : on met la barre latérale à jour
      if (createdChatId.current !== null) refreshChats();
    } finally {
      setIsSending(false);
    }
  }

  // Un clic sur un exemple remplit le champ et y place le curseur
  function handlePickExample(example: string) {
    setInput(example);
    inputRef.current?.focus();
  }

  const isNewChat = chatId === null;
  const showWelcome = !isLoadingHistory && !loadError && messages.length === 0 && !isSending;

  return (
    <div className="flex h-full flex-col">
      {isNewChat ? (
        <AppTabs />
      ) : (
        <header className="flex h-[88px] shrink-0 items-center border-b border-gray-200 bg-gray-50 px-4">
          <Link
            href="/chat"
            className="flex items-center gap-3 rounded-md p-2 transition hover:bg-gray-200"
          >
            <ArrowLeft size={20} aria-hidden="true" />
            <span>
              <span className="block text-gray-900">Nouvelle discussion</span>
              <span className="block text-sm text-gray-700">Conversation active</span>
            </span>
          </Link>
          <button
            type="button"
            onClick={() => setIsReviewModalOpen(true)}
            disabled={messages.length === 0 || isSending}
            title={messages.length === 0 ? "Échangez d'abord avec l'assistant" : undefined}
            className="ml-auto inline-flex items-center gap-2 rounded-md bg-primary px-6 py-3 text-white transition hover:bg-primary-hover disabled:cursor-not-allowed disabled:bg-gray-400"
          >
            <FileText size={18} aria-hidden="true" />
            Générer une revue de presse
          </button>
        </header>
      )}

      <section aria-label="Messages" className="flex-1 overflow-y-auto bg-gray-300 px-6 py-8 md:px-16">
        {isLoadingHistory && (
          <div className="flex justify-center pt-16" aria-busy="true">
            <LoaderCircle className="animate-spin text-primary" aria-label="Chargement de la discussion" />
          </div>
        )}

        {loadError && (
          <p role="alert" className="mx-auto max-w-md rounded-md bg-red-50 px-4 py-3 text-sm text-danger">
            {loadError}
          </p>
        )}

        {showWelcome && <WelcomePanel onPickExample={handlePickExample} />}

        <div className="mx-auto flex max-w-4xl flex-col gap-6">
          {messages.map((message, index) => (
            <MessageBubble key={`${message.created_at}-${index}`} message={message} />
          ))}
          {isSending && <TypingIndicator />}
        </div>
        <div ref={bottomRef} />
      </section>

      {sendError && (
        <p role="alert" className="bg-red-50 px-6 py-2 text-sm text-danger md:px-16">
          {sendError}
        </p>
      )}

      <ChatInput
        value={input}
        onChange={setInput}
        onSubmit={handleSend}
        disabled={isSending || isLoadingHistory || loadError !== null}
        inputRef={inputRef}
      />

      {isReviewModalOpen && chatId !== null && (
        <ReviewModal chatId={chatId} onClose={() => setIsReviewModalOpen(false)} />
      )}
    </div>
  );
}

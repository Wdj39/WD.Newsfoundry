"use client";

import { Send } from "lucide-react";
import { FormEvent, KeyboardEvent, RefObject } from "react";

type ChatInputProps = {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  disabled: boolean;
  inputRef?: RefObject<HTMLTextAreaElement | null>;
};

/** Zone de saisie : Entrée envoie, Maj+Entrée ajoute une ligne. */
export default function ChatInput({ value, onChange, onSubmit, disabled, inputRef }: ChatInputProps) {
  const canSend = !disabled && value.trim().length > 0;

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (canSend) onSubmit();
  }

  function handleKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      if (canSend) onSubmit();
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex items-start gap-2 bg-white px-6 py-4 md:px-16">
      <label htmlFor="chat-input" className="sr-only">
        Votre message
      </label>
      <textarea
        id="chat-input"
        ref={inputRef}
        rows={2}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Tapez votre message ici..."
        maxLength={4000}
        className="min-h-[60px] flex-1 resize-none rounded-md border border-transparent bg-gray-100 px-3 py-2 text-sm text-gray-900 placeholder:text-gray-700 outline-none transition focus:border-primary focus:ring-2 focus:ring-primary/20"
      />
      <button
        type="submit"
        disabled={!canSend}
        aria-label="Envoyer le message"
        className="flex h-10 w-12 items-center justify-center rounded-md bg-primary text-white transition hover:bg-primary-hover disabled:cursor-not-allowed disabled:bg-gray-400"
      >
        <Send size={18} aria-hidden="true" />
      </button>
    </form>
  );
}

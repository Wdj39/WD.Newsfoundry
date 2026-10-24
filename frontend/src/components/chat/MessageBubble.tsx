import { Bot, User } from "lucide-react";
import ReactMarkdown from "react-markdown";

import { Message } from "@/lib/chats";
import { formatTime } from "@/lib/format";

/**
 * Bulle de message (maquette Figma) :
 * - utilisateur : bulle sombre à droite + avatar ;
 * - assistant : bulle claire à gauche + icône robot, contenu Markdown rendu.
 */
export default function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === "user";

  return (
    <div className={`flex items-start gap-3 ${isUser ? "flex-row-reverse" : ""}`}>
      <span
        className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${
          isUser ? "bg-black text-white" : "bg-gray-100 text-gray-900"
        }`}
        aria-hidden="true"
      >
        {isUser ? <User size={16} /> : <Bot size={16} />}
      </span>

      <div
        className={`max-w-[75%] rounded-lg px-4 py-3 ${
          isUser ? "bg-gray-900 text-white" : "bg-gray-100 text-gray-900"
        }`}
      >
        <p className="sr-only">{isUser ? "Vous :" : "Assistant :"}</p>
        {isUser ? (
          <p className="whitespace-pre-wrap">{message.content}</p>
        ) : (
          <div className="markdown">
            <ReactMarkdown>{message.content}</ReactMarkdown>
          </div>
        )}
        <p className={`mt-2 text-xs ${isUser ? "text-gray-400" : "text-gray-700"}`}>
          <time dateTime={message.created_at}>{formatTime(message.created_at)}</time>
        </p>
      </div>
    </div>
  );
}

// frontend/src/components/chat/MessageBubble.tsx

import { memo } from "react";
import type { ChatMessage } from "../../types/chat";
import { StreamingText } from "./StreamingText";
import { ToolCallCard } from "./ToolCallCard";

interface MessageBubbleProps {
  message: ChatMessage;
  isStreaming?: boolean;
}

export const MessageBubble = memo(function MessageBubble({ message, isStreaming = false }: MessageBubbleProps) {
  const isUser = message.role === "user";

  return (
    <div className={`flex gap-3 px-4 py-3 ${isUser ? "bg-bg-secondary" : ""}`}>
      <div className="w-6 h-6 rounded flex items-center justify-center text-xs shrink-0 bg-bg-tertiary">
        {isUser ? "U" : "A"}
      </div>
      <div className="flex-1 min-w-0">
        {isUser ? (
          <div className="text-sm whitespace-pre-wrap">{message.content}</div>
        ) : (
          <>
            <StreamingText text={message.content} isStreaming={isStreaming} />
            {message.toolCalls?.map((tc) => (
              <ToolCallCard key={tc.id} toolCall={tc} />
            ))}
          </>
        )}
      </div>
    </div>
  );
});

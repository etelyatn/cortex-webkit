// frontend/src/components/chat/ChatPanel.tsx

import { useEffect, useRef } from "react";
import { useChatStore } from "../../stores/chatStore";
import { useChatSession } from "../../hooks/useChatSession";
import { MessageBubble } from "./MessageBubble";
import { StreamingText } from "./StreamingText";
import { ToolCallCard } from "./ToolCallCard";
import { ChatInput } from "./ChatInput";
import { api } from "../../lib/api";

export function ChatPanel() {
  const activeSessionId = useChatStore((s) => s.activeSessionId);
  const messages = useChatStore((s) => s.messages);
  const streamingText = useChatStore((s) => s.streamingText);
  const streamingToolCalls = useChatStore((s) => s.streamingToolCalls);
  const isStreaming = useChatStore((s) => s.isStreaming);
  const chatWsStatus = useChatStore((s) => s.chatWsStatus);
  const setActiveSession = useChatStore((s) => s.setActiveSession);
  const clearMessages = useChatStore((s) => s.clearMessages);

  const { sendMessage, cancelTurn } = useChatSession(activeSessionId);

  const sentinelRef = useRef<HTMLDivElement>(null);
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const isAtBottomRef = useRef(true);

  useEffect(() => {
    const sentinel = sentinelRef.current;
    if (!sentinel) return;

    const observer = new IntersectionObserver(
      ([entry]) => { isAtBottomRef.current = entry.isIntersecting; },
      { threshold: 0.1 },
    );
    observer.observe(sentinel);
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    if (isAtBottomRef.current) {
      sentinelRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages.length, streamingText]);

  useEffect(() => {
    if (!activeSessionId) {
      api.createSession().then((session) => {
        setActiveSession(session.id);
      });
    }
  }, [activeSessionId, setActiveSession]);

  const handleNewChat = async () => {
    clearMessages();
    const session = await api.createSession();
    setActiveSession(session.id);
  };

  return (
    <div className="h-full flex flex-col">
      <div className="px-4 py-2 flex items-center border-b border-border bg-bg-secondary shrink-0">
        <span className="text-xs text-text-secondary font-mono">
          {activeSessionId ? activeSessionId.slice(0, 8) : "No session"}
        </span>
        <button
          onClick={handleNewChat}
          className="ml-auto text-xs text-accent hover:text-accent/80"
        >
          + New Chat
        </button>
      </div>

      <div ref={scrollContainerRef} className="flex-1 overflow-y-auto">
        {messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}

        {isStreaming && (streamingText || streamingToolCalls.length > 0) && (
          <div className="flex gap-3 px-4 py-3">
            <div className="w-6 h-6 rounded flex items-center justify-center text-xs shrink-0 bg-bg-tertiary">
              A
            </div>
            <div className="flex-1 min-w-0">
              {streamingText && (
                <StreamingText text={streamingText} isStreaming={true} />
              )}
              {streamingToolCalls.map((tc) => (
                <ToolCallCard key={tc.id} toolCall={tc} />
              ))}
            </div>
          </div>
        )}

        <div ref={sentinelRef} />
      </div>

      <ChatInput
        onSend={sendMessage}
        onCancel={cancelTurn}
        isProcessing={isStreaming}
        disabled={chatWsStatus !== "connected"}
      />

      <div className="px-4 py-1 text-xs text-text-secondary bg-bg-secondary border-t border-border">
        Claude CLI · {chatWsStatus === "connected" ? "Connected" : chatWsStatus}
      </div>
    </div>
  );
}

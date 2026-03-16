// frontend/src/components/chat/ChatInput.tsx

import { useState, useRef, useCallback } from "react";

interface ChatInputProps {
  onSend: (content: string) => void;
  onCancel: () => void;
  isProcessing: boolean;
  disabled: boolean;
}

export function ChatInput({ onSend, onCancel, isProcessing, disabled }: ChatInputProps) {
  const [value, setValue] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSubmit = useCallback(() => {
    const trimmed = value.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setValue("");
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  }, [value, disabled, onSend]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setValue(e.target.value);
    const el = e.target;
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 200) + "px";
  };

  return (
    <div className="border-t border-border p-3 bg-bg-secondary">
      <div className="flex gap-2 items-end">
        <textarea
          ref={textareaRef}
          value={value}
          onChange={handleInput}
          onKeyDown={handleKeyDown}
          placeholder="Send a message..."
          disabled={disabled}
          rows={1}
          className="flex-1 bg-bg-tertiary border border-border rounded px-3 py-2 text-sm resize-none
                     focus:outline-none focus:border-accent placeholder:text-text-secondary
                     disabled:opacity-50"
        />
        {isProcessing ? (
          <button
            onClick={onCancel}
            className="px-4 py-2 bg-error/20 text-error text-sm rounded border border-error/40 hover:bg-error/30"
          >
            Cancel
          </button>
        ) : (
          <button
            onClick={handleSubmit}
            disabled={disabled || !value.trim()}
            className="px-4 py-2 bg-accent text-white text-sm rounded hover:bg-accent/80
                       disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Send
          </button>
        )}
      </div>
    </div>
  );
}

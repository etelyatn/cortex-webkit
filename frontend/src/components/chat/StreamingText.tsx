// frontend/src/components/chat/StreamingText.tsx

import { useState, useEffect, useRef, memo } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { hljs } from "../../lib/markdown";

interface StreamingTextProps {
  text: string;
  isStreaming: boolean;
}

export const StreamingText = memo(function StreamingText({ text, isStreaming }: StreamingTextProps) {
  const [rendered, setRendered] = useState(text);
  const timerRef = useRef<number | null>(null);

  useEffect(() => {
    if (!isStreaming) {
      setRendered(text);
      return;
    }

    if (timerRef.current !== null) {
      clearTimeout(timerRef.current);
    }
    timerRef.current = window.setTimeout(() => {
      setRendered(text);
      timerRef.current = null;
    }, 50);

    return () => {
      if (timerRef.current !== null) clearTimeout(timerRef.current);
    };
  }, [text, isStreaming]);

  return (
    <div className="prose prose-invert max-w-none text-sm">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          code({ className, children, ...props }) {
            const match = /language-(\w+)/.exec(className || "");
            const code = String(children).replace(/\n$/, "");
            if (match) {
              const highlighted = hljs.getLanguage(match[1])
                ? hljs.highlight(code, { language: match[1] }).value
                : code;
              return (
                <pre className="bg-bg-primary rounded p-3 overflow-x-auto text-xs">
                  <code dangerouslySetInnerHTML={{ __html: highlighted }} />
                </pre>
              );
            }
            return (
              <code className="bg-bg-primary px-1 py-0.5 rounded text-xs font-mono" {...props}>
                {children}
              </code>
            );
          },
        }}
      >
        {rendered}
      </ReactMarkdown>
    </div>
  );
});

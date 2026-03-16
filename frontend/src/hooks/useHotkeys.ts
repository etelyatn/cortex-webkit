// frontend/src/hooks/useHotkeys.ts

import { useEffect } from "react";

type HotkeyHandler = (e: KeyboardEvent) => void;

interface Hotkey {
  key: string;
  ctrl?: boolean;
  shift?: boolean;
  handler: HotkeyHandler;
}

export function useHotkeys(hotkeys: Hotkey[]) {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      for (const hk of hotkeys) {
        const ctrlMatch = hk.ctrl ? (e.ctrlKey || e.metaKey) : !(e.ctrlKey || e.metaKey);
        const shiftMatch = hk.shift ? e.shiftKey : !e.shiftKey;
        if (e.key === hk.key && ctrlMatch && shiftMatch) {
          e.preventDefault();
          hk.handler(e);
          return;
        }
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [hotkeys]);
}

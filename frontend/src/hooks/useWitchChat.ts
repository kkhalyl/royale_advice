import { useCallback, useEffect, useRef, useState } from "react";
import type { Player } from "../api/clash";
import { askWitch, type AdviceMode, type ChatMessage } from "../api/witch";

export interface DisplayMessage extends ChatMessage {
  /** texto curto mostrado no lugar do prompt interno (ex.: "Poção de análise") */
  label?: string;
}

export function useWitchChat(player: Player | undefined) {
  const [messages, setMessages] = useState<DisplayMessage[]>([]);
  const [streaming, setStreaming] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const messagesRef = useRef(messages);
  messagesRef.current = messages;
  const streamingRef = useRef(streaming);
  streamingRef.current = streaming;

  useEffect(() => () => abortRef.current?.abort(), []);

  const ask = useCallback(
    async (content: string, mode: AdviceMode, label?: string) => {
      if (!player) return;
      abortRef.current?.abort();
      const controller = new AbortController();
      abortRef.current = controller;

      const history: DisplayMessage[] = [...messagesRef.current, { role: "user", content, label }];
      setMessages(history);
      setStreaming("");
      setError(null);

      try {
        const reply = await askWitch({
          player,
          mode,
          messages: history.map(({ role, content }) => ({ role, content })),
          onChunk: setStreaming,
          signal: controller.signal,
        });
        setMessages((h) => [...h, { role: "assistant", content: reply }]);
      } catch (e) {
        if ((e as Error).name === "AbortError") return;
        setError((e as Error).message);
      } finally {
        if (abortRef.current === controller) setStreaming(null);
      }
    },
    [player]
  );

  const stop = useCallback(() => {
    const partial = streamingRef.current;
    abortRef.current?.abort();
    abortRef.current = null;
    if (partial) setMessages((h) => [...h, { role: "assistant", content: partial }]);
    setStreaming(null);
  }, []);

  const reset = useCallback(() => {
    abortRef.current?.abort();
    setMessages([]);
    setStreaming(null);
    setError(null);
  }, []);

  return { messages, streaming, error, busy: streaming !== null, ask, stop, reset };
}

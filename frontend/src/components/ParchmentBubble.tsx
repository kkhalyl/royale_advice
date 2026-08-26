import { useState } from "react";
import type { FormEvent, ReactNode } from "react";
import styles from "./ParchmentBubble.module.css";

export interface ParchmentBubbleProps {
  label: string;
  children: ReactNode;
  /** When provided, renders an inline free-text question row. */
  onAsk?: (question: string) => void;
  asking?: boolean;
  askPlaceholder?: string;
  width?: number;
}

export function ParchmentBubble({
  label,
  children,
  onAsk,
  asking,
  askPlaceholder = "...ou pergunte livremente a bruxa aqui",
  width,
}: ParchmentBubbleProps) {
  const [question, setQuestion] = useState("");

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const trimmed = question.trim();
    if (!trimmed || !onAsk) return;
    onAsk(trimmed);
    setQuestion("");
  }

  return (
    <div className={styles.bubble} style={width ? { width } : undefined}>
      <div className={styles.label}>{label}</div>
      <div className={styles.content}>{children}</div>

      {onAsk && (
        <form className={styles.askRow} onSubmit={handleSubmit}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#8a6a20" strokeWidth="2">
            <path d="M12 2l2.4 6.6L21 11l-6.6 2.4L12 20l-2.4-6.6L3 11l6.6-2.4L12 2z" />
          </svg>
          <input
            className={styles.askInput}
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder={askPlaceholder}
            disabled={asking}
          />
          <button className={styles.askSend} type="submit" disabled={asking || !question.trim()}>
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#4a2e05" strokeWidth="2.4">
              <path d="M5 12h13M13 6l6 6-6 6" />
            </svg>
          </button>
        </form>
      )}
    </div>
  );
}

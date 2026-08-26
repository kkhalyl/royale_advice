import type { ReactElement } from "react";
import styles from "./ReadingPills.module.css";

export type ReadingKey = "analise" | "dicas" | "trocas" | "resumo";

const PILLS: { key: ReadingKey; label: string; icon: ReactElement }[] = [
  {
    key: "analise",
    label: "Análise",
    icon: (
      <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <circle cx="12" cy="12" r="8" />
        <path d="M12 8v4l3 2" />
      </svg>
    ),
  },
  {
    key: "dicas",
    label: "Dicas",
    icon: (
      <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M4 4h13l3 3v13H4z" />
        <line x1="8" y1="9" x2="16" y2="9" />
        <line x1="8" y1="13" x2="16" y2="13" />
      </svg>
    ),
  },
  {
    key: "trocas",
    label: "Trocas Sugeridas",
    icon: (
      <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M9 3h6l1 5-4 3-4-3 1-5Z" />
        <path d="M8 11c-2 3-2 6 0 8s10 2 12 0 2-5 0-8" />
      </svg>
    ),
  },
  {
    key: "resumo",
    label: "Resumo",
    icon: (
      <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M12 2l2.4 6.6L21 11l-6.6 2.4L12 20l-2.4-6.6L3 11l6.6-2.4L12 2z" />
      </svg>
    ),
  },
];

export interface ReadingPillsProps {
  active: ReadingKey;
  onSelect: (key: ReadingKey) => void;
}

export function ReadingPills({ active, onSelect }: ReadingPillsProps) {
  return (
    <div className={styles.row}>
      {PILLS.map((pill) => (
        <button
          key={pill.key}
          type="button"
          className={`${styles.pill} ${active === pill.key ? styles.active : ""}`}
          onClick={() => onSelect(pill.key)}
        >
          {pill.icon}
          <span>{pill.label}</span>
        </button>
      ))}
    </div>
  );
}

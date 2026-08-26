import styles from "./IssueBadge.module.css";

export interface IssueBadgeProps {
  message: string;
  /** Drives the icon/color - never render the raw `code` field as text to the user. */
  kind: "issue" | "strength";
}

export function IssueBadge({ message, kind }: IssueBadgeProps) {
  const color = kind === "issue" ? "var(--error)" : "var(--cauldron-glow)";

  return (
    <div className={styles.row}>
      {kind === "issue" ? (
        <svg
          className={styles.icon}
          width="22"
          height="22"
          viewBox="0 0 24 24"
          fill="none"
          stroke={color}
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0Z" />
          <line x1="12" y1="9" x2="12" y2="13" />
          <line x1="12" y1="17" x2="12.01" y2="17" />
        </svg>
      ) : (
        <svg
          className={styles.icon}
          width="22"
          height="22"
          viewBox="0 0 24 24"
          fill="none"
          stroke={color}
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="M12 2 4 6v6c0 5 3.5 8.7 8 10 4.5-1.3 8-5 8-10V6l-8-4Z" />
          <path d="m9 12 2 2 4-4" />
        </svg>
      )}
      <div className={styles.text}>{message}</div>
    </div>
  );
}

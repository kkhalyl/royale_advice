import styles from "./LoadingState.module.css";

export interface LoadingStateProps {
  text?: string;
}

export function LoadingState({ text = "a bruxa esta remexendo o caldeirao..." }: LoadingStateProps) {
  return (
    <div className={styles.wrap}>
      <div className={styles.glow} />
      <div className={styles.text}>{text}</div>
    </div>
  );
}

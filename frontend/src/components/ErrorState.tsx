import styles from "./ErrorState.module.css";

export interface ErrorStateProps {
  message: string;
}

/** In-theme error, in the witch's voice - never a raw stack trace or JSON. */
export function ErrorState({ message }: ErrorStateProps) {
  return <div className={styles.wrap}>"{message}"</div>;
}

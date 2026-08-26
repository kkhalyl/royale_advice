import styles from "./CardFrame.module.css";

function rarityClass(rarity: string): string {
  switch (rarity.toLowerCase()) {
    case "rare":
      return styles["rarity-rare"];
    case "epic":
      return styles["rarity-epic"];
    case "legendary":
      return styles["rarity-legendary"];
    default:
      return styles["rarity-common"];
  }
}

export interface CardFrameProps {
  name: string;
  elixir?: number;
  rarity?: string;
  iconUrl?: string | null;
  /** Renders a dashed "?" placeholder for an unresolved/incomplete deck slot. */
  incomplete?: boolean;
}

export function CardFrame({ name, elixir, rarity, iconUrl, incomplete }: CardFrameProps) {
  if (incomplete) {
    return (
      <div className={styles.card}>
        <div className={`${styles.frame} ${styles.incomplete}`}>
          <span className={styles.incompleteMark}>?</span>
        </div>
        <div className={`${styles.name} ${styles.incompleteName}`}>incerto...</div>
      </div>
    );
  }

  return (
    <div className={styles.card}>
      <div className={`${styles.frame} ${rarityClass(rarity ?? "common")}`}>
        {typeof elixir === "number" && <div className={styles.elixir}>{elixir}</div>}
        {iconUrl && (
          <div className={styles.artwork}>
            <img src={iconUrl} alt={name} />
          </div>
        )}
      </div>
      <div className={styles.name}>{name}</div>
    </div>
  );
}

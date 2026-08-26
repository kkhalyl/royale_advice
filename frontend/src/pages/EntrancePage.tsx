import { useState } from "react";
import type { FormEvent } from "react";
import { useNavigate, Link } from "react-router-dom";
import { ParchmentBubble } from "../components/ParchmentBubble";
import styles from "./EntrancePage.module.css";

export function EntrancePage() {
  const [tag, setTag] = useState("");
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const trimmed = tag.trim().replace(/^#/, "");
    if (!trimmed) {
      setError("Digite uma tag para eu consultar os astros.");
      return;
    }
    setError(null);
    navigate(`/player/${encodeURIComponent(trimmed)}`);
  }

  return (
    <div className={styles.root}>
      <div className={styles.title}>
        <div className={styles.titleMain}>Royal Advice</div>
        <div className={styles.titleSub}>a taverna da bruxa das cartas</div>
      </div>

      <div className={styles.witch}>
        <div className={styles.witchGlow} />
        <div className={styles.staff} />
        <div className={styles.staffOrb} />
        <div className={styles.robe} />
        <div className={styles.belt} />
        <div className={styles.hood} />
        <div className={styles.face} />
        <div className={`${styles.eye} ${styles.eyeLeft}`} />
        <div className={`${styles.eye} ${styles.eyeRight}`} />
      </div>

      <div className={styles.bubble}>
        <ParchmentBubble label="a bruxa fala">
          "Entre, viajante... sente-se. O que te traz a minha taverna nesta noite de batalhas?"
        </ParchmentBubble>
      </div>

      <form className={styles.formArea} onSubmit={handleSubmit}>
        <input
          className={styles.input}
          value={tag}
          onChange={(e) => setTag(e.target.value)}
          placeholder="Sua tag... (ex: #2Y8VLPP2)"
        />
        {error && <div style={{ color: "var(--error)", marginBottom: 12, fontSize: 14 }}>{error}</div>}
        <button className={styles.button} type="submit">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="var(--gold-text)">
            <path d="M12 2l2.4 6.6L21 11l-6.6 2.4L12 20l-2.4-6.6L3 11l6.6-2.4L12 2z" />
          </svg>
          Consultar os astros
        </button>
      </form>

      <Link className={styles.navLink} to="/cards">
        ver o grimório de cartas
      </Link>
    </div>
  );
}

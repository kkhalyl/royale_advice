import type { CSSProperties } from "react";
import type { Card } from "../api/clash";
import { cardImage, displayLevel } from "../lib/cards";
import "./ClashCard.css";

interface Props {
  card: Card;
  commonMax: number;
  size?: "sm" | "md" | "lg";
  /** atraso da animação de "revelação" (ms); omita para não animar */
  revealDelay?: number;
}

export function ClashCard({ card, commonMax, size = "md", revealDelay }: Props) {
  const evolved = (card.evolutionLevel ?? 0) > 0;
  const level = displayLevel(card, commonMax);
  const style = revealDelay !== undefined ? ({ "--delay": `${revealDelay}ms` } as CSSProperties) : undefined;

  return (
    <figure
      className={`cc cc--${size} cc--${card.rarity} ${evolved ? "cc--evo" : ""} ${
        revealDelay !== undefined ? "cc--reveal" : ""
      }`}
      style={style}
      title={`${card.name}, nível ${level}${evolved ? " (evoluída)" : ""}`}
    >
      <div className="cc__frame">
        <img className="cc__img" src={cardImage(card)} alt={card.name} loading="lazy" draggable={false} />
        {typeof card.elixirCost === "number" && (
          <span className="cc__elixir" aria-label={`${card.elixirCost} de elixir`}>
            {card.elixirCost}
          </span>
        )}
      </div>
      <figcaption className="cc__level">Nív. {level}</figcaption>
    </figure>
  );
}

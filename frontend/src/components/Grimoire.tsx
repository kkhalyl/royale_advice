import { useEffect, useMemo, useRef, useState } from "react";
import type { Card } from "../api/clash";
import { groupByRarity, RARITY_LABEL } from "../lib/cards";
import { ClashCard } from "./ClashCard";
import "./Grimoire.css";

interface Props {
  cards: Card[];
  commonMax: number;
  onClose: () => void;
}

export function Grimoire({ cards, commonMax, onClose }: Props) {
  const [query, setQuery] = useState("");
  const closeRef = useRef<HTMLButtonElement>(null);

  const groups = useMemo(() => {
    const q = query.trim().toLowerCase();
    return groupByRarity(q ? cards.filter((c) => c.name.toLowerCase().includes(q)) : cards);
  }, [cards, query]);

  useEffect(() => {
    closeRef.current?.focus();
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  return (
    <div className="grim" role="dialog" aria-modal="true" aria-labelledby="grim-title" onClick={onClose}>
      <div className="grim__book" onClick={(e) => e.stopPropagation()}>
        <header className="grim__head">
          <h2 id="grim-title" className="clash-text grim__title">
            Seu grimório: {cards.length} cartas
          </h2>
          <input
            className="grim__search"
            type="search"
            placeholder="Buscar carta"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            aria-label="Buscar carta pelo nome"
          />
          <button ref={closeRef} className="clash-btn clash-btn--blue grim__close" onClick={onClose}>
            Fechar
          </button>
        </header>

        <div className="grim__pages">
          {[...groups.entries()].map(([rarity, list]) =>
            list.length ? (
              <section key={rarity} className={`grim__group grim__group--${rarity}`}>
                <h3 className="grim__group-title">
                  {RARITY_LABEL[rarity]} <small>{list.length}</small>
                </h3>
                <div className="grim__grid">
                  {list.map((c) => (
                    <ClashCard key={c.id} card={c} commonMax={commonMax} size="sm" />
                  ))}
                </div>
              </section>
            ) : null
          )}
        </div>
      </div>
    </div>
  );
}

import { useEffect, useRef, useState, type CSSProperties, type FormEvent, type KeyboardEvent } from "react";
import type { Player } from "../api/clash";
import type { AdviceMode } from "../api/witch";
import type { DisplayMessage } from "../hooks/useWitchChat";
import { ClashCard } from "../components/ClashCard";
import { RichText } from "../components/RichText";
import { POTIONS } from "./Tavern";
import "./Cauldron.css";

const SUGGESTIONS = [
  "Qual carta devo upar primeiro?",
  "Como defendo contra decks aéreos?",
  "Esse deck funciona bem em torneio?",
];

// posições fixas das bolhas (x%, y%, tamanho px, duração s)
const BUBBLES = [
  [10, 30, 14, 2.4], [20, 55, 22, 3.1], [31, 28, 11, 2.0], [42, 60, 18, 2.8], [50, 35, 26, 3.4],
  [58, 58, 12, 2.2], [67, 30, 20, 2.9], [78, 52, 15, 2.5], [88, 36, 10, 2.1],
].map(([x, y, size, dur], i) => ({
  "--x": `${x}%`,
  "--y": `${y}%`,
  "--size": `${size}px`,
  "--dur": `${dur}s`,
  "--delay": `${i * -0.55}s`,
})) as CSSProperties[];

interface Props {
  player: Player;
  commonMax: number;
  mode: AdviceMode;
  messages: DisplayMessage[];
  streaming: string | null;
  error: string | null;
  busy: boolean;
  onAsk: (question: string) => void;
  onPotion: (mode: AdviceMode) => void;
  onStop: () => void;
  onBack: () => void;
}

export function Cauldron({
  player,
  commonMax,
  mode,
  messages,
  streaming,
  error,
  busy,
  onAsk,
  onPotion,
  onStop,
  onBack,
}: Props) {
  const [draft, setDraft] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = scrollRef.current;
    if (el) el.scrollTo({ top: el.scrollHeight, behavior: "smooth" });
  }, [messages.length, streaming]);

  const submit = (e?: FormEvent) => {
    e?.preventDefault();
    const q = draft.trim();
    if (!q || busy) return;
    onAsk(q);
    setDraft("");
  };

  const onKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  };

  return (
    <section className={`cauldron ${busy ? "cauldron--brewing" : ""}`} aria-label="Caldeirão da bruxa">
      <header className="cauldron__bar">
        <button className="clash-btn clash-btn--purple cauldron__back" onClick={onBack}>
          Voltar ao balcão
        </button>

        <nav className="cauldron__tabs" aria-label="Tipo de conselho">
          {POTIONS.map((p) => (
            <button
              key={p.mode}
              className={`cauldron__tab potion--${p.mode}`}
              aria-pressed={p.mode === mode}
              disabled={busy}
              onClick={() => onPotion(p.mode)}
            >
              <span className="cauldron__drop" aria-hidden="true" />
              {p.name}
            </button>
          ))}
        </nav>

        <div className="cauldron__deck" aria-label={`Deck de ${player.name}`}>
          {player.currentDeck.map((c) => (
            <ClashCard key={c.id} card={c} commonMax={commonMax} size="sm" />
          ))}
        </div>
      </header>

      <div className="cauldron__steam" ref={scrollRef} aria-live="polite">
        <ol className="chat">
          {messages.map((m, i) => (
            <li key={i} className={`chat__msg chat__msg--${m.role}`}>
              {m.role === "assistant" && <img className="chat__avatar" src="/witch.png" alt="" />}
              <div className="chat__bubble">
                {m.role === "assistant" ? <RichText text={m.content} /> : <p>{m.label ?? m.content}</p>}
              </div>
            </li>
          ))}

          {streaming !== null && (
            <li className="chat__msg chat__msg--assistant">
              <img className="chat__avatar" src="/witch.png" alt="" />
              <div className="chat__bubble">
                {streaming ? (
                  <RichText text={streaming} />
                ) : (
                  <p className="chat__thinking">A bruxa está mexendo o caldeirão…</p>
                )}
              </div>
            </li>
          )}

          {error && (
            <li className="chat__error" role="alert">
              A resposta não chegou: {error}. Tente perguntar de novo.
            </li>
          )}
        </ol>
      </div>

      <div className="pot">
        <div className="pot__brew" aria-hidden="true">
          {BUBBLES.map((b, i) => (
            <span key={i} className="pot__bubble" style={b} />
          ))}
        </div>

        <form className="ask" onSubmit={submit}>
          {!busy && messages.length > 0 && messages.length < 3 && (
            <div className="ask__suggestions">
              {SUGGESTIONS.map((s) => (
                <button key={s} type="button" className="ask__chip" onClick={() => onAsk(s)}>
                  {s}
                </button>
              ))}
            </div>
          )}
          <div className="ask__row">
            <label htmlFor="ask" className="sr-only">
              Pergunta para a bruxa
            </label>
            <textarea
              id="ask"
              className="ask__input"
              rows={1}
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              onKeyDown={onKeyDown}
              placeholder="Pergunte à bruxa"
            />
            {busy ? (
              <button type="button" className="clash-btn clash-btn--blue" onClick={onStop}>
                Parar
              </button>
            ) : (
              <button type="submit" className="clash-btn" disabled={!draft.trim()}>
                Perguntar
              </button>
            )}
          </div>
        </form>

        <div className="pot__body" aria-hidden="true" />
      </div>
    </section>
  );
}

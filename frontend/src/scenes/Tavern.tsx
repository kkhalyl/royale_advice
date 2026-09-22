import { useEffect, useMemo, useRef, useState, type FormEvent } from "react";
import { PlayerNotFoundError, type Player } from "../api/clash";
import type { AdviceMode } from "../api/witch";
import { avgElixir, formatNumber } from "../lib/cards";
import { ClashCard } from "../components/ClashCard";
import { WitchSpeech } from "../components/WitchSpeech";
import { Grimoire } from "../components/Grimoire";
import "./Tavern.css";

export const POTIONS: { mode: AdviceMode; name: string; hint: string }[] = [
  { mode: "analise", name: "Análise", hint: "O que seu deck faz bem e onde ele quebra" },
  { mode: "dicas", name: "Dicas", hint: "Como jogar cada partida com essas cartas" },
  { mode: "trocas", name: "Trocas sugeridas", hint: "Cartas que entram e saem, pelo seu nível" },
  { mode: "resumo", name: "Resumo", hint: "Sua conta inteira em poucas linhas" },
];

interface Props {
  player?: Player;
  loading: boolean;
  error: unknown;
  commonMax: number;
  onSearch: (tag: string) => void;
  onChoose: (mode: AdviceMode) => void;
  onReset: () => void;
}

export function Tavern({ player, loading, error, commonMax, onSearch, onChoose, onReset }: Props) {
  const [tag, setTag] = useState("");
  const [greeted, setGreeted] = useState(false);
  const [readingDone, setReadingDone] = useState(false);
  const [grimoireOpen, setGrimoireOpen] = useState(false);
  const potionsRef = useRef<HTMLDivElement>(null);

  // as poções podem aparecer abaixo da dobra; traz para a vista
  useEffect(() => {
    if (readingDone) potionsRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, [readingDone]);

  const line = useMemo(() => {
    if (loading) return "Hmm… a névoa está se abrindo. Deixa eu olhar na bola de cristal…";
    if (error instanceof PlayerNotFoundError)
      return "A bola de cristal não mostra ninguém com essa tag. Confira no seu perfil do jogo e tente de novo.";
    if (error) return "Os espíritos estão agitados e a leitura falhou. Tente de novo daqui a pouco.";
    if (player) {
      const deck = player.currentDeck;
      const heart =
        player.currentFavouriteCard?.name ??
        [...deck].sort((a, b) => (b.elixirCost ?? 0) - (a.elixirCost ?? 0))[0]?.name;
      return `Vejo… ${player.name}, nível ${player.expLevel}, com ${formatNumber(player.trophies)} troféus${
        player.arena ? ` em ${player.arena.name}` : ""
      }. Seu deck custa ${formatNumber(avgElixir(deck))} de elixir em média${
        heart ? ` e gira em torno de ${heart}` : ""
      }. O que você veio buscar no meu caldeirão?`;
    }
    return "Ah, um desafiante… Entre, entre. Me diga sua tag de jogador e eu conto o que as suas cartas escondem.";
  }, [loading, error, player]);

  const submit = (e: FormEvent) => {
    e.preventDefault();
    if (!tag.trim()) return;
    setReadingDone(false);
    onSearch(tag);
  };

  const showForm = !loading && !player && (greeted || Boolean(error));

  return (
    <section className="tavern" aria-label="Balcão da bruxa">
      <div className="tavern__wall" aria-hidden="true">
        <span className="tavern__beam" />
        <span className="tavern__shelf" />
      </div>

      <div className="tavern__witch">
        <div className={`tavern__portrait ${loading ? "tavern__portrait--casting" : ""}`}>
          <img src="/witch.png" alt="A bruxa da taverna, sorrindo atrás do balcão com seu cajado" />
        </div>
        {loading && <div className="crystal" aria-hidden="true" />}
        <div className="tavern__counter" aria-hidden="true" />
      </div>

      <div className="tavern__talk">
        <WitchSpeech
          key={line}
          text={line}
          onDone={() => (player ? setReadingDone(true) : setGreeted(true))}
        />

        {showForm && (
          <form className="tagform" onSubmit={submit}>
            <label htmlFor="tag" className="tagform__label">
              Sua tag de jogador
            </label>
            <div className="tagform__row">
              <span className="tagform__hash" aria-hidden="true">
                #
              </span>
              <input
                id="tag"
                className="tagform__input"
                value={tag}
                onChange={(e) => setTag(e.target.value.replace(/^#/, ""))}
                placeholder="2PP0JCQRV"
                autoComplete="off"
                autoCapitalize="characters"
                spellCheck={false}
                autoFocus
              />
              <button className="clash-btn" type="submit" disabled={!tag.trim()}>
                Revelar
              </button>
            </div>
          </form>
        )}

        {player && (
          <div className="reading">
            <header className="reading__banner">
              <div>
                <p className="clash-text reading__name">{player.name}</p>
                <p className="reading__meta">
                  {player.tag}
                  {player.clan ? `, clã ${player.clan.name}` : ""}
                </p>
              </div>
              <dl className="reading__stats">
                <div>
                  <dt>Troféus</dt>
                  <dd>{formatNumber(player.trophies)}</dd>
                </div>
                <div>
                  <dt>Nível</dt>
                  <dd>{player.expLevel}</dd>
                </div>
                <div>
                  <dt>Elixir médio</dt>
                  <dd>{formatNumber(avgElixir(player.currentDeck))}</dd>
                </div>
              </dl>
            </header>

            <div className="reading__deck" aria-label="Deck atual">
              {player.currentDeck.map((c, i) => (
                <ClashCard key={c.id} card={c} commonMax={commonMax} size="lg" revealDelay={400 + i * 160} />
              ))}
            </div>

            <div className="reading__links">
              <button className="reading__link" onClick={() => setGrimoireOpen(true)}>
                Ver todas as {player.cards.length} cartas da sua coleção
              </button>
              <button
                className="reading__link reading__link--quiet"
                onClick={() => {
                  setTag("");
                  setReadingDone(false);
                  onReset();
                }}
              >
                Trocar de jogador
              </button>
            </div>

            {readingDone && (
              <div ref={potionsRef} className="potions" role="group" aria-label="Escolha o tipo de conselho">
                {POTIONS.map((p, i) => (
                  <button
                    key={p.mode}
                    className={`potion potion--${p.mode}`}
                    style={{ animationDelay: `${i * 90}ms` }}
                    onClick={() => onChoose(p.mode)}
                  >
                    <span className="potion__flask" aria-hidden="true" />
                    <span className="potion__name">{p.name}</span>
                    <span className="potion__hint">{p.hint}</span>
                  </button>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {grimoireOpen && player && (
        <Grimoire cards={player.cards} commonMax={commonMax} onClose={() => setGrimoireOpen(false)} />
      )}
    </section>
  );
}

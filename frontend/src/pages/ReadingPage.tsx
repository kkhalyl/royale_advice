import { useState } from "react";
import { useParams, Link } from "react-router-dom";
import { useQuery, useMutation } from "@tanstack/react-query";
import { api, ApiError } from "../api/client";
import { CardFrame } from "../components/CardFrame";
import { ParchmentBubble } from "../components/ParchmentBubble";
import { ReadingPills } from "../components/ReadingPills";
import type { ReadingKey } from "../components/ReadingPills";
import { CauldronPanel } from "../components/CauldronPanel";
import type { CauldronContent } from "../components/CauldronPanel";
import { LoadingState } from "../components/LoadingState";
import { ErrorState } from "../components/ErrorState";
import styles from "./ReadingPage.module.css";

export function ReadingPage() {
  const { tag = "" } = useParams<{ tag: string }>();
  const [active, setActive] = useState<CauldronContent>({ source: "pill", key: "analise" });

  // retry: false - a 400 here means an invalid/unknown tag, a deterministic
  // error retries won't fix, and react-query's `isLoading` flag goes false
  // during the retry backoff delay even with no data yet, so retries would
  // also make the loading/error guards below unreliable.
  const playerQuery = useQuery({
    queryKey: ["player", tag],
    queryFn: () => api.getPlayer(tag),
    retry: false,
  });
  const deckQuery = useQuery({
    queryKey: ["deck", tag],
    queryFn: () => api.getPlayerDeck(tag),
    retry: false,
  });
  const adviceQuery = useQuery({
    queryKey: ["advice", tag],
    queryFn: () => api.getPlayerAdvice(tag),
    retry: false,
  });

  const askMutation = useMutation({
    mutationFn: (question: string) => api.askWitch(tag, question),
  });

  function handleAsk(question: string) {
    askMutation.mutate(question, {
      onSuccess: (data) => {
        setActive({ source: "question", question, answer: data.answer });
      },
    });
  }

  // isPending (not isLoading!) covers the whole no-data-yet window, including
  // any retry backoff delay - isLoading is isPending && isFetching, which
  // goes false between retry attempts even though there's still no data.
  const isPending = playerQuery.isPending || deckQuery.isPending || adviceQuery.isPending;
  const firstError = playerQuery.error || deckQuery.error || adviceQuery.error;

  if (firstError) {
    const message =
      firstError instanceof ApiError
        ? firstError.message
        : "Algo saiu errado na taverna. Tente novamente.";
    return (
      <div className={styles.root}>
        <div className={styles.centeredMessage}>
          <ErrorState message={message} />
          <Link className={styles.backLink} to="/">
            voltar a entrada da taverna
          </Link>
        </div>
      </div>
    );
  }

  if (isPending) {
    return (
      <div className={styles.root}>
        <div className={styles.centeredMessage}>
          <LoadingState text="a bruxa esta consultando as cartas..." />
        </div>
      </div>
    );
  }

  const player = playerQuery.data!;
  const deck = deckQuery.data!;
  const advice = adviceQuery.data!;

  const kingLevelText = player.king_level ? `Rei nível ${player.king_level}, ` : "";
  const revealText = `"Ahh... a nevoa se abre. Vejo ${deck.cards
    .slice(0, 3)
    .map((c) => c.name)
    .join(", ")}... um deck de ${advice.analysis.archetype}, nao e? ${kingLevelText}${player.trophies} troféus. Diga-me, viajante — o que deseja saber?"`;

  return (
    <div className={styles.root}>
      <div className={styles.title}>
        <div className={styles.titleMain}>Royal Advice</div>
      </div>

      <div className={styles.bubbleWrap}>
        <ParchmentBubble
          label="a bruxa fala"
          onAsk={handleAsk}
          asking={askMutation.isPending}
        >
          {revealText}
        </ParchmentBubble>
        {askMutation.isError && (
          <div style={{ marginTop: 12 }}>
            <ErrorState
              message={
                askMutation.error instanceof ApiError
                  ? askMutation.error.message
                  : "A bruxa não conseguiu ler as cartas agora."
              }
            />
          </div>
        )}
      </div>

      <div className={styles.deckSection}>
        <div className={styles.deckGrid}>
          {deck.cards.map((card, i) => (
            <CardFrame
              key={i}
              name={card.name}
              elixir={card.elixir}
              rarity={card.rarity}
              iconUrl={card.icon_url}
            />
          ))}
          {deck.card_count < 8 &&
            Array.from({ length: 8 - deck.card_count }).map((_, i) => (
              <CardFrame key={`incomplete-${i}`} name="incerto" incomplete />
            ))}
        </div>
      </div>

      <div className={styles.pillsWrap}>
        <ReadingPills
          active={active.source === "pill" ? active.key : "analise"}
          onSelect={(key: ReadingKey) => setActive({ source: "pill", key })}
        />
      </div>

      <div className={styles.cauldronWrap}>
        <CauldronPanel advice={advice} deck={deck} active={active} />
      </div>

      <Link className={styles.backLink} to="/">
        voltar a entrada da taverna
      </Link>
    </div>
  );
}

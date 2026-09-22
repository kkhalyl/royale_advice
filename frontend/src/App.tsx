import { useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchPlayer, normalizeTag, PlayerNotFoundError } from "./api/clash";
import { MODE_PROMPTS, type AdviceMode } from "./api/witch";
import { useWitchChat } from "./hooks/useWitchChat";
import { Entrance } from "./scenes/Entrance";
import { POTIONS, Tavern } from "./scenes/Tavern";
import { Cauldron } from "./scenes/Cauldron";
import "./App.css";

type Scene = "entrance" | "tavern" | "cauldron";

/** Camada da cena; fica `inert` (sem foco/clique) quando não está visível. */
function Layer({ name, active, children }: { name: string; active: boolean; children: ReactNode }) {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (ref.current) ref.current.inert = !active;
  }, [active]);
  return (
    <div ref={ref} className={`stage__layer stage__layer--${name}`} aria-hidden={!active}>
      {children}
    </div>
  );
}

export default function App() {
  const [scene, setScene] = useState<Scene>("entrance");
  const [tag, setTag] = useState<string | null>(null);
  const [mode, setMode] = useState<AdviceMode>("analise");

  const playerQuery = useQuery({
    queryKey: ["player", tag],
    queryFn: ({ signal }) => fetchPlayer(tag!, signal),
    enabled: Boolean(tag),
    retry: (count, err) => !(err instanceof PlayerNotFoundError) && count < 1,
  });
  const player = playerQuery.data;

  // maxLevel das comuns = teto real de nível; usado para normalizar os níveis da API
  const commonMax = useMemo(
    () => (player ? Math.max(...player.cards.map((c) => c.maxLevel), 1) : 1),
    [player]
  );

  const chat = useWitchChat(player);

  const brew = (next: AdviceMode) => {
    const potion = POTIONS.find((p) => p.mode === next)!;
    setMode(next);
    chat.ask(MODE_PROMPTS[next], next, `Quero a poção de ${potion.name.toLowerCase()}.`);
  };

  const enterCauldron = (next: AdviceMode) => {
    setScene("cauldron");
    brew(next);
  };

  const reset = () => {
    chat.reset();
    setTag(null);
  };

  return (
    <main className={`stage stage--${scene}`}>
      {scene === "entrance" ? (
        <Entrance onEnter={() => setScene("tavern")} />
      ) : (
        <Layer name="tavern" active={scene === "tavern"}>
          <Tavern
            player={player}
            loading={playerQuery.isFetching && !player}
            error={playerQuery.error}
            commonMax={commonMax}
            onSearch={(raw) => setTag(normalizeTag(raw))}
            onChoose={enterCauldron}
            onReset={reset}
          />
        </Layer>
      )}

      {player && (
        <Layer name="cauldron" active={scene === "cauldron"}>
          <Cauldron
            player={player}
            commonMax={commonMax}
            mode={mode}
            messages={chat.messages}
            streaming={chat.streaming}
            error={chat.error}
            busy={chat.busy}
            onAsk={(q) => chat.ask(q, mode)}
            onPotion={brew}
            onStop={chat.stop}
            onBack={() => setScene("tavern")}
          />
        </Layer>
      )}

      {scene === "cauldron" && <div className="stage__dive" aria-hidden="true" />}
    </main>
  );
}

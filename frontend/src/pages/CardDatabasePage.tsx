import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api, ApiError } from "../api/client";
import { CardFrame } from "../components/CardFrame";
import { LoadingState } from "../components/LoadingState";
import { ErrorState } from "../components/ErrorState";
import styles from "./CardDatabasePage.module.css";

export function CardDatabasePage() {
  const [rarity, setRarity] = useState("");
  const [type, setType] = useState("");
  const [maxElixir, setMaxElixir] = useState("");

  const cardsQuery = useQuery({
    queryKey: ["cards"],
    queryFn: () => api.getCards(),
  });

  const filtered = useMemo(() => {
    const cards = cardsQuery.data?.cards ?? [];
    return cards.filter((card) => {
      if (rarity && card.rarity.toLowerCase() !== rarity) return false;
      if (type && card.type.toLowerCase() !== type) return false;
      if (maxElixir && card.elixir > Number(maxElixir)) return false;
      return true;
    });
  }, [cardsQuery.data, rarity, type, maxElixir]);

  return (
    <div className={styles.root}>
      <div className={styles.header}>
        <div className={styles.title}>Grimório de Cartas</div>
        <Link className={styles.backLink} to="/">
          voltar a taverna
        </Link>
      </div>

      <div className={styles.filters}>
        <select value={rarity} onChange={(e) => setRarity(e.target.value)}>
          <option value="">Todas as raridades</option>
          <option value="common">Comum</option>
          <option value="rare">Rara</option>
          <option value="epic">Épica</option>
          <option value="legendary">Lendária</option>
        </select>
        <select value={type} onChange={(e) => setType(e.target.value)}>
          <option value="">Todos os tipos</option>
          <option value="troop">Tropa</option>
          <option value="spell">Feitiço</option>
          <option value="building">Construção</option>
        </select>
        <input
          type="number"
          min={1}
          max={10}
          placeholder="Elixir máximo"
          value={maxElixir}
          onChange={(e) => setMaxElixir(e.target.value)}
        />
      </div>

      {cardsQuery.isLoading && <LoadingState text="carregando o grimório..." />}

      {cardsQuery.error && (
        <ErrorState
          message={
            cardsQuery.error instanceof ApiError
              ? cardsQuery.error.message
              : "Não foi possível carregar as cartas."
          }
        />
      )}

      {cardsQuery.data && (
        <>
          {filtered.length === 0 ? (
            <div className={styles.empty}>Nenhuma carta encontrada com esses filtros.</div>
          ) : (
            <div className={styles.grid}>
              {filtered.map((card) => (
                <CardFrame
                  key={card.id}
                  name={card.name}
                  elixir={card.elixir}
                  rarity={card.rarity}
                  iconUrl={card.icon_url}
                />
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}

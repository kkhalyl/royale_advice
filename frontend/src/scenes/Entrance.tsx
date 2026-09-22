import { useState } from "react";
import "./Entrance.css";

interface Props {
  onEnter: () => void;
}

export function Entrance({ onEnter }: Props) {
  const [opening, setOpening] = useState(false);

  const open = () => {
    if (opening) return;
    setOpening(true);
    window.setTimeout(onEnter, 1100);
  };

  return (
    <section className={`entrance ${opening ? "entrance--open" : ""}`} aria-label="Entrada da taverna">
      <div className="entrance__sky" />

      <div className="entrance__facade">
        <div className="entrance__sign">
          <span className="entrance__sign-chain" />
          <span className="entrance__sign-chain" />
          <p>Taverna da Bruxa</p>
        </div>

        <div className="entrance__doorway">
          <div className="entrance__light" />
          <div className="entrance__door entrance__door--left" />
          <div className="entrance__door entrance__door--right" />
        </div>

        <span className="entrance__lantern entrance__lantern--left" />
        <span className="entrance__lantern entrance__lantern--right" />
      </div>

      <div className="entrance__copy">
        <h1 className="clash-text entrance__title">Royal Advice</h1>
        <p className="entrance__lead">Uma bruxa lê o seu deck melhor que você.</p>
        <button className="clash-btn entrance__cta" onClick={open} disabled={opening}>
          Entrar na taverna
        </button>
      </div>

      <p className="entrance__legal">
        Conteúdo de fã não oficial, não endossado pela Supercell. Imagens das cartas via API oficial do Clash
        Royale.
      </p>
    </section>
  );
}

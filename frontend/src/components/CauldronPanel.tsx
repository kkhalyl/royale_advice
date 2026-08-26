import type { Advice, PlayerDeckView } from "../api/client";
import type { ReadingKey } from "./ReadingPills";
import { IssueBadge } from "./IssueBadge";
import { ErrorState } from "./ErrorState";
import styles from "./CauldronPanel.module.css";

/**
 * The single active answer shown in the cauldron. Selecting a new pill, or
 * asking a new question, REPLACES this value wholesale - see
 * specs/frontend-app/design.md's "Interaction model": nothing is ever
 * appended to a list or kept alongside a previous answer.
 */
export type CauldronContent =
  | { source: "pill"; key: ReadingKey }
  | { source: "question"; question: string; answer: string };

export interface CauldronPanelProps {
  advice: Advice;
  deck: PlayerDeckView;
  active: CauldronContent;
}

function DeckStrip({ deck, advice }: { deck: PlayerDeckView; advice: Advice }) {
  return (
    <div className={styles.deckStrip}>
      {deck.cards.map((card, i) => (
        <div key={i} className={styles.miniCard} style={{ background: "linear-gradient(160deg,#a9b4c2,#5f6b7a)" }}>
          {card.icon_url ? (
            <img src={card.icon_url} alt={card.name} />
          ) : (
            <span style={{ fontSize: 10, color: "#fff", fontWeight: 700 }}>{card.elixir}</span>
          )}
        </div>
      ))}
      <div className={styles.badges}>
        <span className={`${styles.badge} ${styles.badgeArchetype}`}>{advice.analysis.archetype}</span>
        <span className={`${styles.badge} ${styles.badgeElixir}`}>Elixir {advice.analysis.avg_elixir}</span>
      </div>
    </div>
  );
}

function AnaliseContent({ advice }: { advice: Advice }) {
  return (
    <>
      <div className={styles.sectionTitle}>O que o caldeirão revela sobre seu deck:</div>
      {advice.analysis.flagged_issues.map((issue, i) => (
        <IssueBadge key={`issue-${i}`} message={issue.message} kind="issue" />
      ))}
      {advice.analysis.strengths.map((strength, i) => (
        <IssueBadge key={`strength-${i}`} message={strength.message} kind="strength" />
      ))}
      {advice.analysis.flagged_issues.length === 0 && advice.analysis.strengths.length === 0 && (
        <div className={styles.summaryText}>Nada de especial a reportar - deck equilibrado.</div>
      )}
    </>
  );
}

function TipListContent({
  title,
  tips,
}: {
  title: string;
  tips: { text: string; source: string }[];
}) {
  return (
    <>
      <div className={styles.sectionTitle}>{title}</div>
      <div className={styles.tipList}>
        {tips.map((tip, i) => (
          <div key={i} className={`${styles.tipItem} ${tip.source === "reddit" ? styles.tipItemReddit : ""}`}>
            <div>
              {tip.source === "reddit" && <span className={styles.tipSourceLabel}>sussurro da comunidade</span>}
              <div className={styles.tipText}>{tip.text}</div>
            </div>
          </div>
        ))}
        {tips.length === 0 && <div className={styles.summaryText}>Nada por aqui ainda.</div>}
      </div>
    </>
  );
}

function ResumoContent({ advice }: { advice: Advice }) {
  return (
    <>
      <div className={styles.sectionTitle}>Resumo do coach:</div>
      {advice.llm_summary ? (
        <div className={styles.summaryText}>{advice.llm_summary}</div>
      ) : (
        <ErrorState message="A bruxa está em silêncio hoje - resumo indisponível no momento." />
      )}
    </>
  );
}

function QuestionAnswerContent({ question, answer }: { question: string; answer: string }) {
  return (
    <>
      <div className={styles.questionLabel}>você perguntou: "{question}"</div>
      <div className={styles.sectionTitle}>A bruxa responde:</div>
      <div className={styles.summaryText}>{answer}</div>
    </>
  );
}

export function CauldronPanel({ advice, deck, active }: CauldronPanelProps) {
  return (
    <div className={styles.wrap}>
      <div className={styles.heading}>o caldeirão borbulha e revela...</div>
      <div className={styles.panel}>
        <DeckStrip deck={deck} advice={advice} />

        {active.source === "question" ? (
          <QuestionAnswerContent question={active.question} answer={active.answer} />
        ) : active.key === "analise" ? (
          <AnaliseContent advice={advice} />
        ) : active.key === "dicas" ? (
          <TipListContent title="Dicas gerais:" tips={advice.general_tips} />
        ) : active.key === "trocas" ? (
          <TipListContent title="Trocas sugeridas:" tips={advice.suggested_swaps} />
        ) : (
          <ResumoContent advice={advice} />
        )}

        <div className={styles.footerNote}>
          clicar em outra categoria acima troca o conteúdo aqui embaixo - nada fica empilhado, sempre uma resposta
          por vez
        </div>
      </div>
    </div>
  );
}

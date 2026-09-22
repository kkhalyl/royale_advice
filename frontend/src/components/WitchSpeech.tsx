import { useEffect } from "react";
import { useTypewriter } from "../hooks/useTypewriter";
import "./WitchSpeech.css";

interface Props {
  text: string;
  onDone?: () => void;
}

export function WitchSpeech({ text, onDone }: Props) {
  const { shown, done, skip } = useTypewriter(text);

  useEffect(() => {
    if (done) onDone?.();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [done]);

  return (
    <div className="speech" onClick={skip} role="status" aria-live="polite">
      <p className="speech__text" aria-hidden="true">
        {shown}
        {!done && <span className="speech__caret" />}
      </p>
      <p className="sr-only">{text}</p>
    </div>
  );
}

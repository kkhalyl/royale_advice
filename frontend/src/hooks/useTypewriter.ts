import { useEffect, useState } from "react";

const reduced =
  typeof window !== "undefined" && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

/** Revela `text` letra a letra. Retorna o texto parcial e se terminou. */
export function useTypewriter(text: string, speed = 28) {
  const [count, setCount] = useState(reduced ? text.length : 0);

  useEffect(() => {
    if (reduced) {
      setCount(text.length);
      return;
    }
    setCount(0);
    const id = window.setInterval(() => {
      setCount((n) => {
        if (n >= text.length) {
          window.clearInterval(id);
          return n;
        }
        return n + 1;
      });
    }, speed);
    return () => window.clearInterval(id);
  }, [text, speed]);

  return { shown: text.slice(0, count), done: count >= text.length, skip: () => setCount(text.length) };
}

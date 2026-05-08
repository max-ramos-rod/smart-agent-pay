import { useEffect, useRef, useState } from "react";

/**
 * Fake SOL price oscillator. Starts around $150, drifts each tick.
 * Exposes an imperative `crash` to force a drop for the demo.
 */
export function usePriceSimulator(initial = 150, intervalMs = 1500) {
  const [price, setPrice] = useState(initial);
  const [history, setHistory] = useState<number[]>([initial]);
  const priceRef = useRef(initial);

  useEffect(() => {
    const id = setInterval(() => {
      // small random walk -1.5% .. +1.5%
      const drift = (Math.random() - 0.5) * 0.03;
      const next = Math.max(1, priceRef.current * (1 + drift));
      priceRef.current = next;
      setPrice(next);
      setHistory((h) => [...h.slice(-59), next]);
    }, intervalMs);
    return () => clearInterval(id);
  }, [intervalMs]);

  const crash = (percent = 6) => {
    const next = priceRef.current * (1 - percent / 100);
    priceRef.current = next;
    setPrice(next);
    setHistory((h) => [...h.slice(-59), next]);
  };

  const pump = (percent = 4) => {
    const next = priceRef.current * (1 + percent / 100);
    priceRef.current = next;
    setPrice(next);
    setHistory((h) => [...h.slice(-59), next]);
  };

  return { price, history, crash, pump };
}

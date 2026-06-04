// hooks/usePrice.ts
import { useEffect, useRef, useState } from "react";
import { api } from "@/services/api";

export function usePrice(intervalMs = 5000) {
  const [price, setPrice] = useState<number>(0);
  const [history, setHistory] = useState<number[]>([]);

  // mantém crash/pump locais para o botão de demo ainda funcionar visualmente
  const overrideRef = useRef<number | null>(null);

  const fetchPrice = async () => {
    try {
      const { data } = await api.get("/demo/price");
      const p: number = overrideRef.current ?? data.price;
      setPrice(p);
      setHistory((h) => [...h.slice(-59), p]);
    } catch {
      return;
    }
  };

  useEffect(() => {
    fetchPrice();
    const id = setInterval(fetchPrice, intervalMs);
    return () => clearInterval(id);
  }, [intervalMs]);

  // crash/pump só afetam a visualização local por alguns segundos
  const crash = (percent = 6) => {
    const next = price * (1 - percent / 100);
    overrideRef.current = next;
    setPrice(next);
    setHistory((h) => [...h.slice(-59), next]);
    setTimeout(() => { overrideRef.current = null; }, 12_000);
  };

  const pump = (percent = 4) => {
    const next = price * (1 + percent / 100);
    overrideRef.current = next;
    setPrice(next);
    setHistory((h) => [...h.slice(-59), next]);
    setTimeout(() => { overrideRef.current = null; }, 8_000);
  };

  return { price, history, crash, pump };
}

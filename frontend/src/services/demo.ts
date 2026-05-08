// services/demo.ts — conecta o botão crash() ao backend
import { api } from "./api";

export const setDemoPrice = (price: number) =>
  api.post("/demo/set-price", { price });

export const clearDemoPrice = () =>
  api.delete("/demo/set-price");

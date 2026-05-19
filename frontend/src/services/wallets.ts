import { api } from "./api";

export const getBalance = async () => {
  const { data } = await api.get("/wallets/balance");
  return data;
};

export const getBalances = async (): Promise<{ sol: number; usdc: number }> => {
  const { data } = await api.get("/wallets/balances");
  return data;
};
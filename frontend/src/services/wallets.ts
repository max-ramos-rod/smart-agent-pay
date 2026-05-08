import { api } from "./api";

export const getBalance = async () => {
  const { data } = await api.get("/wallets/balance");
  console.log("🔍 Balance fetched:", data.balance);
  return data;
};
import { api } from "./api";

export const createSession = (max_amount: number) =>
  api.post("/agents/session", { max_amount });

export const getSession = async () => {
  const { data } = await api.get("/agents/session");
  return data;
};
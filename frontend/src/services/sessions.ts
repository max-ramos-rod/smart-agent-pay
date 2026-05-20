import { api } from "./api";

export async function createSession(data: {
  delegate_pubkey: string;
  ephemeral_private_key: string;
  spending_limit: number;
  expiry_days: number;
  session_token_address: string;
}) {
  const res = await api.post("/sessions", data);
  return res.data;
}

export async function revokeSession() {
  const res = await api.delete("/sessions");
  return res.data;
}

export async function getSession() {
  const res = await api.get("/sessions");
  return res.data;
}

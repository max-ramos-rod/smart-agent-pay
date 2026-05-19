// services/auth.ts

import { api } from "./api";
import { Buffer } from 'buffer';

export const loginWithWallet = async (provider: any, publicKey: string) => {
  const challenge = await api.get("/auth/challenge", {
    params: { public_key: publicKey },
  });

  const message = challenge.data.message;

  const encodedMessage = new TextEncoder().encode(message);
  const signed = await provider.signMessage(encodedMessage, "utf8");

  const signature = Buffer.from(signed.signature).toString("base64");

  const res = await api.post("/auth/login", {
    public_key: publicKey,
    signature,
    message,
  });

  localStorage.setItem("wallet_address", publicKey);
  localStorage.setItem("token", res.data.access_token);
  localStorage.setItem("refresh_token", res.data.refresh_token);
  localStorage.setItem("wallet_id", String(res.data.wallet_id));

  return res.data;
};
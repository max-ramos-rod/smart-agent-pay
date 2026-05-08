import { useCallback, useEffect, useState } from "react";
import {
  Connection,
  PublicKey,
  SystemProgram,
  Transaction,
  LAMPORTS_PER_SOL,
  clusterApiUrl,
} from "@solana/web3.js";

type PhantomProvider = {
  isPhantom?: boolean;
  publicKey: { toString(): string } | null;
  isConnected: boolean;
  connect: (opts?: { onlyIfTrusted?: boolean }) => Promise<{ publicKey: { toString(): string } }>;
  disconnect: () => Promise<void>;
  signAndSendTransaction: (tx: Transaction) => Promise<{ signature: string }>;
  on: (event: string, cb: (...args: unknown[]) => void) => void;
};

declare global {
  interface Window {
    solana?: PhantomProvider;
  }
}

const connection = new Connection(clusterApiUrl("devnet"), "confirmed");

export function usePhantom() {
  const [address, setAddress] = useState<string | null>(null);
  const [connecting, setConnecting] = useState(false);
  const [installed, setInstalled] = useState(false);

  useEffect(() => {
    const provider = window.solana;
    setInstalled(Boolean(provider?.isPhantom));
    if (provider?.isPhantom) {
      provider.connect({ onlyIfTrusted: true })
        .then(({ publicKey }) => setAddress(publicKey.toString()))
        .catch(() => {});
      provider.on("disconnect", () => setAddress(null));
      provider.on("accountChanged", (pk) => {
        const key = pk as { toString(): string } | null;
        setAddress(key ? key.toString() : null);
      });
    }
  }, []);

  const connect = useCallback(async () => {
    const provider = window.solana;
    if (!provider?.isPhantom) {
      window.open("https://phantom.app/", "_blank");
      return;
    }
    setConnecting(true);
    try {
      const { publicKey } = await provider.connect();
      setAddress(publicKey.toString());
    } finally {
      setConnecting(false);
    }
  }, []);

  const disconnect = useCallback(async () => {
    await window.solana?.disconnect();
    setAddress(null);
  }, []);

  const sendSol = useCallback(
    async (toAddress: string, amountSol: number): Promise<string> => {
      const provider = window.solana;
      if (!provider?.publicKey) throw new Error("Wallet not connected");

      const fromPubkey = new PublicKey(provider.publicKey.toString());
      const toPubkey = new PublicKey(toAddress);

      const tx = new Transaction().add(
        SystemProgram.transfer({
          fromPubkey,
          toPubkey,
          lamports: Math.round(amountSol * LAMPORTS_PER_SOL),
        })
      );
      tx.feePayer = fromPubkey;
      const { blockhash } = await connection.getLatestBlockhash();
      tx.recentBlockhash = blockhash;

      const { signature } = await provider.signAndSendTransaction(tx);
      return signature;
    },
    []
  );

  return { address, connect, disconnect, connecting, installed, sendSol };
}

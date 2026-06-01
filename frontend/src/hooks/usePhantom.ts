import { useCallback, useEffect, useState } from "react";
import {
  Connection,
  PublicKey,
  SystemProgram,
  Transaction,
  VersionedTransaction,
  LAMPORTS_PER_SOL,
} from "@solana/web3.js";
import {
  getAssociatedTokenAddress,
  createTransferCheckedInstruction,
  createAssociatedTokenAccountInstruction,
  TOKEN_PROGRAM_ID,
  ASSOCIATED_TOKEN_PROGRAM_ID,
} from "@solana/spl-token";

type PhantomProvider = {
  isPhantom?: boolean;
  publicKey: { toString(): string } | null;
  isConnected: boolean;
  connect: (opts?: { onlyIfTrusted?: boolean }) => Promise<{ publicKey: { toString(): string } }>;
  disconnect: () => Promise<void>;
  signAndSendTransaction: (tx: Transaction | VersionedTransaction) => Promise<{ signature: string }>;
  on: (event: string, cb: (...args: unknown[]) => void) => void;
};

declare global {
  interface Window {
    solana?: PhantomProvider;
  }
}

const RPC_URL = import.meta.env.VITE_SOLANA_RPC_URL || "https://api.mainnet-beta.solana.com";
const USDC_MINT_ADDRESS = import.meta.env.VITE_USDC_MINT || "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v";
const connection = new Connection(RPC_URL, "confirmed");

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

  const sendUsdc = useCallback(
    async (toAddress: string, amountUsdc: number): Promise<string> => {
      const provider = window.solana;
      if (!provider?.publicKey) throw new Error("Wallet not connected");

      const USDC_MINT = new PublicKey(USDC_MINT_ADDRESS);
      const fromPubkey = new PublicKey(provider.publicKey.toString());
      const toPubkey = new PublicKey(toAddress);

      const fromAta = await getAssociatedTokenAddress(USDC_MINT, fromPubkey);
      const toAta = await getAssociatedTokenAddress(USDC_MINT, toPubkey);

      const tx = new Transaction();

      // cria ATA do destinatário se não existir
      const toAtaInfo = await connection.getAccountInfo(toAta);
      if (!toAtaInfo) {
        tx.add(
          createAssociatedTokenAccountInstruction(
            fromPubkey,
            toAta,
            toPubkey,
            USDC_MINT,
            TOKEN_PROGRAM_ID,
            ASSOCIATED_TOKEN_PROGRAM_ID,
          )
        );
      }

      tx.add(
        createTransferCheckedInstruction(
          fromAta,
          USDC_MINT,
          toAta,
          fromPubkey,
          BigInt(Math.round(amountUsdc * 1_000_000)), // 6 decimais
          6,
        )
      );

      tx.feePayer = fromPubkey;
      const { blockhash } = await connection.getLatestBlockhash();
      tx.recentBlockhash = blockhash;

      const { signature } = await provider.signAndSendTransaction(tx);
      return signature;
    },
    []
  );

  const signAndSendSwap = useCallback(
    async (serializedTxBase64: string): Promise<string> => {
      const provider = window.solana;
      if (!provider?.publicKey) throw new Error("Wallet not connected");

      const txBytes = Uint8Array.from(atob(serializedTxBase64), (c) => c.charCodeAt(0));
      const tx = VersionedTransaction.deserialize(txBytes);

      const { signature } = await provider.signAndSendTransaction(tx);
      return signature;
    },
    []
  );

  return { address, connect, disconnect, connecting, installed, sendSol, sendUsdc, signAndSendSwap };
}

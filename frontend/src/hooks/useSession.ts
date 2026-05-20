import { useCallback, useState } from "react";
import { Connection, Keypair, PublicKey, clusterApiUrl } from "@solana/web3.js";
import { AnchorProvider, Program, BN } from "@anchor-lang/core";
import idl from "@/idl/sentinelfi.json";
import { api } from "@/services/api";

const PROGRAM_ID = new PublicKey("HwPkZA1WSussRBD8hgRojJ2bg2Upxa1wr428gBzzoATB");
const SESSION_SEED = Buffer.from("session");
const CONNECTION = new Connection(clusterApiUrl("devnet"), "confirmed");

type SessionStatus = {
  active: boolean;
  delegate: string | null;
  spendingLimit: number | null;
  amountSpent: number | null;
  expiry: Date | null;
};

export function useSession() {
  const [creating, setCreating] = useState(false);
  const [revoking, setRevoking] = useState(false);
  const [status, setStatus] = useState<SessionStatus>({
    active: false,
    delegate: null,
    spendingLimit: null,
    amountSpent: null,
    expiry: null,
  });

  const createSession = useCallback(
    async (spendingLimitUsdc: number, expiryDays: number) => {
      const provider = (window as any).solana;
      if (!provider?.publicKey) throw new Error("Phantom não conectado");

      setCreating(true);
      try {
        const ownerPubkey = new PublicKey(provider.publicKey.toString());

        // 1. Gerar ephemeral keypair no browser
        const ephemeralKeypair = Keypair.generate();

        // 2. Derivar PDA da session
        const [sessionPda] = PublicKey.findProgramAddressSync(
          [SESSION_SEED, ownerPubkey.toBuffer()],
          PROGRAM_ID
        );

        // 3. Montar provider e programa Anchor
        const anchorProvider = new AnchorProvider(
          CONNECTION,
          {
            publicKey: ownerPubkey,
            signTransaction: async (tx: any) => provider.signTransaction(tx),
            signAllTransactions: async (txs: any[]) => provider.signAllTransactions(txs),
          },
          { commitment: "confirmed" }
        );

        const program = new Program(idl as any, anchorProvider);

        const spendingLimitRaw = new BN(spendingLimitUsdc * 1_000_000); // micro-USDC
        const expiryTimestamp = new BN(
          Math.floor(Date.now() / 1000) + expiryDays * 86400
        );

        // 4. Usuário assina create_session via Phantom
        await (program.methods as any)
          .createSession(spendingLimitRaw, expiryTimestamp)
          .accounts({
            owner: ownerPubkey,
            delegate: ephemeralKeypair.publicKey,
            sessionToken: sessionPda,
          })
          .rpc();

        // 5. Enviar ephemeral private key ao backend (criptografada em trânsito via HTTPS)
        await api.post("/sessions", {
          delegate_pubkey: ephemeralKeypair.publicKey.toBase58(),
          ephemeral_private_key: Buffer.from(ephemeralKeypair.secretKey).toString("base64"),
          spending_limit: spendingLimitUsdc,
          expiry_days: expiryDays,
          session_token_address: sessionPda.toBase58(),
        });

        setStatus({
          active: true,
          delegate: ephemeralKeypair.publicKey.toBase58(),
          spendingLimit: spendingLimitUsdc,
          amountSpent: 0,
          expiry: new Date(Date.now() + expiryDays * 86400 * 1000),
        });
      } finally {
        setCreating(false);
      }
    },
    []
  );

  const revokeSession = useCallback(async () => {
    const provider = (window as any).solana;
    if (!provider?.publicKey) throw new Error("Phantom não conectado");

    setRevoking(true);
    try {
      const ownerPubkey = new PublicKey(provider.publicKey.toString());

      const [sessionPda] = PublicKey.findProgramAddressSync(
        [SESSION_SEED, ownerPubkey.toBuffer()],
        PROGRAM_ID
      );

      const anchorProvider = new AnchorProvider(
        CONNECTION,
        {
          publicKey: ownerPubkey,
          signTransaction: async (tx: any) => provider.signTransaction(tx),
          signAllTransactions: async (txs: any[]) => provider.signAllTransactions(txs),
        },
        { commitment: "confirmed" }
      );

      const program = new Program(idl as any, anchorProvider);

      // Usuário assina revoke_session — fecha a conta e recupera lamports
      await (program.methods as any)
        .revokeSession()
        .accounts({
          owner: ownerPubkey,
          sessionToken: sessionPda,
        })
        .rpc();

      // Avisar backend para invalidar a sessão
      await api.delete("/sessions");

      setStatus({
        active: false,
        delegate: null,
        spendingLimit: null,
        amountSpent: null,
        expiry: null,
      });
    } finally {
      setRevoking(false);
    }
  }, []);

  return { createSession, revokeSession, creating, revoking, status };
}

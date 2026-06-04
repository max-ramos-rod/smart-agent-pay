import { useCallback, useState } from "react";
import { Connection, Keypair, PublicKey, clusterApiUrl, Transaction, VersionedTransaction } from "@solana/web3.js";
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

type PhantomAnchorProvider = {
  publicKey: { toString(): string };
  signTransaction: <T extends Transaction | VersionedTransaction>(tx: T) => Promise<T>;
  signAllTransactions: <T extends Transaction | VersionedTransaction>(txs: T[]) => Promise<T[]>;
};

type AnchorRpcCall = {
  rpc: () => Promise<unknown>;
};

type AnchorMethod = {
  accounts: (accounts: Record<string, unknown>) => AnchorRpcCall;
};

type SessionProgramMethods = {
  createSession: (spendingLimit: BN, expiry: BN) => AnchorMethod;
  revokeSession: () => AnchorMethod;
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
      const provider = window.solana as PhantomAnchorProvider | undefined;
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
            signTransaction: async <T extends Transaction | VersionedTransaction>(tx: T) => provider.signTransaction(tx),
            signAllTransactions: async <T extends Transaction | VersionedTransaction>(txs: T[]) => provider.signAllTransactions(txs),
          },
          { commitment: "confirmed" }
        );

        const program = new Program(idl as unknown as ConstructorParameters<typeof Program>[0], anchorProvider);
        const methods = program.methods as unknown as SessionProgramMethods;

        // 4. Se o PDA já existe on-chain, revogar antes (init falha com conta existente)
        const existingAccount = await CONNECTION.getAccountInfo(sessionPda);
        if (existingAccount) {
          await methods
            .revokeSession()
            .accounts({ owner: ownerPubkey, sessionToken: sessionPda })
            .rpc();
        }

        const spendingLimitRaw = new BN(spendingLimitUsdc * 1_000_000); // micro-USDC
        const expiryTimestamp = new BN(
          Math.floor(Date.now() / 1000) + expiryDays * 86400
        );

        // 5. Usuário assina create_session via Phantom
        await methods
          .createSession(spendingLimitRaw, expiryTimestamp)
          .accounts({
            owner: ownerPubkey,
            delegate: ephemeralKeypair.publicKey,
            sessionToken: sessionPda,
          })
          .rpc();

        // 6. Enviar ephemeral private key ao backend (criptografada em trânsito via HTTPS)
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
    const provider = window.solana as PhantomAnchorProvider | undefined;
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
          signTransaction: async <T extends Transaction | VersionedTransaction>(tx: T) => provider.signTransaction(tx),
          signAllTransactions: async <T extends Transaction | VersionedTransaction>(txs: T[]) => provider.signAllTransactions(txs),
        },
        { commitment: "confirmed" }
      );

      const program = new Program(idl as unknown as ConstructorParameters<typeof Program>[0], anchorProvider);
      const methods = program.methods as unknown as SessionProgramMethods;

      // Usuário assina revoke_session — fecha a conta e recupera lamports
      await methods
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

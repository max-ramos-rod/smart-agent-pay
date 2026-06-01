import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import logo from "@/assets/logo.png";
import { z } from "zod";
import { toast } from "sonner";
import {
  Activity, Bot, ExternalLink, Power, Wallet,
  Zap, TrendingDown, TrendingUp, Trash2,
  CheckCircle2, XCircle, Clock, FlaskConical, Timer,
  Shield, ShieldCheck, ShieldOff, KeyRound,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { usePhantom } from "@/hooks/usePhantom";
import { usePrice } from "@/hooks/usePrice";
import { useSession } from "@/hooks/useSession";
import { Sparkline } from "@/components/Sparkline";
import { api } from "@/services/api";
import { getStrategies, createStrategy } from "@/services/strategy";
import { getExecutions } from "@/services/logs";
import { getBalances } from "@/services/wallets";
import { getSession } from "@/services/sessions";
import { useAuth } from "@/hooks/useAuth";

type Strategy = {
  id: string;
  drop_percent: number;
  amount_sol: number;
  destination_address: string;
  reference_price: number;
  active: boolean;
  created_at: string;
};

type Execution = {
  id: string;
  strategy_id: string | null;
  trigger_price: number;
  reference_price: number;
  drop_percent: number;
  amount_sol: number;
  token: string;
  amount_usdc: number | null;
  tx_hash: string | null;
  status: string;
  explanation: string | null;
  serialized_tx: string | null;
  created_at: string;
};

const strategySchema = z.object({
  drop_percent: z.coerce.number().min(0.1, "Min 0.1%").max(99, "Max 99%"),
  amount_sol: z.coerce.number().min(0.0001, "Min 0.0001 SOL").max(10, "Max 10 SOL"),
  destination_address: z.string().trim().min(32, "Endereço inválido").max(64, "Endereço inválido"),
});

type SessionInfo = {
  delegate_pubkey: string;
  spending_limit: number;
  expiry: string;
  session_token_address: string;
} | null;

const Index = () => {
  const { address, connect, disconnect, connecting, sendSol, sendUsdc, signAndSendSwap } = usePhantom();
  const { loginWithWallet } = useAuth();
  const { price, history, crash } = usePrice();
  const { createSession, revokeSession, creating, revoking } = useSession();

  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [executions, setExecutions] = useState<Execution[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [balances, setBalances] = useState<{ sol: number; usdc: number } | null>(null);
  const [balanceOpen, setBalanceOpen] = useState(false);
  const [isReady, setIsReady] = useState(false);
  const [demoLoading, setDemoLoading] = useState(false);
  const [demoActive, setDemoActive] = useState(false);

  const [dropPct, setDropPct] = useState("5");
  const [amount, setAmount] = useState("0.001");
  const [destination, setDestination] = useState("");
  const [token, setToken] = useState<"SOL" | "USDC">("SOL");
  const [strategyMode, setStrategyMode] = useState<"transfer" | "swap">("transfer");
  const [tokenIn, setTokenIn] = useState<"SOL" | "USDC">("SOL");
  const [tokenOut, setTokenOut] = useState<"SOL" | "USDC">("USDC");
  const [slippageBps, setSlippageBps] = useState("50");
  const [signingExecution, setSigningExecution] = useState<Execution | null>(null);
  const [signing, setSigning] = useState(false);
  const dismissedIds = useRef<Set<string>>(new Set());

  const [sessionInfo, setSessionInfo] = useState<SessionInfo>(null);
  const [spendingLimit, setSpendingLimit] = useState("50");
  const [expiryDays, setExpiryDays] = useState("7");

  // --- CORRIGIDO: uma única função de refresh, useCallback para estabilidade ---
  const refresh = useCallback(async () => {
    const [stratResult, execResult, balResult] = await Promise.allSettled([
      getStrategies(),
      getExecutions(),
      getBalances(),
    ]);

    if (stratResult.status === "fulfilled") {
      setStrategies(stratResult.value);
    }

    if (execResult.status === "fulfilled") {
      const exec = execResult.value;
      setExecutions(exec);

      const pending = exec.filter(
        (e: Execution) => e.status === "awaiting_signature" && !dismissedIds.current.has(e.id)
      );
      if (pending.length > 0 && !signingExecution) setSigningExecution(pending[0]);

      if (signingExecution) {
        const stillPending = exec.find(
          (e: Execution) => e.id === signingExecution.id && e.status === "awaiting_signature"
        );
        if (!stillPending) {
          setSigningExecution(null);
          toast.info("⏰ Solicitação expirada — condições podem ter mudado");
        }
      }
    }

    if (balResult.status === "fulfilled") {
      setBalances(balResult.value);
    }
  }, [signingExecution]);

  // --- init: auto-login e primeiro load ---
  useEffect(() => {
    const provider = (window as any).solana;
    if (!address || !provider) return;

    const init = async () => {
      try {
        localStorage.setItem("wallet_address", address);
        let token = localStorage.getItem("token");
        if (!token) {
          const res = await loginWithWallet(provider, address);
          token = res.access_token;
          localStorage.setItem("token", token);
          localStorage.setItem("wallet_id", String(res.wallet_id));
        }
        await refresh();
        try {
          const sessionRes = await getSession();
          if (sessionRes?.data) setSessionInfo(sessionRes.data);
        } catch {
          // sem sessão ou não autenticado ainda — ok
        }
        setIsReady(true);
      } catch (err) {
        console.error("Erro init:", err);
      }
    };

    init();
  }, [address]);

  // --- CORRIGIDO: um único intervalo de polling (não dois) ---
  // Execuções a 3s, mas chamando refresh completo para evitar race condition
  // entre dois setIntervals chamando setExecutions simultaneamente.
  // 3s é tolerável para todos os dados do dashboard.
  useEffect(() => {
    if (!isReady) return;
    const id = setInterval(refresh, 3000);
    return () => clearInterval(id);
  }, [isReady, refresh]);

  const activeStrategies = useMemo(() => strategies.filter((s) => s.active), [strategies]);
  const priceChange = history.length > 1 ? ((price - history[0]) / history[0]) * 100 : 0;
  const priceUp = priceChange >= 0;
  const [execMode, setExecMode] = useState<"recurring" | "once">("recurring");
  const [cooldown, setCooldown] = useState("60");

  const handleAuthorize = async () => {
    try {
      await createSession(Number(spendingLimit), Number(expiryDays));
      const sessionRes = await getSession();
      if (sessionRes?.data) setSessionInfo(sessionRes.data);
      toast.success("🔑 Agente autorizado", {
        description: `Limite: ${spendingLimit} USDC · ${expiryDays} dias`,
      });
    } catch (err: any) {
      toast.error("Erro ao autorizar agente", { description: err.message });
    }
  };

  const handleRevoke = async () => {
    try {
      await revokeSession();
      setSessionInfo(null);
      toast.success("🔒 Sessão revogada — agente em modo manual");
    } catch (err: any) {
      toast.error("Erro ao revogar sessão", { description: err.message });
    }
  };

  const handleSignPhantom = async () => {
    if (!signingExecution) return;
    setSigning(true);
    try {
      let txHash: string;

      const isSwapExecution = signingExecution.explanation?.startsWith("Swap") ?? false;

      if (signingExecution.serialized_tx) {
        // Jupiter swap real (mainnet) — assina VersionedTransaction
        txHash = await signAndSendSwap(signingExecution.serialized_tx);
        toast.success("🔄 Swap executado via Jupiter", { description: `TX: ${txHash.slice(0, 8)}…` });
      } else if (isSwapExecution) {
        // Mock swap (devnet demo) — confirma sem assinatura Phantom real
        txHash = `demo_swap_${Date.now()}`;
        toast.success("🔄 Swap simulado (devnet demo)", {
          description: signingExecution.explanation ?? "swap executado",
        });
      } else {
        const strategy = strategies.find(s => String(s.id) === String(signingExecution.strategy_id));
        const dest = strategy?.destination_address ?? "";
        const isUsdc = signingExecution.token === "USDC";
        txHash = isUsdc
          ? await sendUsdc(dest, signingExecution.amount_usdc ?? 0)
          : await sendSol(dest, signingExecution.amount_sol);
        const label = isUsdc ? `${signingExecution.amount_usdc} USDC` : `${signingExecution.amount_sol} SOL`;
        toast.success(`✅ ${label} transferido`, { description: `TX: ${txHash.slice(0, 8)}…` });
      }

      await api.patch(`/executions/${signingExecution.id}/confirm`, { tx_hash: txHash });
      dismissedIds.current.add(signingExecution.id);
      setSigningExecution(null);
      await refresh();
    } catch (err: any) {
      toast.error("Erro ao assinar", { description: err.message });
    } finally {
      setSigning(false);
    }
  };

  const handleCreate = async () => {
    if (!address) { toast.error("Conecte o Phantom primeiro"); return; }

    if (strategyMode === "swap") {
      if (tokenIn === tokenOut) { toast.error("Token de entrada e saída devem ser diferentes"); return; }
      const dropVal = Number(dropPct);
      const amtVal = Number(amount);
      if (isNaN(dropVal) || dropVal <= 0) { toast.error("Queda % inválida"); return; }
      if (isNaN(amtVal) || amtVal <= 0) { toast.error("Quantidade inválida"); return; }
      setSubmitting(true);
      try {
        await createStrategy({
          type: "swap",
          drop_percent: dropVal,
          amount_sol: tokenIn === "SOL" ? amtVal : 0,
          amount_usdc: tokenIn === "USDC" ? amtVal : undefined,
          destination_address: address, // swap retorna para a própria wallet
          reference_price: price,
          cooldown_seconds: Number(cooldown),
          execution_mode: execMode,
          token: tokenIn,
          token_in: tokenIn,
          token_out: tokenOut,
          slippage_bps: Number(slippageBps),
        });
        toast.success("🔄 Agente de swap ativado", {
          description: `Swap ${amtVal} ${tokenIn} → ${tokenOut} se SOL cair ${dropVal}%`,
        });
        await refresh();
      } catch (err: any) {
        toast.error("Erro ao salvar", { description: err.response?.data?.detail?.[0]?.msg || err.message });
      } finally {
        setSubmitting(false);
      }
      return;
    }

    const parsed = strategySchema.safeParse({ drop_percent: dropPct, amount_sol: amount, destination_address: destination });
    if (!parsed.success) { toast.error(parsed.error.issues[0].message); return; }
    setSubmitting(true);
    try {
      await createStrategy({
        type: "buy",
        drop_percent: parsed.data.drop_percent,
        amount_sol: parsed.data.amount_sol,
        destination_address: parsed.data.destination_address,
        reference_price: price,
        cooldown_seconds: Number(cooldown),
        execution_mode: execMode,
        token,
        amount_usdc: token === "USDC" ? parsed.data.amount_sol : undefined,
      });
      toast.success("🤖 Agente ativado", {
        description: `Compra ${parsed.data.amount_sol} SOL se cair ${parsed.data.drop_percent}%`,
      });
      setDestination("");
      await refresh();
    } catch (err: any) {
      toast.error("Erro ao salvar", { description: err.response?.data?.detail?.[0]?.msg || err.message });
    } finally {
      setSubmitting(false);
    }
  };

  const handleToggle = async (s: Strategy) => {
    try {
      await api.patch(`/strategies/${s.id}`, { active: !s.active });
      await refresh();
    } catch {
      toast.error("Erro ao alterar estratégia");
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await api.delete(`/strategies/${id}`);
      await refresh();
    } catch {
      toast.error("Erro ao remover estratégia");
    }
  };

  // --- Demo toggle: ON = mantém preço simulado, OFF = volta ao real ---
  const handleToggleDemoMode = async (crashPercent = 6) => {
    setDemoLoading(true);
    try {
      if (demoActive) {
        // Desativa demo — volta ao preço real
        await api.delete("/demo/set-price");
        setDemoActive(false);
        toast.success("✅ Demo desativado — voltando ao preço real");
      } else {
        // Ativa demo — congela em preço baixo
        const crashedPrice = price * (1 - crashPercent / 100);
        await api.post("/demo/set-price", { price: crashedPrice });
        crash(crashPercent);
        setDemoActive(true);
        toast.info(`📉 Demo ativado — preço simulado por até 6%`, {
          description: "Clique novamente para desativar",
        });
      }
    } catch {
      toast.error("Erro ao alterar modo demo");
    } finally {
      setDemoLoading(false);
    }
  };

  const relativeTime = (dateStr: string) => {
    const normalized = dateStr.endsWith("Z") || dateStr.includes("+") ? dateStr : dateStr + "Z";
    const diff = Date.now() - new Date(normalized).getTime();
    const secs = Math.floor(diff / 1000);
    if (secs < 60) return "agora mesmo";
    const mins = Math.floor(secs / 60);
    if (mins < 60) return `há ${mins} min`;
    const hrs = Math.floor(mins / 60);
    if (hrs < 24) return `há ${hrs}h`;
    return new Date(dateStr).toLocaleDateString("pt-BR");
  };

  const humanizeExecution = (e: Execution) => {
    const isSwap = !!e.serialized_tx || (e.explanation?.startsWith("Swap") ?? false);
    const isUsdc = e.token === "USDC";
    const amount = isUsdc ? `${e.amount_usdc} USDC` : `${e.amount_sol} SOL`;
    const swapLabel = e.explanation ?? "swap";

    if (isSwap) {
      if (e.status === "success") return `Jupiter swap executado a $${Number(e.trigger_price).toFixed(2)} — ${swapLabel}`;
      if (e.status === "awaiting_signature") return `Aguardando assinatura Phantom — ${swapLabel}`;
      if (e.status === "expired") return `Swap expirado — sem assinatura em 3 min (${swapLabel})`;
      if (e.status === "failed") return `Swap falhou a $${Number(e.trigger_price).toFixed(2)}`;
    }

    if (e.status === "success")
      return `Transferi ${amount} a $${Number(e.trigger_price).toFixed(2)} — queda de ${Number(e.drop_percent).toFixed(1)}% detectada`;
    if (e.status === "failed")
      return `Tentativa de ${amount} a $${Number(e.trigger_price).toFixed(2)} falhou`;
    if (e.status === "awaiting_signature")
      return `Aguardando assinatura Phantom para ${amount}`;
    if (e.status === "expired")
      return `Expirado — sem assinatura em 3 min (${amount})`;
    return `Processando ${amount}…`;
  };

  return (
    <div className="min-h-screen relative">
      <div className="absolute inset-0 grid-bg opacity-30 pointer-events-none" />

      {/* HEADER */}
      <header className="relative border-b border-border/50 backdrop-blur-sm">
        <div className="container flex items-center justify-between py-5">
          <div className="flex items-center gap-3">
            <img src={logo} alt="SentinelFi" className="h-[50px] w-auto" />
            <p className="text-xs text-muted-foreground font-mono">
              solana · {import.meta.env.VITE_SOLANA_NETWORK ?? "mainnet-beta"}
            </p>
          </div>
          {address ? (
            
            <div className="flex items-center gap-2">
              {/* BOTÃO DE SALDO COM POPOVER */}
              <div className="relative">
                <button
                  onMouseEnter={() => setBalanceOpen(true)}
                  onMouseLeave={(e) => {
                    const related = e.relatedTarget as HTMLElement;
                    if (!related?.closest?.("[data-balance-popover]")) setBalanceOpen(false);
                  }}
                  onClick={() => setBalanceOpen(v => !v)}
                  className="hidden sm:flex items-center gap-2 px-3 py-2 rounded-lg bg-secondary/50 border border-border hover:bg-secondary/80 transition-colors"
                >
                  <div className="h-2 w-2 rounded-full bg-primary pulse-dot" />
                  <span className="font-mono text-sm">Saldo ▾</span>
                </button>
                {balanceOpen && balances && (
                  <div
                    data-balance-popover
                    onMouseEnter={() => setBalanceOpen(true)}
                    onMouseLeave={() => setBalanceOpen(false)}
                    className="absolute right-0 top-full mt-1 z-50 min-w-[160px] rounded-xl border border-border bg-background/95 backdrop-blur-sm shadow-lg p-3 space-y-2"
                  >
                    <div className="flex items-center justify-between gap-6 font-mono text-sm">
                      <span className="text-muted-foreground">◎ SOL</span>
                      <span className="font-semibold">{balances.sol}</span>
                    </div>
                    <div className="flex items-center justify-between gap-6 font-mono text-sm">
                      <span className="text-muted-foreground">💵 USDC</span>
                      <span className="font-semibold">{balances.usdc.toFixed(2)}</span>
                    </div>
                  </div>
                )}
              </div>
              <div className="hidden sm:flex items-center gap-2 px-3 py-2 rounded-lg bg-secondary/50 border border-border">
                <div className="h-2 w-2 rounded-full bg-primary pulse-dot" />
                <span className="font-mono text-sm">{address.slice(0, 4)}…{address.slice(-4)}</span>
              </div>
              <Button variant="ghost" size="sm" onClick={disconnect}>Desconectar</Button>
            </div>
          ) : (
            <Button onClick={connect} disabled={connecting} className="gap-2">
              <Wallet className="h-4 w-4" />
              {connecting ? "Conectando…" : "Conectar Phantom"}
            </Button>
          )}
        </div>
      </header>

      <main className="container relative py-10 space-y-8">
        {/* DEMO MODE BANNER */}
        {demoActive && (
          <div className="flex items-center gap-3 rounded-xl border border-yellow-500/40 bg-yellow-500/10 px-4 py-3 text-yellow-400">
            <FlaskConical className="h-4 w-4 shrink-0 animate-pulse" />
            <div className="flex-1 text-sm font-medium">
              MODO DEMO ATIVO — preço simulado em ${price.toFixed(2)} (queda 6%). Agente reagindo automaticamente…
            </div>
            <span className="font-mono text-xs opacity-60">mainnet · preços reais</span>
          </div>
        )}

        {/* HERO PRICE */}
        <section className="card-elevated rounded-2xl p-6 md:p-8">
          <div className="flex flex-wrap items-end justify-between gap-4 mb-6">
            <div>
              <p className="text-xs uppercase tracking-widest text-muted-foreground mb-2">SOL / USD · simulado</p>
              <div className="flex items-baseline gap-3">
                <span key={price} className="font-mono text-5xl md:text-6xl font-bold animate-ticker">
                  ${price.toFixed(2)}
                </span>
                <span className={`font-mono text-lg flex items-center gap-1 ${priceUp ? "text-primary" : "text-destructive"}`}>
                  {priceUp ? <TrendingUp className="h-4 w-4" /> : <TrendingDown className="h-4 w-4" />}
                  {priceChange.toFixed(2)}%
                </span>
              </div>
            </div>
            <div className="flex gap-2">
              <Button
                variant={demoActive ? "destructive" : "outline"}
                size="sm"
                onClick={() => handleToggleDemoMode(6)}
                disabled={demoLoading}
                className="gap-1"
              >
                {demoActive ? (
                  <>
                    <TrendingUp className="h-3 w-3" />
                    {demoLoading ? "Desativando…" : "⏹ Desativar Demo"}
                  </>
                ) : (
                  <>
                    <TrendingDown className="h-3 w-3" />
                    {demoLoading ? "Ativando…" : "🎬 Ativar Demo"}
                  </>
                )}
              </Button>
            </div>
          </div>
          <Sparkline data={history} />
          <div className="flex flex-wrap gap-6 mt-4 pt-4 border-t border-border/50 text-sm">
            <div className="flex items-center gap-2">
              <Activity className="h-4 w-4 text-primary" />
              <span className="text-muted-foreground">Agentes ativos:</span>
              <span className="font-mono font-semibold">{activeStrategies.length}</span>
            </div>
            <div className="flex items-center gap-2">
              <Zap className="h-4 w-4 text-accent" />
              <span className="text-muted-foreground">Execuções:</span>
              <span className="font-mono font-semibold">{executions.length}</span>
            </div>
          </div>
        </section>

        {/* SESSION KEYS — AUTORIZAR AGENTE */}
        {address && (
          <section className="card-elevated rounded-2xl p-6">
            <div className="flex items-center justify-between gap-2 mb-4">
              <div className="flex items-center gap-2">
                <div className={`h-8 w-8 rounded-lg flex items-center justify-center ${sessionInfo ? "bg-primary/10" : "bg-muted"}`}>
                  {sessionInfo
                    ? <ShieldCheck className="h-4 w-4 text-primary" />
                    : <Shield className="h-4 w-4 text-muted-foreground" />}
                </div>
                <div>
                  <h2 className="text-lg font-semibold leading-none">Autorização do Agente</h2>
                  <p className="text-xs text-muted-foreground mt-0.5">
                    {sessionInfo ? "Agente operando de forma autônoma" : "Agente aguardando autorização — assinatura manual em cada execução"}
                  </p>
                </div>
              </div>
              {sessionInfo && (
                <span className="shrink-0 text-xs font-medium px-2 py-1 rounded-full bg-primary/10 text-primary border border-primary/20">
                  ● ATIVO
                </span>
              )}
            </div>

            {sessionInfo ? (
              <div className="space-y-3">
                <div className="rounded-xl border border-border bg-secondary/30 p-4 grid grid-cols-2 sm:grid-cols-3 gap-4 font-mono text-sm">
                  <div>
                    <p className="text-xs text-muted-foreground mb-0.5">Limite de gasto</p>
                    <p className="font-semibold">{(sessionInfo.spending_limit / 1_000_000).toFixed(2)} USDC</p>
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground mb-0.5">Expira em</p>
                    <p className="font-semibold">{new Date(sessionInfo.expiry).toLocaleDateString("pt-BR")}</p>
                  </div>
                  <div className="col-span-2 sm:col-span-1">
                    <p className="text-xs text-muted-foreground mb-0.5">Delegate</p>
                    <p className="font-semibold text-xs truncate">{sessionInfo.delegate_pubkey.slice(0, 8)}…{sessionInfo.delegate_pubkey.slice(-6)}</p>
                  </div>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleRevoke}
                  disabled={revoking}
                  className="gap-2 text-destructive hover:text-destructive hover:bg-destructive/10 border-destructive/30"
                >
                  <ShieldOff className="h-4 w-4" />
                  {revoking ? "Revogando…" : "Revogar Sessão"}
                </Button>
              </div>
            ) : (
              <div className="space-y-3">
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <Label htmlFor="spendingLimit">Limite de gasto (USDC)</Label>
                    <Input
                      id="spendingLimit"
                      type="number"
                      min="1"
                      step="1"
                      value={spendingLimit}
                      onChange={(e) => setSpendingLimit(e.target.value)}
                      className="font-mono"
                    />
                    <p className="text-xs text-muted-foreground mt-1">Máximo que o agente pode gastar.</p>
                  </div>
                  <div>
                    <Label htmlFor="expiryDays">Validade (dias)</Label>
                    <Input
                      id="expiryDays"
                      type="number"
                      min="1"
                      max="30"
                      step="1"
                      value={expiryDays}
                      onChange={(e) => setExpiryDays(e.target.value)}
                      className="font-mono"
                    />
                    <p className="text-xs text-muted-foreground mt-1">Sessão expira automaticamente.</p>
                  </div>
                </div>
                <Button
                  onClick={handleAuthorize}
                  disabled={creating || !address}
                  className="w-full gap-2"
                >
                  <KeyRound className="h-4 w-4" />
                  {creating ? "Aguardando Phantom…" : "Autorizar Agente"}
                </Button>
              </div>
            )}
          </section>
        )}

        <div className="grid lg:grid-cols-2 gap-6">
          {/* CREATE STRATEGY */}
          <section className="card-elevated rounded-2xl p-6">
            <div className="flex items-center gap-2 mb-1">
              <div className="h-8 w-8 rounded-lg bg-primary/10 flex items-center justify-center">
                <Bot className="h-4 w-4 text-primary" />
              </div>
              <h2 className="text-lg font-semibold">Criar estratégia</h2>
            </div>
            <p className="text-sm text-muted-foreground mb-5">
              Se SOL cair X%, comprar Y SOL automaticamente.
            </p>
            <div className="space-y-4">
              {/* MODO: Transfer ou Swap */}
              <div className="grid grid-cols-2 gap-2">
                <button type="button" onClick={() => setStrategyMode("transfer")}
                  className={`rounded-lg border p-3 text-left transition-colors ${
                    strategyMode === "transfer"
                      ? "border-primary bg-primary/10 text-primary"
                      : "border-border bg-secondary/30 text-muted-foreground hover:bg-secondary/50"
                  }`}>
                  <div className="font-medium text-sm">💸 Transfer</div>
                  <div className="text-xs mt-0.5 opacity-70">SOL ou USDC para endereço</div>
                </button>
                <button type="button" onClick={() => setStrategyMode("swap")}
                  className={`rounded-lg border p-3 text-left transition-colors ${
                    strategyMode === "swap"
                      ? "border-primary bg-primary/10 text-primary"
                      : "border-border bg-secondary/30 text-muted-foreground hover:bg-secondary/50"
                  }`}>
                  <div className="font-medium text-sm">🔄 Swap Jupiter</div>
                  <div className="text-xs mt-0.5 opacity-70">Troca tokens via DEX</div>
                </button>
              </div>

              {strategyMode === "transfer" && (
                <div className="grid grid-cols-2 gap-2">
                  <button type="button" onClick={() => setToken("SOL")}
                    className={`rounded-lg border p-3 text-left transition-colors ${
                      token === "SOL"
                        ? "border-primary bg-primary/10 text-primary"
                        : "border-border bg-secondary/30 text-muted-foreground hover:bg-secondary/50"
                    }`}>
                    <div className="font-medium text-sm">◎ SOL</div>
                    <div className="text-xs mt-0.5 opacity-70">Execução automática</div>
                  </button>
                  <button type="button" onClick={() => setToken("USDC")}
                    className={`rounded-lg border p-3 text-left transition-colors ${
                      token === "USDC"
                        ? "border-primary bg-primary/10 text-primary"
                        : "border-border bg-secondary/30 text-muted-foreground hover:bg-secondary/50"
                    }`}>
                    <div className="font-medium text-sm">💵 USDC</div>
                    <div className="text-xs mt-0.5 opacity-70">Requer assinatura Phantom</div>
                  </button>
                </div>
              )}

              {strategyMode === "swap" && (
                <div className="space-y-3">
                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <Label>De (token_in)</Label>
                      <div className="grid grid-cols-2 gap-1 mt-1">
                        {(["SOL", "USDC"] as const).map((t) => (
                          <button key={t} type="button" onClick={() => setTokenIn(t)}
                            className={`rounded-md border p-2 text-xs font-medium transition-colors ${
                              tokenIn === t ? "border-primary bg-primary/10 text-primary" : "border-border bg-secondary/30 text-muted-foreground"
                            }`}>{t}</button>
                        ))}
                      </div>
                    </div>
                    <div>
                      <Label>Para (token_out)</Label>
                      <div className="grid grid-cols-2 gap-1 mt-1">
                        {(["SOL", "USDC"] as const).map((t) => (
                          <button key={t} type="button" onClick={() => setTokenOut(t)}
                            className={`rounded-md border p-2 text-xs font-medium transition-colors ${
                              tokenOut === t ? "border-primary bg-primary/10 text-primary" : "border-border bg-secondary/30 text-muted-foreground"
                            }`}>{t}</button>
                        ))}
                      </div>
                    </div>
                  </div>
                  <div>
                    <Label htmlFor="slippage">Slippage (bps) — 50 = 0.5%</Label>
                    <Input id="slippage" type="number" min="1" max="1000" value={slippageBps}
                      onChange={(e) => setSlippageBps(e.target.value)} className="font-mono" />
                  </div>
                </div>
              )}

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <Label htmlFor="drop">Cair (%)</Label>
                  <Input id="drop" type="number" step="0.1" value={dropPct}
                    onChange={(e) => setDropPct(e.target.value)} className="font-mono" />
                </div>
                <div>
                  <Label htmlFor="amount">
                    {strategyMode === "swap" ? `Quantidade (${tokenIn})` : `Comprar (${token})`}
                  </Label>
                  <Input id="amount" type="number" step="0.0001" value={amount}
                    onChange={(e) => setAmount(e.target.value)} className="font-mono" />
                </div>
              </div>

              {strategyMode === "transfer" && (
                <div>
                  <Label htmlFor="dest">Endereço destino (Devnet)</Label>
                  <Input id="dest" placeholder="Ex: 4Nd1m…" value={destination}
                    onChange={(e) => setDestination(e.target.value)} className="font-mono text-xs" />
                </div>
              )}
              <div className="rounded-lg bg-secondary/40 border border-border p-3 text-sm font-mono">
                <span className="text-muted-foreground">Preço de referência: </span>
                <span className="font-semibold">${price.toFixed(2)}</span>
              </div>
              {/* toggle de modo — vai logo acima do botão de submit */}
              <div className="grid grid-cols-2 gap-2">
                <button
                  type="button"
                  onClick={() => setExecMode("recurring")}
                  className={`rounded-lg border p-3 text-left transition-colors ${
                    execMode === "recurring"
                      ? "border-primary bg-primary/10 text-primary"
                      : "border-border bg-secondary/30 text-muted-foreground hover:bg-secondary/50"
                  }`}
                >
                  <div className="font-medium text-sm">🔁 Recorrente</div>
                  <div className="text-xs mt-0.5 opacity-70">
                    Executa toda vez que a condição for atingida
                  </div>
                </button>
                <button
                  type="button"
                  onClick={() => setExecMode("once")}
                  className={`rounded-lg border p-3 text-left transition-colors ${
                    execMode === "once"
                      ? "border-primary bg-primary/10 text-primary"
                      : "border-border bg-secondary/30 text-muted-foreground hover:bg-secondary/50"
                  }`}
                >
                  <div className="font-medium text-sm">⚡ Uma vez</div>
                  <div className="text-xs mt-0.5 opacity-70">
                    Executa uma única vez e se desativa
                  </div>
                </button>
              </div>
              <div>
                <Label htmlFor="cooldown">Cooldown (segundos)</Label>
                <Input
                  id="cooldown"
                  type="number"
                  min="10"
                  step="10"
                  value={cooldown}
                  onChange={(e) => setCooldown(e.target.value)}
                  className="font-mono"
                />
                <p className="text-xs text-muted-foreground mt-1">
                  Tempo mínimo entre execuções da mesma estratégia.
                </p>
              </div>
              <Button
                onClick={handleCreate}
                disabled={submitting || !address}
                className="w-full gap-2"
                size="lg"
              >
                <Power className="h-4 w-4" />
                {address
                  ? submitting
                    ? "Ativando…"
                    : `Ativar Agente ${execMode === "once" ? "· Uma vez" : "· Recorrente"}`
                  : "Conecte a wallet primeiro"}
              </Button>
            </div>
          </section>

          {/* ACTIVE STRATEGIES */}
          <section className="card-elevated rounded-2xl p-6">
            <div className="flex items-center gap-2 mb-5">
              <div className="h-8 w-8 rounded-lg bg-accent/10 flex items-center justify-center">
                <Activity className="h-4 w-4 text-accent" />
              </div>
              <h2 className="text-lg font-semibold">Suas estratégias</h2>
            </div>
            {strategies.length === 0 ? (
              <div className="text-center py-12 text-muted-foreground text-sm">
                Nenhuma estratégia ainda. Crie uma do lado.
              </div>
            ) : (
              <ul className="space-y-3">
                {strategies.map((s) => {
                  const dropNow = ((s.reference_price - price) / s.reference_price) * 100;
                  const progress = Math.min(100, Math.max(0, (dropNow / s.drop_percent) * 100));
                  return (
                    <li key={s.id} className="rounded-xl border border-border bg-secondary/30 p-4">
                      <div className="flex items-start justify-between gap-2 mb-2">
                        <div>
                          <div className="font-mono text-sm">
                            <span className="text-primary font-semibold">−{s.drop_percent}%</span>
                            <span className="text-muted-foreground"> → comprar </span>
                            <span className="font-semibold">{s.amount_sol} SOL</span>
                          </div>
                          <div className="text-xs text-muted-foreground font-mono mt-0.5">
                            ref ${Number(s.reference_price).toFixed(2)} · {s.destination_address?.slice(0, 6)}…{s.destination_address?.slice(-4)}
                          </div>
                        </div>
                        <div className="flex items-center gap-1">
                          <button onClick={() => handleToggle(s)}
                            className={`text-xs px-2 py-1 rounded-md font-medium transition-colors ${
                              s.active ? "bg-primary/15 text-primary hover:bg-primary/25" : "bg-muted text-muted-foreground"
                            }`}>
                            {s.active ? "● ATIVO" : "○ pausado"}
                          </button>
                          <button onClick={() => handleDelete(s.id)}
                            className="p-1.5 rounded-md hover:bg-destructive/10 text-muted-foreground hover:text-destructive transition-colors">
                            <Trash2 className="h-3.5 w-3.5" />
                          </button>
                        </div>
                      </div>
                      <div className="h-1.5 rounded-full bg-muted overflow-hidden">
                        <div className="h-full bg-gradient-to-r from-primary to-accent transition-all duration-500"
                          style={{ width: `${progress}%` }} />
                      </div>
                      <p className="text-xs text-muted-foreground mt-1.5 font-mono">
                        queda atual: {dropNow.toFixed(2)}% / {s.drop_percent}%
                      </p>
                    </li>
                  );
                })}
              </ul>
            )}
          </section>
        </div>

        {/* EXECUTION FEED */}
        <section className="card-elevated rounded-2xl p-6">
          <div className="flex items-center justify-between mb-5">
            <div className="flex items-center gap-2">
              <div className="h-8 w-8 rounded-lg bg-primary/10 flex items-center justify-center">
                <Zap className="h-4 w-4 text-primary" />
              </div>
              <h2 className="text-lg font-semibold">Histórico de execuções</h2>
            </div>
            {isReady && (
              <span className="text-xs text-muted-foreground font-mono animate-pulse">● ao vivo</span>
            )}
          </div>
          {executions.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground text-sm">
              Nada executado ainda. Use "Simular queda" para testar.
            </div>
          ) : (
            <ul className="space-y-3">
              {executions.map((e) => (
                <li key={e.id} className={`flex gap-4 rounded-xl border p-4 transition-colors ${
                  e.status === "success"           ? "border-primary/20 bg-primary/5" :
                  e.status === "failed"            ? "border-destructive/20 bg-destructive/5" :
                  e.status === "expired"           ? "border-yellow-500/20 bg-yellow-500/5" :
                  "border-border bg-secondary/20"
                }`}>
                  <div className="shrink-0 mt-0.5">
                    {e.status === "success"           && <CheckCircle2 className="h-5 w-5 text-primary" />}
                    {e.status === "failed"            && <XCircle className="h-5 w-5 text-destructive" />}
                    {e.status === "expired"           && <Timer className="h-5 w-5 text-yellow-500" />}
                    {e.status === "pending"           && <Clock className="h-5 w-5 text-muted-foreground animate-pulse" />}
                    {e.status === "awaiting_signature" && <Clock className="h-5 w-5 text-accent animate-pulse" />}
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center justify-between gap-2 mb-1">
                      <p className="text-sm font-semibold leading-snug">
                        🤖 Agente: {humanizeExecution(e)}
                      </p>
                      <span className="shrink-0 text-xs text-muted-foreground font-mono">
                        {relativeTime(e.created_at)}
                      </span>
                    </div>
                    <p className="text-xs text-muted-foreground">
                      ref ${Number(e.reference_price).toFixed(2)} · queda alvo {Number(e.drop_percent).toFixed(1)}%
                      {e.explanation ? ` · ${e.explanation}` : ""}
                    </p>
                    {e.tx_hash && !e.tx_hash.startsWith("demo_") ? (
                      <a href={`https://explorer.solana.com/tx/${e.tx_hash}`}
                        target="_blank" rel="noreferrer"
                        className="inline-flex items-center gap-1 mt-2 text-xs font-mono text-accent hover:underline">
                        <ExternalLink className="h-3 w-3" />
                        ver no Solana Explorer
                      </a>
                    ) : e.tx_hash?.startsWith("demo_") ? (
                      <span className="inline-flex items-center gap-1 mt-2 text-xs font-mono text-muted-foreground">
                        <FlaskConical className="h-3 w-3" />
                        swap simulado
                      </span>
                    ) : null}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </section>

        <footer className="text-center text-xs text-muted-foreground font-mono pb-4">
          Solana Devnet · sem risco financeiro · {sessionInfo ? "agente operando de forma autônoma via Session Keys" : "transações assinadas pela Phantom"}
        </footer>
      </main>

      {/* MODAL DE ASSINATURA */}
      {signingExecution && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <div className="card-elevated rounded-2xl p-6 max-w-sm w-full mx-4 space-y-4">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-xl bg-primary/10 flex items-center justify-center">
                {signingExecution.serialized_tx ? <span className="text-lg">🔄</span> : <Bot className="h-5 w-5 text-primary" />}
              </div>
              <div>
                <h3 className="font-semibold">
                  {signingExecution.serialized_tx ? "Agente quer fazer swap" : "Agente quer executar"}
                </h3>
                <p className="text-xs text-muted-foreground">Assinatura necessária via Phantom</p>
              </div>
            </div>
            <div className="rounded-lg bg-secondary/40 border border-border p-4 space-y-2 font-mono text-sm">
              {signingExecution.serialized_tx ? (
                <>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Operação</span>
                    <span className="font-semibold text-primary">Jupiter Swap</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Detalhe</span>
                    <span className="font-semibold text-xs">{signingExecution.explanation}</span>
                  </div>
                </>
              ) : (
                <>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Token</span>
                    <span className="font-semibold">
                      {signingExecution.token === "USDC" ? "💵 USDC" : "◎ SOL"}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Valor</span>
                    <span className="font-semibold">
                      {signingExecution.token === "USDC"
                        ? `${signingExecution.amount_usdc} USDC`
                        : `${signingExecution.amount_sol} SOL`}
                    </span>
                  </div>
                </>
              )}
              <div className="flex justify-between">
                <span className="text-muted-foreground">Preço trigger</span>
                <span className="font-semibold">${Number(signingExecution.trigger_price).toFixed(2)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Queda</span>
                <span className="font-semibold text-destructive">−{Number(signingExecution.drop_percent).toFixed(1)}%</span>
              </div>
            </div>
            <div className="flex gap-2">
              <Button variant="ghost" className="flex-1"
                onClick={() => { dismissedIds.current.add(signingExecution.id); setSigningExecution(null); }} disabled={signing}>
                Ignorar
              </Button>
              <Button className="flex-1 gap-2" onClick={handleSignPhantom} disabled={signing}>
                <Zap className="h-4 w-4" />
                {signing
                  ? "Executando…"
                  : signingExecution.serialized_tx
                    ? "Assinar com Phantom"
                    : signingExecution.explanation?.startsWith("Swap")
                      ? "Simular Swap"
                      : "Assinar com Phantom"}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Index;

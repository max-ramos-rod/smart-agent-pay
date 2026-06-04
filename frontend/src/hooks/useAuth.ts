import { loginWithWallet as loginService } from "@/services/auth";
import type { WalletAuthProvider } from "@/services/auth";
import { useCallback } from "react";

export const useAuth = () => {
  const loginWithWallet = useCallback(async (provider: WalletAuthProvider, publicKey: string) => {
    return await loginService(provider, publicKey);
  }, []);

  return { loginWithWallet };
};

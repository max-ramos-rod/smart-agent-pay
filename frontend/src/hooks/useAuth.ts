import { loginWithWallet as loginService } from "@/services/auth";

export const useAuth = () => {
  const loginWithWallet = async (provider: any, publicKey: string) => {
    return await loginService(provider, publicKey);
  };

  return { loginWithWallet };
};
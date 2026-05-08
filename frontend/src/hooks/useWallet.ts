import { useQuery } from "@tanstack/react-query";
import { getBalance } from "@/services/wallet";

export const useWallet = () => {
  return useQuery({
    queryKey: ["wallet"],
    queryFn: getBalance,
  });
};
import { useMutation, useQuery } from "@tanstack/react-query";
import { createSession, getSession } from "@/services/agent";

export const useSession = () =>
  useQuery({
    queryKey: ["session"],
    queryFn: getSession,
  });

export const useCreateSession = () =>
  useMutation({
    mutationFn: (max_amount: number) =>
      createSession(max_amount),
  });
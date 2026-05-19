import { useQuery, useMutation } from "@tanstack/react-query";
import { createStrategy, getStrategies } from "@/services/strategy";

export const useStrategies = () =>
  useQuery({
    queryKey: ["strategies"],
    queryFn: getStrategies,
  });

export const useCreateStrategy = () =>
  useMutation({
    mutationFn: createStrategy,
  });
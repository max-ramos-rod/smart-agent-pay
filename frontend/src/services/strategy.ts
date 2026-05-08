// services/strategy.ts — versão atualizada
import { api } from "./api";

type ApiResponse<T> = { data: T; meta: any };

export const getStrategies = async () => {
  const response = await api.get<ApiResponse<Strategy[]>>("/strategies");
  return response.data.data;
};

export const createStrategy = async (payload: {
  type: string;
  drop_percent: number;
  amount_sol: number;
  destination_address: string;
  reference_price: number;
  cooldown_seconds?: number;
  execution_mode?: "once" | "recurring";
}) => {
  const { data } = await api.post("/strategies", payload);
  return data.data;
};

// toggle ativo/inativo — chama PATCH /strategies/:id
export const toggleStrategy = async (id: number, active: boolean) => {
  const { data } = await api.patch(`/strategies/${id}`, { active });
  return data.data;
};

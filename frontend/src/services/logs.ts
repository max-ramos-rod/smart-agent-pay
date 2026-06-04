import { api } from "./api";

type ApiResponse<T> = {
  data: T;
  meta: unknown;
};

export const getExecutions = async () => {
  const response = await api.get<ApiResponse<Execution[]>>("/executions");
  return response.data.data;
};

import { api } from "./api";

type ApiResponse<T> = {
  data: T;
  meta: any;
};

export const getExecutions = async () => {
  const response = await api.get<ApiResponse<Execution[]>>("/executions");
  return response.data.data;
};
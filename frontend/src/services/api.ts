import axios from "axios";

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
});

api.interceptors.request.use((config) => {
  const address = localStorage.getItem("wallet_address");
  console.log("WALLET ADDRESS SEND:", address);
  if (address) {
    config.headers["X-Wallet-Address"] = address;
  }

  const token = localStorage.getItem("token");
  console.log("TOKEN SEND:", token);
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  return config;
});

let isRefreshing = false;
let failedQueue: any[] = [];

const processQueue = (error: any, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (token) {
      prom.resolve(token);
    } else {
      prom.reject(error);
    }
  });

  failedQueue = [];
};

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status !== 401) {
      return Promise.reject(error);
    }

    // evita loop infinito
    if (originalRequest._retry) {
      return Promise.reject(error);
    }

    originalRequest._retry = true;

    if (isRefreshing) {
      return new Promise((resolve, reject) => {
        failedQueue.push({
          resolve: (token: string) => {
            originalRequest.headers.Authorization = `Bearer ${token}`;
            resolve(api(originalRequest));
          },
          reject,
        });
      });
    }

    isRefreshing = true;

    try {
      const refreshToken = localStorage.getItem("refresh_token");

      if (!refreshToken) {
        processQueue(error, null);
        return Promise.reject(error);
      }

      const res = await axios.post(
        `${import.meta.env.VITE_API_URL}/auth/refresh`,
        { refresh_token: refreshToken }
      );

      const newToken = res.data.access_token;
      localStorage.setItem("token", newToken);
      localStorage.setItem("refresh_token", res.data.refresh_token);

      processQueue(null, newToken);

      originalRequest.headers.Authorization = `Bearer ${newToken}`;

      return api(originalRequest);
    } catch (err) {
      processQueue(err, null);
      localStorage.removeItem("token");
      localStorage.removeItem("refresh_token");
      return Promise.reject(err);
    } finally {
      isRefreshing = false;
    }
  }
);
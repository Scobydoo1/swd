import axios from "axios";

// Web (Vite dev/preview, hoặc backend serve cùng origin): để trống -> dùng "/api"
// tương đối, proxy qua Vite. APK Capacitor đứng một mình: set VITE_API_BASE thành
// URL tuyệt đối của backend (vd http://192.168.100.6:8000/api) khi build.
const API_BASE = import.meta.env.VITE_API_BASE ?? "/api";

export const api = axios.create({ baseURL: API_BASE });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem("token");
      if (location.pathname !== "/login") location.href = "/login";
    }
    return Promise.reject(err);
  }
);

import axios, { AxiosError, type InternalAxiosRequestConfig } from "axios";

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

// Render free tier ngủ sau ~15 phút không dùng; request đầu tiên đánh thức service
// mất 30-60s và trong lúc đó trả 502/503 hoặc lỗi mạng (không kèm header CORS).
// Tự thử lại nhiều lần để người dùng không thấy "Có lỗi xảy ra" khi backend đang dậy.
const COLD_START_RETRIES = 10;
const RETRY_DELAY_MS = 5000;

type RetryConfig = InternalAxiosRequestConfig & { _retry?: number };

api.interceptors.response.use(
  (res) => res,
  async (err: AxiosError) => {
    const config = err.config as RetryConfig | undefined;

    // 401: token hết hạn/không hợp lệ -> về trang đăng nhập (giữ hành vi cũ).
    if (err.response?.status === 401) {
      localStorage.removeItem("token");
      if (location.pathname !== "/login") location.href = "/login";
      return Promise.reject(err);
    }

    // Cold-start: không có response (lỗi mạng/CORS khi backend đang dậy) hoặc
    // gateway 502/503/504. Các trường hợp này request CHƯA tới app nên retry an toàn,
    // không gây trùng dữ liệu cho POST.
    const isColdStart =
      !err.response || [502, 503, 504].includes(err.response.status);
    if (config && isColdStart) {
      config._retry = (config._retry ?? 0) + 1;
      if (config._retry <= COLD_START_RETRIES) {
        await new Promise((r) => setTimeout(r, RETRY_DELAY_MS));
        return api(config);
      }
    }

    return Promise.reject(err);
  }
);

// Đánh thức backend ngay khi mở app (fire-and-forget) để lúc người dùng đăng nhập
// thì service đã sẵn sàng. Lỗi được nuốt — interceptor ở trên đã tự retry.
export function warmUpBackend(): void {
  api.get("/health").catch(() => {
    /* im lặng — chỉ nhằm đánh thức Render free tier */
  });
}

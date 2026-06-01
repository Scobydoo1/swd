import type { CapacitorConfig } from "@capacitor/cli";

const config: CapacitorConfig = {
  appId: "com.maple.app",
  appName: "Maple",
  webDir: "dist",
  server: {
    // Backend demo chạy HTTP (chưa có TLS) nên dùng scheme http cho webview để
    // gọi http://<backend> không bị chặn vì mixed-content, và bật cleartext.
    // Lên production (backend HTTPS) thì bỏ 2 dòng này để mặc định androidScheme=https.
    androidScheme: "http",
    cleartext: true,

    // --- Tuỳ chọn LIVE-RELOAD khi dev (không cần build lại APK mỗi lần sửa code) ---
    // Mở comment + đổi IP thành IP LAN của máy chạy Vite (npm run dev --host).
    // App sẽ tải web trực tiếp từ Vite, /api proxy qua luôn nên không cần VITE_API_BASE.
    //   - Điện thoại cùng Wi-Fi:  http://192.168.100.6:5173
    //   - Android emulator:       http://10.0.2.2:5173
    // url: "http://192.168.100.6:5173",
  },
};

export default config;

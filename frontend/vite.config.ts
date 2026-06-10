import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  // Web build cho GitHub Pages (project site) chạy dưới subpath /swd/ nên cần base.
  // Workflow deploy đặt VITE_BASE=/swd/. Dev local & build APK Capacitor để trống
  // -> base "/" (Capacitor nạp web từ gốc webview, không có subpath).
  base: process.env.VITE_BASE || "/",
  plugins: [react()],
  server: {
    // host: true -> lắng nghe trên 0.0.0.0 để emulator (10.0.2.2) và điện thoại
    // cùng Wi-Fi (http://<IP-máy>:5173) truy cập được. Proxy /api vẫn chạy trên
    // máy này nên backend :8000 không cần mở ra mạng.
    host: true,
    port: 5173,
    proxy: {
      "/api": "http://localhost:8000",
    },
  },
});

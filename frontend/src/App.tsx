import { Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "./auth/AuthContext";
import { ChatSessionProvider } from "./chat/ChatSessionContext";
import { AppLayout } from "./components/layout/AppLayout";
import { AdminPage } from "./pages/AdminPage";
import { ChatPage } from "./pages/ChatPage";
import { DocumentsPage } from "./pages/DocumentsPage";
import { LoginPage } from "./pages/LoginPage";
import { PricingPage } from "./pages/PricingPage";
import { QuizzesPage } from "./pages/QuizzesPage";
import { RoomDetailPage } from "./pages/RoomDetailPage";
import { RoomsPage } from "./pages/RoomsPage";

function Protected({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  if (loading)
    return (
      <div className="flex h-screen items-center justify-center text-accent">
        Đang tải…
      </div>
    );
  return user ? <>{children}</> : <Navigate to="/login" replace />;
}

// Lecturer không dùng AI chat — trang chủ của họ là Phòng học.
function Home() {
  const { user } = useAuth();
  if (user?.role === "LECTURER") return <Navigate to="/rooms" replace />;
  return <ChatPage />;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/"
        element={
          <Protected>
            <ChatSessionProvider>
              <AppLayout />
            </ChatSessionProvider>
          </Protected>
        }
      >
        <Route index element={<Home />} />
        <Route path="documents" element={<DocumentsPage />} />
        <Route path="rooms" element={<RoomsPage />} />
        <Route path="rooms/:id" element={<RoomDetailPage />} />
        <Route path="quizzes" element={<QuizzesPage />} />
        <Route path="pricing" element={<PricingPage />} />
        <Route path="admin" element={<AdminPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

/**
 * Корневой компонент приложения
 */
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { Toaster } from 'react-hot-toast';
import { useAuthStore } from './store';
import AppLayout from './components/shared/AppLayout';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 2,
      staleTime: 30_000,
      refetchOnWindowFocus: false,
    },
  },
});

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuthStore();
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route
            path="/*"
            element={
              <ProtectedRoute>
                <AppLayout>
                  <Routes>
                    <Route path="/" element={<DashboardPage />} />
                    {/* Lazy-loaded pages */}
                    <Route path="/attendance" element={<div className="p-6">Посещаемость</div>} />
                    <Route path="/persons" element={<div className="p-6">База персон</div>} />
                    <Route path="/cameras" element={<div className="p-6">Камеры</div>} />
                    <Route path="/analytics" element={<div className="p-6">Аналитика</div>} />
                    <Route path="/reports" element={<div className="p-6">Отчёты</div>} />
                    <Route path="/settings" element={<div className="p-6">Настройки</div>} />
                    <Route path="*" element={<Navigate to="/" replace />} />
                  </Routes>
                </AppLayout>
              </ProtectedRoute>
            }
          />
        </Routes>
      </BrowserRouter>

      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            borderRadius: '10px',
            fontSize: '13px',
          },
        }}
      />

      {import.meta.env.DEV && <ReactQueryDevtools />}
    </QueryClientProvider>
  );
}

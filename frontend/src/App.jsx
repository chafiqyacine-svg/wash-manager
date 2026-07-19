import { Navigate, Route, Routes } from "react-router-dom";
import Sidebar from "./components/Sidebar.jsx";
import { useAuth } from "./context/AuthContext.jsx";
import Anomalies from "./pages/Anomalies.jsx";
import Bays from "./pages/Bays.jsx";
import Caisse from "./pages/Caisse.jsx";
import Config from "./pages/Config.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import Employees from "./pages/Employees.jsx";
import History from "./pages/History.jsx";
import LiveView from "./pages/LiveView.jsx";
import Login from "./pages/Login.jsx";
import Payments from "./pages/Payments.jsx";
import Queue from "./pages/Queue.jsx";
import Rapprochement from "./pages/Rapprochement.jsx";
import Reports from "./pages/Reports.jsx";
import Vehicules from "./pages/Vehicules.jsx";

function Protected({ children }) {
  const { isAuth } = useAuth();
  return isAuth ? children : <Navigate to="/login" replace />;
}

function Layout({ children }) {
  return (
    <div className="flex min-h-screen bg-slate-100 text-slate-800">
      <Sidebar />
      <main className="flex-1 p-6">{children}</main>
    </div>
  );
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        path="/*"
        element={
          <Protected>
            <Layout>
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/caisse" element={<Caisse />} />
                <Route path="/live" element={<LiveView />} />
                <Route path="/history" element={<History />} />
                <Route path="/anomalies" element={<Anomalies />} />
                <Route path="/bays" element={<Bays />} />
                <Route path="/queue" element={<Queue />} />
                <Route path="/payments" element={<Payments />} />
                <Route path="/vehicules" element={<Vehicules />} />
                <Route path="/rapprochement" element={<Rapprochement />} />
                <Route path="/employees" element={<Employees />} />
                <Route path="/reports" element={<Reports />} />
                <Route path="/config" element={<Config />} />
              </Routes>
            </Layout>
          </Protected>
        }
      />
    </Routes>
  );
}

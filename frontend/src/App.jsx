import { useEffect, useState } from "react";
import { useAuth } from "./hooks/useAuth.jsx";
import Layout, { NAV } from "./components/Layout.jsx";
import { Spinner } from "./components/ui.jsx";
import AuthPage from "./pages/AuthPage.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import Chat from "./pages/Chat.jsx";
import Records from "./pages/Records.jsx";
import Trends from "./pages/Trends.jsx";
import Recommendations from "./pages/Recommendations.jsx";
import Appointments from "./pages/Appointments.jsx";
import SettingsPage from "./pages/Settings.jsx";

const PAGES = {
  dashboard: Dashboard, chat: Chat, records: Records, trends: Trends,
  recommendations: Recommendations, appointments: Appointments, settings: SettingsPage,
};
const readHash = () => {
  const h = window.location.hash.replace("#", "");
  return NAV.some((n) => n.id === h) ? h : "dashboard";
};

export default function App() {
  const { user, loading } = useAuth();
  const [page, setPage] = useState(readHash());
  useEffect(() => {
    const onHash = () => setPage(readHash());
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);
  const go = (id) => { window.location.hash = id; };

  if (loading) return <Spinner />;
  if (!user) return <AuthPage />;
  const Page = PAGES[page];
  return <Layout page={page} go={go}><Page go={go} /></Layout>;
}

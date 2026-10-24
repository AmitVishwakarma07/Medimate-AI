import { useState } from "react";
import { Activity, CalendarDays, ClipboardList, HeartPulse, LayoutDashboard, LogOut, Menu, MessageCircle, Settings, Sparkles, X } from "lucide-react";
import { useAuth } from "../hooks/useAuth.jsx";

export const NAV = [
  { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
  { id: "chat", label: "AI Chatbot", icon: MessageCircle },
  { id: "records", label: "Health Records", icon: ClipboardList },
  { id: "trends", label: "Health Trends", icon: Activity },
  { id: "recommendations", label: "Wellness Tips", icon: Sparkles },
  { id: "appointments", label: "Appointments", icon: CalendarDays },
  { id: "settings", label: "Profile & Settings", icon: Settings },
];

export default function Layout({ page, go, children }) {
  const [open, setOpen] = useState(false);
  const { logout, user } = useAuth();
  const choose = (id) => { go(id); setOpen(false); };

  return (
    <div className="app">
      <div className={`backdrop ${open ? "open" : ""}`} onClick={() => setOpen(false)} />
      <nav className={`sidebar ${open ? "open" : ""}`} aria-label="Main navigation">
        <div className="brand"><HeartPulse /> MediMate AI</div>
        {NAV.map(({ id, label, icon: Icon }) => (
          <button key={id} className={`nav-link ${page === id ? "active" : ""}`} onClick={() => choose(id)}
                  aria-current={page === id ? "page" : undefined}>
            <Icon size={18} /> {label}
          </button>
        ))}
        <div className="spacer" />
        <p className="muted" style={{ padding: "0 .8rem" }}>Signed in as<br /><strong>{user?.name}</strong></p>
        <button className="nav-link" onClick={logout}><LogOut size={18} /> Log out</button>
      </nav>
      <main className="main">
        <div className="topbar">
          <button className="hamburger" onClick={() => setOpen(!open)} aria-label="Toggle menu">
            {open ? <X /> : <Menu />}
          </button>
          <HeartPulse size={20} /> MediMate AI
        </div>
        {children}
      </main>
    </div>
  );
}

import { useEffect, useState } from "react";
import { api } from "../services/api";

// Plain-language privacy notice. The site operator MUST set CONTACT_EMAIL on the server and have this
// text reviewed before real users sign up.
export default function PrivacyNotice() {
  const [contact, setContact] = useState("");
  useEffect(() => { api.publicConfig().then((c) => setContact(c.contact_email || "")).catch(() => {}); }, []);
  const CONTACT = contact || "[operator: set CONTACT_EMAIL on the server]";

  return (
    <div className="privacy">
      <h3>Privacy notice</h3>
      <p><strong>What we collect:</strong> your name, email, a password (stored only as a one-way hash), the goals and
        settings you choose, and the health records, appointment reminders and wellness progress you enter.</p>
      <p><strong>Why:</strong> only to run this app for you - to show your records and charts, give general wellness
        suggestions, and keep your reminders. We do not sell your data or use it for advertising.</p>
      <p><strong>Chatbot:</strong> by default questions are answered by a built-in rule-based helper and stay on the server.
        Only if you turn on external AI in Settings (and the server has it configured) is the text you type sent to that
        AI service. Your health records are never sent.</p>
      <p><strong>Your choices:</strong> in Settings you can download all your data, change your password, withdraw the
        external-AI permission, or delete your account and all your data at any time.</p>
      <p><strong>Not medical advice:</strong> MediMate AI is not a medical device and does not diagnose or treat. For
        emergencies contact your local emergency services.</p>
      <p><strong>Questions or complaints:</strong> {CONTACT}</p>
    </div>
  );
}

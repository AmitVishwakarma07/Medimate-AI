import { useEffect, useRef, useState } from "react";
import { Send } from "lucide-react";
import { api } from "../services/api";
import { useAsync } from "../hooks/useAsync";
import { PageHead } from "../components/ui.jsx";

const SUGGESTED = [
  "What are common causes of a headache?",
  "How can I improve my sleep habits?",
  "What are some healthy hydration habits?",
  "What does blood pressure mean?",
  "When should I seek medical help for a symptom?",
];
const time = (d) => d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

export default function Chat() {
  const { data: status } = useAsync(() => api.chatStatus());
  const [msgs, setMsgs] = useState([{
    role: "assistant", ts: new Date(), source: "intro",
    text: "Hi! I can share general health education. I'm not a doctor and can't diagnose or recommend medicines. Pick a suggested question or type your own.",
  }]);
  const [text, setText] = useState("");
  const [typing, setTyping] = useState(false);
  const end = useRef(null);
  useEffect(() => { end.current?.scrollIntoView({ behavior: "smooth" }); }, [msgs, typing]);

  async function send(q) {
    const message = (q ?? text).trim();
    if (!message || typing) return;
    setText("");
    setMsgs((m) => [...m, { role: "user", text: message, ts: new Date() }]);
    setTyping(true);
    try {
      const r = await api.chat(message);
      setMsgs((m) => [...m, { role: "assistant", text: r.reply, ts: new Date(), source: r.source, emergency: r.emergency }]);
    } catch (e) {
      setMsgs((m) => [...m, { role: "assistant", text: `Sorry, something went wrong: ${e.message}`, ts: new Date(), source: "error" }]);
    } finally {
      setTyping(false);
    }
  }

  const usingLlm = status?.mode === "llm";
  return (
    <>
      <PageHead title="AI Healthcare Chatbot" subtitle="General educational information only" />
      <div className="notice">
        <strong>I am not a doctor.</strong> This is not medical advice. For emergencies contact your local emergency services immediately.
        {status && (usingLlm
          ? " Your typed questions are sent to an external AI service because you allowed it in Settings. Your health records are never sent."
          : " Answers come from a simple built-in rule-based helper (not a real AI model); nothing leaves this app.")}
      </div>
      <div className="card chat">
        <div className="messages" aria-live="polite">
          {msgs.map((m, i) => (
            <div key={i} className={`msg ${m.role} ${m.emergency ? "emergency" : ""}`}>
              {m.text}
              <div className="meta">
                {time(m.ts)}{m.role === "assistant" && m.source === "rule_based" && " - rule-based helper"}
                {m.role === "assistant" && m.source === "llm" && " - external AI model"}
              </div>
            </div>
          ))}
          {typing && <div className="msg assistant typing" aria-label="Assistant is typing"><span /><span /><span /></div>}
          <div ref={end} />
        </div>
        <div className="chips">
          {SUGGESTED.map((s) => <button key={s} className="chip" onClick={() => send(s)}>{s}</button>)}
        </div>
        <form className="chat-input" onSubmit={(e) => { e.preventDefault(); send(); }}>
          <input value={text} onChange={(e) => setText(e.target.value)} maxLength={1000} placeholder="Ask a general health question..." aria-label="Your message" />
          <button className="btn" disabled={typing || !text.trim()}><Send size={16} /> Send</button>
        </form>
      </div>
    </>
  );
}

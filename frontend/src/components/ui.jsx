import { Inbox } from "lucide-react";

export const Spinner = () => <div className="spinner" role="status" aria-label="Loading" />;

export function Empty({ icon: Icon = Inbox, title, hint, children }) {
  return (
    <div className="empty">
      <Icon size={36} />
      <p><strong>{title}</strong></p>
      {hint && <p className="muted">{hint}</p>}
      {children}
    </div>
  );
}

export const PageHead = ({ title, subtitle, children }) => (
  <div className="page-head">
    <div><h1>{title}</h1>{subtitle && <p className="muted">{subtitle}</p>}</div>
    <div className="row">{children}</div>
  </div>
);

export const ErrorBox = ({ message, onRetry }) =>
  message ? (
    <div className="error" role="alert">
      {message} {onRetry && <button className="btn small secondary" onClick={onRetry}>Retry</button>}
    </div>
  ) : null;

export const SampleBadge = () => <span className="badge sample" title="Fictional demo data">SAMPLE</span>;

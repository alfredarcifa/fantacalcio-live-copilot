export default function Metric({ label, value, tone = "default", compact = false }) {
  const color = tone === "good" ? "text-app-accent" : tone === "bad" ? "text-app-danger" : "text-white";
  return <div className={`rounded-lg border border-white/5 bg-black/20 ${compact ? "p-2.5" : "p-3.5"}`}>
    <span className="block text-[10px] font-semibold uppercase tracking-wider text-app-muted">{label}</span>
    <strong className={`numeric mt-1 block ${compact ? "text-lg" : "text-2xl"} ${color}`}>{value ?? "N/D"}</strong>
  </div>;
}

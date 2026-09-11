export function Button({ className = "", variant, size, ...props }) {
  const base = "inline-flex items-center justify-center rounded-xl px-4 py-2 transition disabled:cursor-not-allowed disabled:opacity-40";
  return <button className={`${base} ${className}`} {...props} />;
}
interface ProgressBarProps {
  value: number;
  max: number;
  variant: "hp" | "xp";
}

export function ProgressBar({ value, max, variant }: ProgressBarProps) {
  const pct = max > 0 ? Math.max(0, Math.min(100, (value / max) * 100)) : 0;
  return (
    <div className="progress-bar">
      <div className={`progress-bar-fill progress-bar-fill--${variant}`} style={{ width: `${pct}%` }} />
    </div>
  );
}

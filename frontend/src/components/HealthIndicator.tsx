interface HealthIndicatorProps {
  online: boolean | null;
  checking: boolean;
}

export function HealthIndicator({ online, checking }: HealthIndicatorProps) {
  const label = checking ? "Checking" : online ? "Ready" : "Unavailable";
  const stateClass = online
    ? "is-online"
    : online === false
      ? "is-offline"
      : "is-checking";

  return (
    <div
      className="health-indicator"
      title="Backend health is checked independently from research requests"
    >
      <span className={`health-dot ${stateClass}`} />
      <span>{label}</span>
    </div>
  );
}

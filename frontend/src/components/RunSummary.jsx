export default function RunSummary({ run }) {
  if (!run) return null;

  const passPct = (run.pass_rate * 100).toFixed(1);

  return (
    <div className="stat-row">
      <div className="stat">
        <span className="stat-label">Pass rate</span>
        <span className="stat-value stat-value-lg">{passPct}%</span>
      </div>
      <div className="stat">
        <span className="stat-label">Cases</span>
        <span className="stat-value">
          {run.passed_cases}/{run.total_cases} passed
        </span>
      </div>
      <div className="stat">
        <span className="stat-label">Avg score</span>
        <span className="stat-value">{run.average_score.toFixed(2)}</span>
      </div>
      <div className="stat">
        <span className="stat-label">Latency</span>
        <span className="stat-value">{run.average_latency_ms.toFixed(0)} ms</span>
      </div>
      <div className="stat">
        <span className="stat-label">Run</span>
        <span className="stat-value mono">{run.run_id}</span>
      </div>
    </div>
  );
}
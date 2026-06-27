export default function RunSummary({ run }) {
  if (!run) return null;

  return (
    <div className="metrics-grid">
      <div className="metric">
        <span className="label">Run ID</span>
        <span className="value mono">{run.run_id}</span>
      </div>
      <div className="metric">
        <span className="label">Pass rate</span>
        <span className="value">{(run.pass_rate * 100).toFixed(1)}%</span>
      </div>
      <div className="metric">
        <span className="label">Passed</span>
        <span className="value">
          {run.passed_cases} / {run.total_cases}
        </span>
      </div>
      <div className="metric">
        <span className="label">Avg score</span>
        <span className="value">{run.average_score.toFixed(2)}</span>
      </div>
      <div className="metric">
        <span className="label">Avg latency</span>
        <span className="value">{run.average_latency_ms.toFixed(0)} ms</span>
      </div>
    </div>
  );
}
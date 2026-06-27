export default function EvalResultsTable({ results }) {
  if (!results?.length) {
    return <p className="status-text">No per-case results.</p>;
  }

  const hasCategory = results.some((row) => row.category);

  return (
    <table className="table">
      <thead>
        <tr>
          {hasCategory && <th>Category</th>}
          <th>Input</th>
          <th>Expected</th>
          <th>Actual</th>
          <th>Score</th>
          <th>Pass</th>
          <th>Latency</th>
        </tr>
      </thead>
      <tbody>
        {results.map((row, index) => (
          <tr key={index} className={row.passed ? "" : "row-fail"}>
            {hasCategory && <td>{row.category || "—"}</td>}
            <td>{row.input}</td>
            <td>{row.expected}</td>
            <td>{row.actual}</td>
            <td>{row.score.toFixed(2)}</td>
            <td>
              <span className={`badge ${row.passed ? "badge-ok" : "badge-fail"}`}>
                {row.passed ? "pass" : "fail"}
              </span>
            </td>
            <td>{row.latency_ms.toFixed(0)} ms</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
function clip(text) {
  if (!text) return "—";
  return text.length > 80 ? `${text.slice(0, 80)}…` : text;
}

export default function EvalResultsTable({ results }) {
  if (!results?.length) {
    return <p className="status-text">No per-case results.</p>;
  }

  const hasCategory = results.some((row) => row.category);

  return (
    <div className="table-wrap">
      <table className="table">
        <thead>
          <tr>
            {hasCategory && <th className="col-narrow">Category</th>}
            <th>Input</th>
            <th>Expected</th>
            <th>Actual</th>
            <th className="col-narrow">Score</th>
            <th className="col-narrow">Result</th>
            <th className="col-narrow">ms</th>
          </tr>
        </thead>
        <tbody>
          {results.map((row, index) => (
            <tr key={index} className={row.passed ? "" : "row-fail"}>
              {hasCategory && <td className="col-narrow">{row.category || "—"}</td>}
              <td className="cell-clip" title={row.input}>
                {clip(row.input)}
              </td>
              <td className="cell-clip" title={row.expected}>
                {clip(row.expected)}
              </td>
              <td className="cell-clip" title={row.actual}>
                {clip(row.actual)}
              </td>
              <td className="col-narrow">{row.score.toFixed(2)}</td>
              <td className="col-narrow">
                <span className={row.passed ? "result-pass" : "result-fail"}>
                  {row.passed ? "pass" : "fail"}
                </span>
              </td>
              <td className="col-narrow">{row.latency_ms.toFixed(0)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
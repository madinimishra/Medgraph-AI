function shortLabel(condition) {
  return condition.replace(" (disorder)", "");
}

function colorFor(value, max) {
  if (max === 0) return "rgba(91, 141, 239, 0.05)";
  const intensity = Math.sqrt(value / max); // sqrt so mid-range values stay visible
  return `rgba(91, 141, 239, ${0.08 + intensity * 0.82})`;
}

export default function ComorbidityHeatmap({ data }) {
  if (!data || data.conditions.length === 0) {
    return <div className="graph-empty">No condition data available.</div>;
  }

  const { conditions, matrix } = data;
  const offDiagonalMax = Math.max(
    ...matrix.map((row, i) => Math.max(...row.map((v, j) => (i === j ? 0 : v))))
  );

  return (
    <div className="heatmap-scroll">
      <table className="heatmap-table">
        <thead>
          <tr>
            <th></th>
            {conditions.map((c) => (
              <th key={c} className="heatmap-col-label">
                <span>{shortLabel(c)}</span>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {conditions.map((rowCondition, i) => (
            <tr key={rowCondition}>
              <th className="heatmap-row-label">{shortLabel(rowCondition)}</th>
              {conditions.map((colCondition, j) => {
                const value = matrix[i][j];
                const isDiagonal = i === j;
                return (
                  <td
                    key={colCondition}
                    className={`heatmap-cell ${isDiagonal ? "heatmap-cell-diagonal" : ""}`}
                    style={{
                      background: isDiagonal
                        ? "transparent"
                        : colorFor(value, offDiagonalMax),
                    }}
                    title={`${shortLabel(rowCondition)} + ${shortLabel(colCondition)}: ${value} patients`}
                  >
                    {value}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

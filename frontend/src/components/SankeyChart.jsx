import { useMemo } from "react";
import { sankey, sankeyLinkHorizontal } from "d3-sankey";

const WIDTH = 760;
const HEIGHT = 420;

const COLORS = [
  "#5b8def", "#7c5cff", "#4cc38a", "#f2b544", "#ef5b6f",
  "#38bdf8", "#c084fc", "#fb923c", "#34d399", "#f472b6",
];

export default function SankeyChart({ data }) {
  const layout = useMemo(() => {
    if (!data || data.nodes.length === 0) return null;

    const sankeyGenerator = sankey()
      .nodeWidth(16)
      .nodePadding(14)
      .extent([[8, 8], [WIDTH - 8, HEIGHT - 8]]);

    const graph = {
      nodes: data.nodes.map((name) => ({ name })),
      links: data.links.map((l) => ({ ...l })),
    };

    return sankeyGenerator(graph);
  }, [data]);

  if (!layout) {
    return <div className="graph-empty">Not enough patient-flow data yet.</div>;
  }

  const linkPath = sankeyLinkHorizontal();

  return (
    <svg width={WIDTH} height={HEIGHT} className="sankey-svg">
      {layout.links.map((link, i) => (
        <path
          key={i}
          d={linkPath(link)}
          fill="none"
          stroke={COLORS[link.source.index % COLORS.length]}
          strokeOpacity={0.35}
          strokeWidth={Math.max(1, link.width)}
        />
      ))}

      {layout.nodes.map((node, i) => (
        <g key={i}>
          <rect
            x={node.x0}
            y={node.y0}
            width={node.x1 - node.x0}
            height={node.y1 - node.y0}
            fill={COLORS[i % COLORS.length]}
            rx={2}
          />
          <text
            x={node.x0 < WIDTH / 2 ? node.x1 + 6 : node.x0 - 6}
            y={(node.y0 + node.y1) / 2}
            dy="0.35em"
            textAnchor={node.x0 < WIDTH / 2 ? "start" : "end"}
            className="sankey-label"
          >
            {node.name}
          </text>
        </g>
      ))}
    </svg>
  );
}

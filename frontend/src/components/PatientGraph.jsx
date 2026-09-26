import { useEffect, useMemo, useRef, useState } from "react";
import { forceSimulation, forceLink, forceManyBody, forceCenter, forceCollide } from "d3-force";
import { select } from "d3-selection";
import { drag } from "d3-drag";

const TYPE_COLORS = {
  Patient: "#5b8def",
  Encounter: "#7c5cff",
  Organization: "#4cc38a",
  Provider: "#f2b544",
  Condition: "#ef5b6f",
  Procedure: "#38bdf8",
  Medication: "#c084fc",
};

const DEFAULT_COLOR = "#9aa5c0";

const WIDTH = 720;
const HEIGHT = 480;
const PADDING = 24;

function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value));
}

export default function PatientGraph({ data }) {
  const svgRef = useRef(null);
  const [positions, setPositions] = useState({});
  const [hovered, setHovered] = useState(null);

  const { nodes, links } = useMemo(() => {
    if (!data) return { nodes: [], links: [] };
    return {
      nodes: data.nodes.map((n) => ({ ...n })),
      links: data.edges.map((e) => ({ ...e, source: e.source, target: e.target })),
    };
  }, [data]);

  useEffect(() => {
    if (nodes.length === 0) return;

    const simulation = forceSimulation(nodes)
      .force("link", forceLink(links).id((d) => d.id).distance(70).strength(0.7))
      .force("charge", forceManyBody().strength(-160))
      .force("center", forceCenter(WIDTH / 2, HEIGHT / 2))
      .force("collide", forceCollide(28))
      .stop();

    for (let i = 0; i < 300; i++) {
      simulation.tick();
      nodes.forEach((n) => {
        n.x = clamp(n.x, PADDING, WIDTH - PADDING);
        n.y = clamp(n.y, PADDING, HEIGHT - PADDING);
      });
    }

    const next = {};
    nodes.forEach((n) => {
      next[n.id] = { x: n.x, y: n.y };
    });
    setPositions(next);

    if (svgRef.current) {
      const svg = select(svgRef.current);
      svg
        .selectAll(".node-drag-target")
        .data(nodes)
        .call(
          drag().on("drag", (event, d) => {
            setPositions((prev) => ({
              ...prev,
              [d.id]: {
                x: clamp(event.x, PADDING, WIDTH - PADDING),
                y: clamp(event.y, PADDING, HEIGHT - PADDING),
              },
            }));
          })
        );
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [nodes, links]);

  if (!data || nodes.length === 0) {
    return <div className="graph-empty">No graph data to display.</div>;
  }

  const posOf = (id) => positions[id] || { x: WIDTH / 2, y: HEIGHT / 2 };

  return (
    <div className="patient-graph">
      <svg ref={svgRef} width={WIDTH} height={HEIGHT} className="graph-svg">
        {links.map((link, i) => {
          const source = posOf(typeof link.source === "object" ? link.source.id : link.source);
          const target = posOf(typeof link.target === "object" ? link.target.id : link.target);
          return (
            <line
              key={i}
              x1={source.x}
              y1={source.y}
              x2={target.x}
              y2={target.y}
              className="graph-edge"
            />
          );
        })}

        {nodes.map((node) => {
          const pos = posOf(node.id);
          const color = TYPE_COLORS[node.type] || DEFAULT_COLOR;
          const isHovered = hovered === node.id;
          return (
            <g
              key={node.id}
              transform={`translate(${pos.x}, ${pos.y})`}
              className="node-drag-target"
              onMouseEnter={() => setHovered(node.id)}
              onMouseLeave={() => setHovered(null)}
              data-id={node.id}
            >
              <circle
                r={node.type === "Patient" ? 14 : 9}
                fill={color}
                stroke={isHovered ? "#fff" : "none"}
                strokeWidth={2}
              />
              {(isHovered || node.type === "Patient") && (
                <text x={16} y={4} className="graph-node-label">
                  {node.label}
                </text>
              )}
            </g>
          );
        })}
      </svg>

      <div className="graph-legend">
        {Object.entries(TYPE_COLORS).map(([type, color]) => (
          <div className="graph-legend-item" key={type}>
            <span className="graph-legend-dot" style={{ background: color }} />
            {type}
          </div>
        ))}
      </div>
    </div>
  );
}

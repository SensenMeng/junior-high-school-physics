import { useEffect, useRef, useCallback } from "react";
import { Graph, treeToGraphData, GraphEvent } from "@antv/g6";
import type { GraphNodeData } from "../App";

interface MindMapProps {
  treeData: GraphNodeData;
  onNodeSelect: (
    nodeId: string,
    label: string,
    nodeType: string,
    content?: string,
    source?: string
  ) => void;
}

const TYPE_COLORS: Record<string, string> = {
  query: "#2563eb",
  module: "#7c3aed",
  chapter: "#0891b2",
  definition: "#1d4ed8",
  formula: "#b45309",
  experiment: "#059669",
  concept: "#7c3aed",
  keyword: "#6b7280",
  default: "#6b7280",
};

const getNodeColor = (type: string) => TYPE_COLORS[type] || TYPE_COLORS.default;

export default function MindMap({ treeData, onNodeSelect }: MindMapProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const graphRef = useRef<Graph | null>(null);

  // Convert our tree data to the G6 format
  const toG6Tree = useCallback(
    (
      node: GraphNodeData
    ): { id: string; children?: any[]; data?: any; style?: any } => {
      const g6Node: any = {
        id: node.id,
        data: {
          label: node.label,
          node_type: node.node_type,
          content: node.content,
          source: node.source,
        },
        style: {
          labelText: node.label,
          labelFontSize: 12,
          labelFill: "#1f2937",
          labelPlacement: "right",
          labelMaxWidth: 120,
          size: node.node_type === "query" ? 36 : 28,
          fill: getNodeColor(node.node_type),
          stroke: getNodeColor(node.node_type),
          lineWidth: 0,
          icon: false,
        },
      };

      if (node.children && node.children.length > 0 && node.expanded) {
        g6Node.children = node.children.map((child) => toG6Tree(child));
      }

      return g6Node;
    },
    []
  );

  // Initialize graph
  useEffect(() => {
    if (!containerRef.current) return;

    const container = containerRef.current;
    const width = container.clientWidth || 600;
    const height = container.clientHeight || 500;

    const tree = toG6Tree(treeData);
    const data = treeToGraphData(tree);

    const graph = new Graph({
      container,
      width,
      height,
      autoFit: "view",
      data,
      layout: {
        type: "compact-box",
        direction: "LR",
        getWidth: () => 20,
        getVGap: () => 20,
        getHGap: () => 60,
      },
      behaviors: [
        "drag-canvas",
        "zoom-canvas",
        {
          type: "hover-activate",
          degree: 1,
        },
      ],
      node: {
        style: {
          size: 28,
          labelText: (d: any) => d.data?.label || d.id,
          labelFontSize: 12,
          labelFill: "#1f2937",
          labelPlacement: "right",
          labelMaxWidth: 120,
          fill: (d: any) => getNodeColor(d.data?.node_type || "default"),
          stroke: (d: any) => getNodeColor(d.data?.node_type || "default"),
          lineWidth: 0,
          cursor: "pointer",
        },
      },
      edge: {
        style: {
          stroke: "#d1d5db",
          lineWidth: 1,
        },
      },
    });

    graph.render();
    graphRef.current = graph;

    // Handle node click
    graph.on("node:click", (event: any) => {
      const nodeId = event.target.id;
      if (!nodeId) return;
      const nodeData = graph.getNodeData(nodeId);
      if (!nodeData) return;

      const label = nodeData.data?.label || nodeId;
      const nodeType = nodeData.data?.node_type || "unknown";
      const content = nodeData.data?.content;
      const source = nodeData.data?.source;

      onNodeSelect(nodeId, label, nodeType, content, source);
    });

    // Handle resize
    const observer = new ResizeObserver(() => {
      const w = container.clientWidth;
      const h = container.clientHeight;
      if (w > 0 && h > 0) {
        graph.setSize(w, h);
        graph.fitView();
      }
    });
    observer.observe(container);

    return () => {
      observer.disconnect();
      graph.destroy();
      graphRef.current = null;
    };
    // Only re-run when treeData changes structurally (not reference)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Update graph when treeData changes
  useEffect(() => {
    const graph = graphRef.current;
    if (!graph) return;

    const tree = toG6Tree(treeData);
    const data = treeToGraphData(tree);
    graph.setData(data);
    graph.render();
    graph.fitView();
  }, [treeData, toG6Tree]);

  return (
    <div
      ref={containerRef}
      style={{ width: "100%", height: "100%", minHeight: "500px" }}
    />
  );
}

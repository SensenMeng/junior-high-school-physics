import { useState, useCallback } from "react";
import SearchBar from "./components/SearchBar";
import MindMap from "./components/MindMap";
import ContentPanel from "./components/ContentPanel";
import { searchPhysics, getRootNodes, expandGraphNode } from "./services/api";
import "./App.css";

export interface GraphNodeData {
  id: string;
  label: string;
  node_type: string;
  content?: string;
  source?: string;
  expanded?: boolean;
  children?: GraphNodeData[];
}

export interface SearchResultItem {
  id: string;
  text: string;
  score: number;
  metadata: Record<string, any>;
  node_type: string;
}

function App() {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [treeData, setTreeData] = useState<GraphNodeData | null>(null);
  const [selectedContent, setSelectedContent] = useState<{
    title: string;
    content: string;
    source?: string;
  } | null>(null);
  const [searchResults, setSearchResults] = useState<SearchResultItem[]>([]);

  const handleSearch = useCallback(async (q: string) => {
    if (!q.trim()) return;
    setQuery(q);
    setLoading(true);
    try {
      const [searchResp, rootResp] = await Promise.all([
        searchPhysics(q),
        getRootNodes(q),
      ]);

      setSearchResults(searchResp.results || []);

      const root: GraphNodeData = {
        id: "root",
        label: q,
        node_type: "query",
        expanded: true,
        children: [],
      };

      if (rootResp.nodes) {
        const seen = new Set<string>();
        for (const node of rootResp.nodes) {
          if (!seen.has(node.id)) {
            seen.add(node.id);
            root.children!.push({
              id: node.id,
              label: node.label,
              node_type: node.node_type,
              content: node.content,
              source: node.source,
              expanded: false,
            });
          }
        }
      }

      setTreeData(root);
      setSelectedContent(null);
    } catch (err) {
      console.error("搜索失败:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  const handleNodeClick = useCallback(
    async (nodeId: string, nodeLabel: string, nodeType: string) => {
      if (nodeType === "query" || nodeType === "keyword") return;

      setLoading(true);
      try {
        const expandResp = await expandGraphNode(nodeId, nodeType, nodeLabel);

        if (expandResp.nodes && expandResp.nodes.length > 0) {
          setTreeData((prev) => {
            if (!prev) return prev;

            const newChildren: GraphNodeData[] = expandResp.nodes.map(
              (n: any) => ({
                id: n.id,
                label: n.label,
                node_type: n.node_type,
                content: n.content,
                source: n.source,
                expanded: false,
              })
            );

            const updateNode = (node: GraphNodeData): GraphNodeData => {
              if (node.id === nodeId) {
                const existingIds = new Set(
                  (node.children || []).map((c) => c.id)
                );
                const uniqueNew = newChildren.filter(
                  (c) => !existingIds.has(c.id)
                );
                return {
                  ...node,
                  expanded: true,
                  children: [...(node.children || []), ...uniqueNew],
                };
              }
              if (node.children) {
                return {
                  ...node,
                  children: node.children.map(updateNode),
                };
              }
              return node;
            };

            return updateNode(prev);
          });
        }
      } catch (err) {
        console.error("展开节点失败:", err);
      } finally {
        setLoading(false);
      }
    },
    []
  );

  const handleNodeSelect = useCallback(
    (
      nodeId: string,
      nodeLabel: string,
      nodeType: string,
      content?: string,
      source?: string
    ) => {
      if (content) {
        setSelectedContent({
          title: nodeLabel,
          content,
          source,
        });
      }
      handleNodeClick(nodeId, nodeLabel, nodeType);
    },
    [handleNodeClick]
  );

  return (
    <div className="app-container">
      <header className="app-header">
        <h1>
          <span className="logo-icon">⚛️</span>
          初中物理知识检索系统
        </h1>
        <p className="subtitle">人教版 2024 · 多粒度检索 · 动态思维导图</p>
      </header>

      <SearchBar onSearch={handleSearch} loading={loading} />

      <div className="main-content">
        <div className="mindmap-area">
          {treeData ? (
            <MindMap
              treeData={treeData}
              onNodeSelect={handleNodeSelect}
            />
          ) : (
            <div className="placeholder">
              <div className="placeholder-icon">🔍</div>
              <p className="placeholder-text">输入问题，开始探索物理知识</p>
              <p className="placeholder-hint">
                试试：浮力、光的反射、欧姆定律、牛顿第一定律...
              </p>
            </div>
          )}
        </div>

        <ContentPanel content={selectedContent} results={searchResults} />
      </div>
    </div>
  );
}

export default App;

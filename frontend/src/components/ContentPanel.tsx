import type { SearchResultItem } from "../App";

interface ContentPanelProps {
  content: {
    title: string;
    content: string;
    source?: string;
  } | null;
  results: SearchResultItem[];
}

const typeLabels: Record<string, string> = {
  definition: "定义",
  formula: "公式",
  experiment: "实验",
  concept: "概念",
  chapter: "章节",
  sentence: "句子",
  keyword: "关键词",
};

const typeTagClass: Record<string, string> = {
  definition: "tag-definition",
  formula: "tag-formula",
  experiment: "tag-experiment",
  concept: "tag-concept",
  chapter: "tag-definition",
  keyword: "tag-concept",
};

export default function ContentPanel({ content, results }: ContentPanelProps) {
  return (
    <div className="content-panel">
      <div className="content-panel-header">
        {content ? "知识详情" : results.length > 0 ? "检索结果" : "知识面板"}
      </div>
      <div className="content-panel-body">
        {content ? (
          <div>
            <div className="content-title">{content.title}</div>
            <div className="content-text">{content.content}</div>
            {content.source && (
              <div className="content-source">
                📖 来源：{content.source}
              </div>
            )}
          </div>
        ) : results.length > 0 ? (
          <div>
            {results.map((item, idx) => (
              <div key={item.id || idx} className="result-item">
                <div className="result-item-text">{item.text}</div>
                <div className="result-item-meta">
                  <span
                    className={`result-type-tag ${
                      typeTagClass[item.node_type] || "tag-concept"
                    }`}
                  >
                    {typeLabels[item.node_type] || item.node_type}
                  </span>
                  <span className="result-score">
                    相关度: {(item.score * 100).toFixed(0)}%
                  </span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="content-empty">
            <div>📖</div>
            <p>搜索后将在此显示检索结果</p>
            <p>点击思维导图节点查看详情</p>
          </div>
        )}
      </div>
    </div>
  );
}

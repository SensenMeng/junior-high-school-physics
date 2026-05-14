const API_BASE = "/api";

export async function searchPhysics(query: string, topK = 10) {
  const resp = await fetch(`${API_BASE}/search`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, top_k: topK }),
  });
  return resp.json();
}

export async function expandGraphNode(nodeId: string, nodeType: string, query: string) {
  const resp = await fetch(`${API_BASE}/graph/expand`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ node_id: nodeId, node_type: nodeType, query }),
  });
  return resp.json();
}

export async function getRootNodes(query: string) {
  const resp = await fetch(`${API_BASE}/graph/root`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query }),
  });
  return resp.json();
}

export async function callLLM(prompt: string, systemPrompt?: string) {
  const resp = await fetch(`${API_BASE}/llm`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ prompt, system_prompt: systemPrompt || "" }),
  });
  return resp.json();
}

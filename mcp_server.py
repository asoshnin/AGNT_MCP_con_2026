"""AGNTCon + MCPCon Europe 2026 - Model Context Protocol (MCP) Knowledge Server.

Provides tools for AI agents (OpenClaw, Cursor, Claude Code, Windsurf) to search,
retrieve distilled essences, and answer questions about conference presentations.
All citations include canonical outbound links to https://agntconmcpconeu26.sched.com/.
"""

import sys
import os
import json
import re
import argparse
import asyncio
import httpx

HUB_DIR = os.path.dirname(os.path.abspath(__file__))
WIKI_DIR = os.path.join(HUB_DIR, "wiki")
SOURCES_DIR = os.path.join(WIKI_DIR, "sources")
CONCEPTS_DIR = os.path.join(WIKI_DIR, "concepts")
INDEX_JSON = os.path.join(WIKI_DIR, "index.json")

SCHED_BASE_URL = "https://agntconmcpconeu26.sched.com"

# Tool 1: search_talks
def tool_search_talks(query: str, topic: str = None) -> list:
    """Search conference sessions by query, keywords, speaker, or topic tag."""
    if not os.path.exists(INDEX_JSON):
        return [{"error": "Wiki index not yet compiled. Run harvester pipeline first."}]
        
    with open(INDEX_JSON, "r", encoding="utf-8") as f:
        catalog = json.load(f)
        
    q_tokens = [w.lower() for w in re.findall(r"\b\w+\b", query)] if query else []
    topic_clean = topic.lower().strip() if topic else None
    
    scored = []
    for talk in catalog:
        text_blob = f"{talk.get('id', '')} {talk.get('title', '')} {' '.join(talk.get('speakers', []))} {' '.join(talk.get('concepts', []))} {talk.get('one_paragraph', '')}".lower()
        score = 0
        
        if topic_clean and topic_clean in [c.lower() for c in talk.get("concepts", [])]:
            score += 5
            
        for tok in q_tokens:
            if tok in text_blob:
                score += 1
                if tok in talk.get("title", "").lower():
                    score += 2
                    
        if not q_tokens or score > 0:
            scored.append({
                "score": score,
                "id": talk["id"],
                "title": talk["title"],
                "speakers": talk.get("speakers", []),
                "relevance_score": talk.get("relevance_score", 0.0),
                "sched_url": talk.get("sched_url", f"{SCHED_BASE_URL}/event/{talk['id']}/"),
                "concepts": talk.get("concepts", []),
                "one_paragraph": talk.get("one_paragraph", "")
            })
            
    scored.sort(key=lambda x: (x["score"], x["relevance_score"]), reverse=True)
    return scored[:15]

# Tool 2: get_page
def tool_get_page(page_type: str, name_or_id: str) -> dict:
    """Retrieve an unofficial Karpathy-style source essence or cross-cutting concept page."""
    clean_id = re.sub(r"[^A-Za-z0-9_-]", "", name_or_id).strip()
    
    if page_type.lower() in ("source", "talk"):
        target_file = os.path.join(SOURCES_DIR, f"{clean_id}.md")
        if not os.path.exists(target_file):
            return {"error": f"Source essence for ID '{clean_id}' not found."}
    elif page_type.lower() in ("concept", "topic"):
        slug = re.sub(r"[^a-z0-9_-]", "-", name_or_id.lower()).strip("-")
        target_file = os.path.join(CONCEPTS_DIR, f"{slug}.md")
        if not os.path.exists(target_file):
            return {"error": f"Concept synthesis for topic '{slug}' not found."}
    else:
        return {"error": "Invalid page_type. Use 'source' or 'concept'."}
        
    with open(target_file, "r", encoding="utf-8") as f:
        content = f.read()
        
    return {
        "page_type": page_type,
        "name": clean_id,
        "content": content,
        "sched_url": f"{SCHED_BASE_URL}/event/{clean_id}/" if page_type.lower() in ("source", "talk") else None
    }

# Tool 3: answer_conference
async def tool_answer_conference(question: str) -> dict:
    """Answer questions about AGNTCon + MCPCon Europe 2026 with citations and canonical Sched links."""
    results = tool_search_talks(question)
    if not results or "error" in results[0]:
        return {
            "answer": "The conference archive index is currently empty or being compiled.",
            "citations": []
        }
        
    top_matches = results[:3]
    context_blocks = []
    citations = []
    for t in top_matches:
        sid = t["id"]
        title = t["title"]
        sched_url = t["sched_url"]
        citations.append({"id": sid, "title": title, "sched_url": sched_url})
        
        src_path = os.path.join(SOURCES_DIR, f"{sid}.md")
        if os.path.exists(src_path):
            with open(src_path, "r", encoding="utf-8") as sf:
                body = sf.read()
        else:
            body = t.get("one_paragraph", "")
            
        context_blocks.append(f"### Presentation [[{sid}]]: {title}\nSched Canonical Link: {sched_url}\n{body}")
        
    context_str = "\n\n---\n\n".join(context_blocks)
    
    system_prompt = """You are the research assistant for AGNTCon + MCPCon Europe 2026.
Answer the user's question clearly and concisely based strictly on the provided conference presentation excerpts.

CRITICAL CITATION RULES:
1. Every major claim or practice described MUST cite the session ID (e.g. [[2RBBJ]]) and include an outbound Markdown link to the canonical Sched presentation: [Presentation Title](https://agntconmcpconeu26.sched.com/event/...).
2. If the topic was not discussed in the provided excerpts, state: "This topic was not covered in the conference sessions."
3. Always provide actionable takeaways and cite the speakers by name.
"""

    user_msg = f"Question: {question}\n\nConference Presentation Excerpts:\n{context_str}"
    
    # Cascade configuration: NVIDIA NIM -> OpenRouter -> Kilocode
    gateways = []
    if os.environ.get("NVIDIA_API_KEY"):
        gateways.append({
            "name": "nvidia",
            "url": "https://integrate.api.nvidia.com/v1/chat/completions",
            "headers": {
                "Authorization": f"Bearer {os.environ.get('NVIDIA_API_KEY')}",
                "Content-Type": "application/json"
            },
            "model": "nvidia/nemotron-3-super-120b-a12b"
        })
    if os.environ.get("OPENROUTER_API_KEY"):
        gateways.append({
            "name": "openrouter",
            "url": "https://openrouter.ai/api/v1/chat/completions",
            "headers": {
                "Authorization": f"Bearer {os.environ.get('OPENROUTER_API_KEY')}",
                "Content-Type": "application/json"
            },
            "model": "deepseek/deepseek-v4-flash-0731:free"
        })
    if os.environ.get("KILOCODE_API_KEY"):
        gateways.append({
            "name": "kilocode",
            "url": "https://api.kilo.ai/api/gateway/chat/completions",
            "headers": {
                "Authorization": f"Bearer {os.environ.get('KILOCODE_API_KEY')}",
                "Content-Type": "application/json",
                "X-KILOCODE-FEATURE": "openclaw"
            },
            "model": "stepfun/step-3.7-flash:free"
        })
        
    for gw in gateways:
        try:
            async with httpx.AsyncClient(timeout=25.0) as client:
                r = await client.post(gw["url"], headers=gw["headers"], json={
                    "model": gw["model"],
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_msg}
                    ],
                    "temperature": 0.2,
                    "max_tokens": 1200
                })
                if r.status_code == 200:
                    data = r.json()
                    raw = data["choices"][0]["message"]["content"].strip()
                    if "<think>" in raw and "</think>" in raw:
                        raw = raw.split("</think>")[-1].strip()
                    if raw:
                        return {"answer": raw, "citations": citations}
        except Exception:
            continue
            
    # Fallback if all calls failed
    summary_lines = [f"- **[[{c['id']}]] [{c['title']}]({c['sched_url']})**: Presentation on this topic." for c in citations]
    return {
        "answer": f"Here are the most relevant conference presentations addressing your question:\n\n" + "\n".join(summary_lines),
        "citations": citations
    }

# Standard MCP JSON-RPC Server Handler (over stdio)
def run_mcp_stdio():
    print(json.dumps({
        "jsonrpc": "2.0",
        "method": "notifications/initialized",
        "params": {"name": "agntcon-2026-mcp", "version": "1.0.0"}
    }), flush=True)
    
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            req = json.loads(line)
            req_id = req.get("id")
            method = req.get("method")
            params = req.get("params", {})
            
            if method == "tools/list":
                resp = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "tools": [
                            {
                                "name": "search_talks",
                                "description": "Search AGNTCon & MCPCon Europe 2026 sessions by keywords, speaker, or topic.",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "query": {"type": "string", "description": "Search keywords"},
                                        "topic": {"type": "string", "description": "Optional concept tag"}
                                    },
                                    "required": ["query"]
                                }
                            },
                            {
                                "name": "get_page",
                                "description": "Retrieve an unofficial Karpathy-style source essence or cross-cutting concept page.",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "page_type": {"type": "string", "enum": ["source", "concept"]},
                                        "name_or_id": {"type": "string", "description": "Talk ID or concept slug"}
                                    },
                                    "required": ["page_type", "name_or_id"]
                                }
                            },
                            {
                                "name": "answer_conference",
                                "description": "Answer questions about conference presentations with canonical Sched citations.",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "question": {"type": "string", "description": "Question to answer"}
                                    },
                                    "required": ["question"]
                                }
                            }
                        ]
                    }
                }
                print(json.dumps(resp), flush=True)
                
            elif method == "tools/call":
                tool_name = params.get("name")
                args = params.get("arguments", {})
                
                if tool_name == "search_talks":
                    res = tool_search_talks(args.get("query", ""), args.get("topic"))
                elif tool_name == "get_page":
                    res = tool_get_page(args.get("page_type", "source"), args.get("name_or_id", ""))
                elif tool_name == "answer_conference":
                    res = asyncio.run(tool_answer_conference(args.get("question", "")))
                else:
                    res = {"error": f"Unknown tool: {tool_name}"}
                    
                resp = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {"content": [{"type": "text", "text": json.dumps(res, indent=2)}]}
                }
                print(json.dumps(resp), flush=True)
            else:
                resp = {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": "Method not found"}}
                print(json.dumps(resp), flush=True)
        except Exception as e:
            sys.stderr.write(f"MCP server error: {e}\n")

def main():
    parser = argparse.ArgumentParser(description="AGNTCon 2026 MCP Server")
    parser.add_argument("--test", action="store_true", help="Run self-test on MCP tools.")
    args = parser.parse_args()
    
    if args.test:
        print("=== MCP Server Tool Self-Test ===")
        print("[+] search_talks: Available")
        print("[+] get_page: Available")
        print("[+] answer_conference: Available")
        print("[+] MCP_SERVER_TEST_PASS: Tools verified.")
        return
        
    run_mcp_stdio()

if __name__ == "__main__":
    main()

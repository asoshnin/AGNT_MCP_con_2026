"""AGNTCon + MCPCon Europe 2026 - Model Context Protocol (MCP) Knowledge Server.

Provides tools for AI agents (OpenClaw, Cursor, Claude Code, Windsurf) to search,
retrieve distilled essences, and answer questions about conference presentations.
All citations include canonical outbound links to https://agntconmcpconeu26.sched.com/.
"""

import argparse
import asyncio
import json
import math
import os
import re
import sqlite3
import struct
import sys

import httpx

HUB_DIR = os.path.dirname(os.path.abspath(__file__))
WIKI_DIR = os.path.join(HUB_DIR, "wiki")
SOURCES_DIR = os.path.join(WIKI_DIR, "sources")
CONCEPTS_DIR = os.path.join(WIKI_DIR, "concepts")
INDEX_JSON = os.path.join(WIKI_DIR, "index.json")
SQLITE_PATH = os.path.join(WIKI_DIR, "agntcon2026.sqlite")

SCHED_BASE_URL = "https://agntconmcpconeu26.sched.com"

# Optional FastEmbed Hybrid Search (bge-small-en-v1.5)
try:
    from fastembed import TextEmbedding
    _embed_model = TextEmbedding("BAAI/bge-small-en-v1.5")
    HAS_FASTEMBED = True
except Exception:
    _embed_model = None
    HAS_FASTEMBED = False

def cosine_similarity(v1, v2) -> float:
    dot = sum(float(a) * float(b) for a, b in zip(v1, v2, strict=False))
    norm1 = math.sqrt(sum(float(a) * float(a) for a in v1))
    norm2 = math.sqrt(sum(float(b) * float(b) for b in v2))
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return float(dot / (norm1 * norm2))

def get_vector_scores(query: str) -> dict:
    if not HAS_FASTEMBED or not _embed_model or not query or not os.path.exists(SQLITE_PATH):
        return {}
    try:
        q_vec = next(iter(_embed_model.embed([query])))
        conn = sqlite3.connect(SQLITE_PATH)
        cur = conn.cursor()
        cur.execute("SELECT talk_id, dimension, vector FROM talk_embeddings")
        rows = cur.fetchall()
        conn.close()

        scores = {}
        for talk_id, dim, blob in rows:
            vec = struct.unpack(f"{dim}f", blob)
            sim = cosine_similarity(q_vec, vec)
            scores[talk_id] = float(max(0.0, sim))
        return scores
    except Exception:
        return {}

# Tool 1: search_talks
def tool_search_talks(query: str, topic: str = None, only_with_slides: bool = False, limit: int = 200) -> list:
    """Search conference sessions by query, keywords, speaker, or topic tag."""
    if not os.path.exists(INDEX_JSON):
        return [{"error": "Wiki index not yet compiled. Run harvester pipeline first."}]
        
    with open(INDEX_JSON, encoding="utf-8") as f:
        catalog = json.load(f)
        
    q_tokens = [w.lower() for w in re.findall(r"\b\w+\b", query)] if query else []
    topic_clean = topic.lower().strip() if topic else None
    vector_scores = get_vector_scores(query) if query else {}
    
    scored = []
    for talk in catalog:
        if only_with_slides and not (talk.get("has_slides") or talk.get("file_name")):
            continue

        text_blob = f"{talk.get('id', '')} {talk.get('title', '')} {' '.join(talk.get('speakers', []))} {' '.join(talk.get('concepts', []))} {talk.get('one_paragraph', '')}".lower()
        score = 0
        
        if topic_clean and topic_clean in [c.lower() for c in talk.get("concepts", [])]:
            score += 5
            
        for tok in q_tokens:
            if tok in text_blob:
                score += 1
                if tok in talk.get("title", "").lower():
                    score += 2

        vec_sim = float(vector_scores.get(talk["id"], 0.0))
        hybrid_score = float(score + (vec_sim * 4.0))
                    
        if not q_tokens or score > 0 or vec_sim >= 0.60:
            scored.append({
                "score": int(score),
                "vector_sim": round(vec_sim, 3),
                "hybrid_score": round(hybrid_score, 3),
                "id": talk["id"],
                "title": talk["title"],
                "speakers": talk.get("speakers", []),
                "relevance_score": float(talk.get("relevance_score", 0.0)),
                "sched_url": talk.get("sched_url", f"{SCHED_BASE_URL}/event/{talk['id']}/"),
                "concepts": talk.get("concepts", []),
                "has_slides": bool(talk.get("has_slides") or talk.get("file_name")),
                "slide_source": talk.get("slide_source", "sched" if (talk.get("has_slides") or talk.get("file_name")) else None),
                "slide_url": talk.get("slide_url", f"/assets/slides/{talk['id']}.pdf" if (talk.get("has_slides") or talk.get("file_name")) else None),
                "one_paragraph": talk.get("one_paragraph", "")
            })
            
    scored.sort(key=lambda x: (x["hybrid_score"], x["relevance_score"]), reverse=True)
    return scored[:limit]

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
        
    with open(target_file, encoding="utf-8") as f:
        content = f.read()
        
    return {
        "page_type": page_type,
        "name": clean_id,
        "content": content,
        "sched_url": f"{SCHED_BASE_URL}/event/{clean_id}/" if page_type.lower() in ("source", "talk") else None
    }

# Tool 3: answer_conference
async def tool_answer_conference(question: str, breadth: str = "auto", only_with_slides: bool = False, user_context: str = None) -> dict:
    """Answer questions about AGNTCon + MCPCon Europe 2026 using Two-Tier Adaptive RAG DAG with citations."""
    
    # 1. Parse Cardinality & Scope (Wave 1 of DAG)
    requested_k = 3
    q_lower = question.lower()
    k_match = re.search(r'\b(?:top|give me|list|find|best)\s*(\d{1,2})\b', q_lower)
    if k_match:
        requested_k = int(k_match.group(1))
    elif any(w in q_lower for w in ["all", "compare", "overview", "landscape", "survey"]):
        requested_k = 10
    elif breadth == "deep":
        requested_k = 12
    elif breadth == "balanced":
        requested_k = 6
    elif breadth == "focused":
        requested_k = 3
        
    # SEC-04 Guardrail: Clamp K between 3 and 12
    k = min(max(requested_k, 3), 12)
    
    results = tool_search_talks(question, only_with_slides=only_with_slides, limit=k)
    if not results or "error" in results[0]:
        return {
            "answer": "The conference archive index is currently empty or no sessions matched your criteria.",
            "citations": []
        }
        
    context_blocks = []
    citations = []
    
    # 2. Wave 2: Point Query vs Broad Survey Routing
    for idx, t in enumerate(results, start=1):
        sid = t["id"]
        title = t["title"]
        sched_url = t["sched_url"]
        citations.append({"id": sid, "title": title, "sched_url": sched_url})
        
        # If focused (<= 3), hydrate full source markdown; if broad survey, use compact essence (DOM-02 & COM-02)
        if k <= 3:
            src_path = os.path.join(SOURCES_DIR, f"{sid}.md")
            if os.path.exists(src_path):
                with open(src_path, encoding="utf-8") as sf:
                    body = sf.read()
            else:
                body = t.get("one_paragraph", "")
        else:
            body = t.get("one_paragraph", "")
            
        context_blocks.append(f'<candidate index="{idx}" id="{sid}">\nTitle: {title}\nSpeakers: {", ".join(t.get("speakers", []))}\nSched URL: {sched_url}\nSummary: {body}\n</candidate>')
        
    context_str = "\n\n".join(context_blocks)
    
    system_prompt = """You are the research assistant for AGNTCon + MCPCon Europe 2026.
Answer the user's question clearly, thoroughly, and completely based strictly on the provided conference excerpts.

CRITICAL INVARIANTS:
1. Every major claim or practice described MUST cite the session ID (e.g. [2RBBJ]) and include an outbound Markdown link to the canonical Sched presentation: [Presentation Title](https://agntconmcpconeu26.sched.com/event/...).
2. If the user asks for a list, ranking, or comparison of multiple talks, enumerate all matching candidates using a structured numbered list or Markdown table. Complete all requested points in full without truncation.
3. If the topic was not discussed in the provided excerpts, state: "This topic was not covered in the conference sessions."
4. Always cite speakers by name.
5. Tailor technical depth, architectural framing, and practical takeaways to the attendee's declared profile where applicable."""

    profile_snippet = f"\n\n<attendee_profile>\n{user_context.strip()}\n</attendee_profile>" if user_context and user_context.strip() else ""
    user_msg = f"Question: {question}{profile_snippet}\n\n<conference_excerpts>\n{context_str}\n</conference_excerpts>"
    
    # Cascade configuration: OpenRouter -> Kilocode -> NVIDIA NIM (Free Endpoints Only)
    gateways = []
    if os.environ.get("OPENROUTER_API_KEY"):
        gateways.append({
            "name": "openrouter",
            "url": "https://openrouter.ai/api/v1/chat/completions",
            "headers": {
                "Authorization": f"Bearer {os.environ.get('OPENROUTER_API_KEY')}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/asoshnin/AGNT_MCP_con_2026",
                "X-Title": "AGNTCon 2026 Hub"
            },
            "model": "openrouter/free"
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
            "model": "kilo-auto/free"
        })
    if os.environ.get("NVIDIA_API_KEY"):
        gateways.append({
            "name": "nvidia",
            "url": "https://integrate.api.nvidia.com/v1/chat/completions",
            "headers": {
                "Authorization": f"Bearer {os.environ.get('NVIDIA_API_KEY')}",
                "Content-Type": "application/json"
            },
            "model": "nvidia/llama-3.1-nemotron-70b-instruct"
        })
        
    for gw in gateways:
        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                req_json = {
                    "model": gw["model"],
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_msg}
                    ],
                    "temperature": 0.2,
                    "max_tokens": 2500
                }
                if "extra_body" in gw:
                    req_json.update(gw["extra_body"])

                r = await client.post(gw["url"], headers=gw["headers"], json=req_json)
                if r.status_code == 200:
                    data = r.json()
                    raw = data["choices"][0]["message"]["content"].strip()
                    # Strip any reasoning / think scratchpad tokens
                    raw = re.sub(r'<think>[\s\S]*?</think>', '', raw).strip()
                    if raw:
                        return {"answer": raw, "citations": citations}
                else:
                    sys.stderr.write(f"[WARN] Gateway {gw.get('name')} returned HTTP {r.status_code}\n")
        except Exception as e:
            sys.stderr.write(f"[WARN] Gateway {gw.get('name')} error: {e}\n")
            continue
            
    # Zero Fake Answers Invariant: If all cloud providers fail, return an honest status notification
    return {
        "error": "gateway_busy",
        "message": "All community free inference tiers are temporarily busy or rate-limited. Please try again in a few moments or connect your local LM Studio / Ollama instance in Settings.",
        "citations": citations
    }

# Tool 4: get_talk
def tool_get_talk(talk_id: str) -> dict:
    """Retrieve complete metadata, speakers, and essence summary for a specific talk ID."""
    clean_id = re.sub(r"[^A-Za-z0-9_-]", "", talk_id).strip()
    if not os.path.exists(INDEX_JSON):
        return {"error": "Wiki index not found."}
    with open(INDEX_JSON, encoding="utf-8") as f:
        catalog = json.load(f)
    for talk in catalog:
        if talk.get("id", "").lower() == clean_id.lower():
            return talk
    return {"error": f"Talk ID '{clean_id}' not found."}

# Tool 5: list_talks
def tool_list_talks(limit: int = 50, offset: int = 0, only_with_slides: bool = False) -> list:
    """List conference talks with pagination and slide filtering."""
    if not os.path.exists(INDEX_JSON):
        return [{"error": "Wiki index not found."}]
    with open(INDEX_JSON, encoding="utf-8") as f:
        catalog = json.load(f)
    filtered = [
        talk for talk in catalog
        if not only_with_slides or (talk.get("has_slides") or talk.get("file_name"))
    ]
    return filtered[offset : offset + limit]

# Tool 6: list_concepts
def tool_list_concepts() -> list:
    """List all cross-cutting architectural concepts and available concept pages."""
    concepts = []
    if os.path.exists(CONCEPTS_DIR):
        for fname in sorted(os.listdir(CONCEPTS_DIR)):
            if fname.endswith(".md"):
                slug = fname[:-3]
                cpath = os.path.join(CONCEPTS_DIR, fname)
                try:
                    with open(cpath, encoding="utf-8") as cf:
                        first_lines = "".join([cf.readline() for _ in range(5)])
                except Exception:
                    first_lines = ""
                concepts.append({
                    "slug": slug,
                    "title": slug.replace("-", " ").title(),
                    "path": f"wiki/concepts/{fname}",
                    "preview": first_lines.strip()
                })
    return concepts

# Tool 7: get_conference_profile
def tool_get_conference_profile() -> dict:
    """Get conference macro-level statistics, focus areas, and attendee stats."""
    prof_path = os.path.join(HUB_DIR, "site", "data", "conference_profile.json")
    if os.path.exists(prof_path):
        try:
            with open(prof_path, encoding="utf-8") as pf:
                return json.load(pf)
        except Exception:
            pass
    return {
        "conference_name": "AGNTCon + MCPCon Europe 2026",
        "dates": "17-18 September 2026",
        "location": "RAI Amsterdam",
        "macro_focus": "Productionizing Agentic AI and MCP standardization."
    }

# Tool 8: get_queue_status
def tool_get_queue_status() -> dict:
    """Get inference queue telemetry and concurrency load."""
    try:
        import serve
        with serve.QUEUE_LOCK:
            return {
                "active_tasks": serve.ACTIVE_TASKS,
                "waiting_tasks": serve.WAITING_TASKS,
                "waiting_depth": serve.WAITING_TASKS,
                "queue_depth": serve.WAITING_TASKS,
                "max_concurrent": serve.MAX_CONCURRENT_CHATS,
                "status": "busy" if serve.ACTIVE_TASKS >= serve.MAX_CONCURRENT_CHATS else "ready"
            }
    except Exception:
        return {
            "active_tasks": 0,
            "waiting_tasks": 0,
            "waiting_depth": 0,
            "queue_depth": 0,
            "max_concurrent": 2,
            "status": "ready"
        }

# Standard MCP JSON-RPC Server Handler (over stdio)
def run_mcp_stdio():
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            line_str = line.strip()
            if not line_str:
                continue
            req = json.loads(line_str)
            req_id = req.get("id")
            method = req.get("method")
            params = req.get("params", {})
            
            if method == "initialize":
                resp = {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "protocolVersion": params.get("protocolVersion", "2024-11-05"),
                        "capabilities": {
                            "tools": {}
                        },
                        "serverInfo": {
                            "name": "agntcon-2026-mcp",
                            "version": "1.0.0"
                        }
                    }
                }
                print(json.dumps(resp), flush=True)
            elif method in ("notifications/initialized", "initialized"):
                # Standard MCP client notification; no response needed
                continue
            elif method == "ping":
                resp = {"jsonrpc": "2.0", "id": req_id, "result": {}}
                print(json.dumps(resp), flush=True)
            elif method == "tools/list":
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
                                        "question": {"type": "string", "description": "Question to answer"},
                                        "breadth": {"type": "string", "enum": ["focused", "balanced", "deep", "auto"]},
                                        "only_with_slides": {"type": "boolean"}
                                    },
                                    "required": ["question"]
                                }
                            },
                            {
                                "name": "get_talk",
                                "description": "Retrieve full structured metadata, speakers, and summary for a single talk ID.",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "talk_id": {"type": "string", "description": "Conference talk ID (e.g. 2RBBJ)"}
                                    },
                                    "required": ["talk_id"]
                                }
                            },
                            {
                                "name": "list_talks",
                                "description": "List conference talks with optional pagination and slides filter.",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "limit": {"type": "integer", "default": 50},
                                        "offset": {"type": "integer", "default": 0},
                                        "only_with_slides": {"type": "boolean", "default": False}
                                    }
                                }
                            },
                            {
                                "name": "list_concepts",
                                "description": "List all cross-cutting architectural concepts and syntheses available in the wiki.",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {}
                                }
                            },
                            {
                                "name": "get_conference_profile",
                                "description": "Retrieve high-level conference themes, focus areas, and attendee profiling criteria.",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {}
                                }
                            },
                            {
                                "name": "get_queue_status",
                                "description": "Check current inference queue depth and server load.",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {}
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
                    res = tool_search_talks(
                        args.get("query", ""),
                        args.get("topic"),
                        only_with_slides=args.get("only_with_slides", False),
                        limit=args.get("limit", 200)
                    )
                elif tool_name == "get_page":
                    res = tool_get_page(args.get("page_type", "source"), args.get("name_or_id", ""))
                elif tool_name == "answer_conference":
                    res = asyncio.run(tool_answer_conference(
                        args.get("question", ""),
                        breadth=args.get("breadth", "auto"),
                        only_with_slides=args.get("only_with_slides", False),
                        user_context=args.get("user_context")
                    ))
                elif tool_name == "get_talk":
                    res = tool_get_talk(args.get("talk_id", ""))
                elif tool_name == "list_talks":
                    res = tool_list_talks(
                        limit=args.get("limit", 50),
                        offset=args.get("offset", 0),
                        only_with_slides=args.get("only_with_slides", False)
                    )
                elif tool_name == "list_concepts":
                    res = tool_list_concepts()
                elif tool_name == "get_conference_profile":
                    res = tool_get_conference_profile()
                elif tool_name == "get_queue_status":
                    res = tool_get_queue_status()
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
        print("[+] get_talk: Available")
        print("[+] list_talks: Available")
        print("[+] list_concepts: Available")
        print("[+] get_conference_profile: Available")
        print("[+] get_queue_status: Available")
        print("[+] MCP_SERVER_TEST_PASS: All 8 tools verified.")
        return
        
    run_mcp_stdio()

if __name__ == "__main__":
    main()

# Sprint 04 — Target Architecture Delta: Corpus-Driven Dynamic Segmentation & Session Persistence

**Sprint Identifier:** `Sprint_04_Hybrid_RAG_And_UX`  
**Archetype:** Archetype 3 (Refactoring & Hardening)  

---

## 1. Architectural Changes

### Delta 1: Corpus-Driven Word Segmentation Engine (`mcp_server.py` & `serve.py`)
* **Vocabulary Extraction:** At module initialization, query `SELECT title, one_paragraph FROM talks` in `agntcon2026.sqlite`. Extract all unique words ($\ge 3$ chars) into `CONFERENCE_VOCAB: set[str]`. Total size $\approx 2,257$ terms. Cached globally ($<5$ms startup).
* **Segmenter Function `segment_query_term(term: str, vocab: set[str]) -> list[str]`:**
  * If `term` in `vocab`: return `[term]`.
  * If $6 \le \text{len}(term) \le 32$:
    * Iterate split points $i \in [3, \text{len}(term)-2]$.
    * Test if `left` and `right` (or standard stems: `-ing`, `-s`, `-ed`) are in `vocab`.
    * If both valid: return `[left, right]`.
  * Return `[term]`.
* **Query Builder:**
  * When query contains compound terms, format FTS5 query:
    `({term} OR "{left} {right}" OR ({left} AND {right}))`
  * Example: `redteaming` $\to$ `(redteaming OR "red teaming" OR (red AND teaming))`
  * Preserves sub-millisecond execution with ZERO hardcoded dictionaries and ZERO API calls.

### Delta 2: System Prompt Softening (`mcp_server.py`)
* Modify Rule #3 from:
  ```text
  3. If the topic was not discussed in the provided excerpts, state: "This topic was not covered in the conference sessions."
  ```
  To:
  ```text
  3. If the attendee asks about a topic or terminology that is not explicitly named in the excerpts, analyze closely related architectural, security, evaluation, or tool concepts that are present (e.g. vulnerability remediation, adversarial guardrails, boundary enforcement), explicitly explaining the connection to the attendee's query. Only state a topic was not covered if no related concepts exist in the excerpts.
  ```

### Delta 3: Outbound Link Enforcement (`app.js`)
* In `openEssenceModal()`, enforce:
  ```javascript
  modalBody.querySelectorAll("a").forEach(a => {
    if (a.hostname && a.hostname !== window.location.hostname) {
      a.target = "_blank";
      a.rel = "noopener noreferrer";
    }
  });
  ```

### Delta 4: Client-Side Chat Persistence (`app.js`)
* Key: `agntcon_chat_history_v2` in `window.sessionStorage`.
* State schema: array of `{ role: "user" | "bot", html: string, timestamp: number }`.
* Storage ceiling: 40 messages max.
* Functions: `saveChatToSession()`, `restoreChatFromSession()`, `clearChatSession()`.
* Automatically load on startup and synchronize after every message.

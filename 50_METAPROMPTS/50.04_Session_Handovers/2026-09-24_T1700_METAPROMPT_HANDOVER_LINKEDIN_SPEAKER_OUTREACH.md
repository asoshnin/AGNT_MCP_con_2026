# 🎯 Metaprompt Handover: LinkedIn Speaker Outreach Autopilot

**Handover ID:** `handover-agntcon-linkedin-outreach-v1`  
**Timestamp:** 2026-09-24T17:00:00+02:00  
**Project:** AGNTCon + MCPCon Europe 2026 (`02_public_hub`)  
**Git Branch / Commit:** `main` (`e050998`)  
**Parent Playbook:** `02_public_hub/out/STAKEHOLDER_COMMUNICATIONS_PLAYBOOK.md`  
**Browser Profile:** `chrome` (Active OpenClaw Extension on port 18799)

---

## 1. Executive Status & Proven State

1. **System & App Health:** 
   - Multi-cloud hubs live (`https://agntcon-demo.vwoosh.com`), CI green (133/133 tests passing).
   - OpenClaw Chrome Extension is paired and connected (`running: true`).
2. **First Verified Invite (Proof of Work):**
   - Speaker #1 **Adewale Abati** (`https://linkedin.com/in/acekyd`) was executed in the operator's real Chrome session.
   - Status confirmed in LinkedIn Invitation Manager: **`Pending`** with the 272-character personalized note.
3. **Target Scope for This Session:**
   - Process remaining 44 speakers (Row #2 to #45) from Section 4 of `02_public_hub/out/STAKEHOLDER_COMMUNICATIONS_PLAYBOOK.md`.

---

## 2. Hard Execution Invariants

1. **Verification Gate (Correct Person Check):**
   - When navigating to `https://linkedin.com/in/<vanity_or_slug>`, snapshot the header.
   - Verify that the profile name matches the speaker and has mutual conference / AI / developer context before touching any interaction buttons.
2. **Follow First Rule:**
   - Check if a **«Follow»** button exists on the profile (and is not already following).
   - If present, click «Follow» first. If already followed or absent, proceed directly to Connect.
3. **Connect + Add a Note Flow:**
   - Locate the **«Connect»** button (or `More...` ➔ `Connect`).
   - If a prompt asks to personalize, select **`Add a note`** (NEVER send blank invites without a note).
   - Retrieve the exact pre-approved message from `STAKEHOLDER_COMMUNICATIONS_PLAYBOOK.md` ($\le 280$ characters, includes `https://agntcon-demo.vwoosh.com`).
   - Type text with human cadence (`act: type, slowly: true`).
   - Submit via `Send` button.
4. **Anti-Bot Rate-Limiting & Jitter:**
   - Sleep 8–15 seconds between speakers.
   - Process in bounded batches of 5 speakers per turn, presenting a status checkpoint before advancing.
5. **State Logging:**
   - Record each dispatched speaker into a progress card or log table with timestamp and status (`PENDING`).

---

## 3. Immediate Step 1 for the New Session

Open `02_public_hub/out/STAKEHOLDER_COMMUNICATIONS_PLAYBOOK.md`, verify `browser(action="tabs", profile="chrome")` is active, and dispatch the invitation for Speaker #2:
- **Speaker #2:** Fausto Albers (WonderWhy AI, Session `2RBBV`)
- **Profile:** `https://linkedin.com/in/stepintoliquid`
- **Action:** Verify profile ➔ Click Follow ➔ Click Connect ➔ Add a note ➔ Type pre-approved text ➔ Submit.

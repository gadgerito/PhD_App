"""
comps_coach.py
--------------
Comps Coach modal for the Batman PhD Streamlit app.
Drop this file in the same directory as phd_app.py, then follow
the three integration steps at the bottom of this file.
"""

import streamlit as st
from anthropic import Anthropic

# ── Constants ──────────────────────────────────────────────────────────────

COMPS_SYSTEM_PROMPT = """You are a knowledgeable, warm dissertation coach specializing in the CUNY School of Public Health (CUNY SPH) CHHP doctoral program comprehensive exam. You help PhD students navigate their comps with accurate, program-specific guidance.

WHAT IS THE COMPREHENSIVE EXAM:
- Independent scholarly activity: written paper + oral defense before a closed committee
- Literature reviews — NOT a dissertation proposal, NOT data collection or analysis
- Serves as exploration of dissertation topic area
- Provides background for eventual dissertation questions and proposal

ELIGIBILITY:
- Must have passed the qualifying exam
- Must have completed all coursework (can be taking last 1-2 electives concurrently, including teaching requirement)
- If taking final elective concurrently: no additional registration needed
- If not taking any courses: must register for Maintenance of Matriculation (with doctoral director approval)
- Ideally completed in one semester

WRITTEN FORMAT:
- 30 double-spaced pages MAXIMUM (not including title page, references, or appendices)
- 11–12 point font size
- Structure:
  1. Brief Introduction (states purpose of paper)
  2. Four sections:
     - Two content areas (OR one content area + one public health theory or policy analysis)
     - Two research methods sections
  3. Brief Conclusion (summarizes what is known, identifies gaps → leads to dissertation questions)

COMMITTEE:
- 3 members total
- 2 members must be affiliated with CUNY SPH
- Chair must be from HPAM or CHASS
- Can have a 4th person participate but not officially serve as committee member
- Often (but not always) becomes the dissertation committee
- Choose for: (1) substantive expertise, (2) compatibility, (3) availability and responsiveness

PROCESS STEPS:
1. Prepare list of potential topics, methods, policies, theories
2. Identify exam chair — write a one-paragraph overview first, finalize 4 section categories
3. Identify two other committee members (with chair's help)
4. Complete the application to take the exam
5. Send reading list to committee for approval
6. Prepare draft — one section at a time, iterate with chair before defense
7. Set defense date; coordinate with Departmental Administrators (Himani or Toya) for Zoom room
8. Chair notifies Registrar and PhD Program Director after successful defense
9. Email doctoral director to move to Level III; identify dissertation chair; begin proposal

ORAL DEFENSE FORMAT:
- Closed to public (only committee members), 2 hours total
- 20-minute student presentation (highlights of paper)
- Committee questions, then student leaves for deliberation
- Outcomes: pass, pass with revisions, or fail
- Chair emails Registrar and doctoral director with determination

DR. TSUI'S METHODS RECIPE:
1. Describe what the method is — what research questions does it suit? Strengths and limitations?
2. Explore how the method has been used in your content area (look at adjacent areas if needed)
3. Critically analyze how people have used that method:
   - Where has it worked?
   - Where has it NOT worked or contributed little?
   - This reveals how to employ the method differently to shape your dissertation

SUMMER FAQ:
- Faculty are not contracted in summer — ask chair/committee if willing to review drafts
- If not: finalize topics end of spring, draft over summer, ready for review in early fall
- If yes: can defend in summer semester

KEY HACKS FOR SUCCESS:
- Pick a topic you're genuinely excited about
- Map out a timeline with your chair and committee — time management is critical
- Start reading early — have major lit review done before writing begins
- Break daunting tasks into tiny manageable pieces
- Choose chair/committee carefully: expertise + compatibility + availability
- Don't just aim to pass — treat it as dissertation groundwork
- Communicate early and clearly with all committee members
- Having a focus is critical — identify an unsolved public health problem and what's known/unknown

AFTER PASSING:
- Email doctoral director to advance to Level III
- Identify dissertation chair (may be same as comp chair)
- Start writing dissertation proposal

Respond in a warm, encouraging tone. Be specific to CUNY SPH requirements. Keep answers focused and practical. Use bullet points and clear structure for scannability."""

QUICK_PROMPTS = [
    ("📝", "Paper sections", "What are the four sections I need to write and what goes in each?"),
    ("👥", "Committee rules", "What are all the rules for assembling my committee?"),
    ("🔬", "Methods recipe", "Walk me through Dr. Tsui's methods recipe step by step."),
    ("🎤", "Oral defense", "What exactly happens at the oral defense?"),
    ("⚡", "Top hacks", "What are the top hacks for succeeding at comps?"),
    ("☀️", "Summer FAQ", "Can I work on comps over the summer?"),
    ("🗺️", "Process steps", "Walk me through all the steps of the comp exam process in order."),
    ("🎯", "Choosing topics", "How should I choose my four section topics strategically?"),
]

# ── Session state helpers ───────────────────────────────────────────────────

def _init_state():
    if "comps_open" not in st.session_state:
        st.session_state.comps_open = False
    if "comps_messages" not in st.session_state:
        st.session_state.comps_messages = []
    if "comps_loading" not in st.session_state:
        st.session_state.comps_loading = False


def _send(user_text: str, client: Anthropic, context_prompt: str = ""):
    """Append user message, call API, append assistant reply."""
    st.session_state.comps_messages.append({"role": "user", "content": user_text})
    st.session_state.comps_loading = True

    # COMPS_SYSTEM_PROMPT is large and static — mark it cacheable so repeated
    # messages in the same session pay ~10% of the token cost after the first call.
    system = [{"type": "text", "text": COMPS_SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}]
    if context_prompt:
        system.append({"type": "text", "text": context_prompt})

    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=1024,
        system=system,
        messages=st.session_state.comps_messages,
    )
    reply = response.content[0].text
    st.session_state.comps_messages.append({"role": "assistant", "content": reply})
    st.session_state.comps_loading = False


# ── Public functions ────────────────────────────────────────────────────────

def render_floating_button():
    """
    Renders the floating 🦇 Comps Coach button fixed to the bottom-right.
    Call this once per page render, before render_comps_modal().
    """
    st.markdown("""
    <style>
    .comps-fab {
        position: fixed;
        bottom: 28px;
        right: 28px;
        z-index: 9999;
    }
    .comps-fab button {
        background: #1a1410 !important;
        color: #e8c876 !important;
        border: 2px solid #c9983a !important;
        border-radius: 50px !important;
        padding: 10px 20px !important;
        font-size: 15px !important;
        font-weight: 600 !important;
        cursor: pointer !important;
        box-shadow: 0 4px 20px rgba(0,0,0,0.4) !important;
        transition: all 0.2s !important;
    }
    .comps-fab button:hover {
        background: #c9983a !important;
        color: #1a1410 !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # Streamlit button can't be truly fixed-position, so we use a sidebar
    # workaround: inject the button via st.button and let CSS handle placement.
    # For a true floating effect, we use columns to push right.
    col1, col2 = st.columns([8, 1])
    with col2:
        if st.button("🎓 Comps", key="comps_fab_btn", help="Open Comps Coach"):
            st.session_state.comps_open = not st.session_state.comps_open
            st.rerun()


def render_comps_modal(client: Anthropic, context_data: dict = None):
    """
    Renders the Comps Coach chat modal when comps_open is True.
    Pass in your existing Anthropic client instance and optionally context_data.

    context_data can include:
      - xp: current XP
      - section_timers: {section: minutes} dict
      - saved_responses: {key: response_text} dict
      - last_worked_section: string
      - last_worked_date: string
    """
    _init_state()

    if not st.session_state.comps_open:
        return

    # Build context prompt from data
    context_prompt = ""
    if context_data:
        ctx_parts = ["STUDENT'S CURRENT PROGRESS:"]
        if context_data.get("xp"):
            ctx_parts.append(f"- XP earned: {context_data['xp']}")
        if context_data.get("last_worked_section"):
            ctx_parts.append(f"- Last worked section: {context_data['last_worked_section']}")
        if context_data.get("last_worked_date"):
            ctx_parts.append(f"- Last worked date: {context_data['last_worked_date']}")
        if context_data.get("section_timers"):
            total_mins = sum(context_data["section_timers"].values())
            ctx_parts.append(f"- Total focus time: {total_mins // 60}h {total_mins % 60}m")
            for section, mins in sorted(context_data["section_timers"].items(), key=lambda x: x[1], reverse=True):
                ctx_parts.append(f"  • {section}: {mins}m")
        if context_data.get("saved_responses"):
            ctx_parts.append(f"- Sections with draft responses: {len(context_data['saved_responses'])}")

        context_prompt = "\n".join(ctx_parts) + "\n\nGive feedback on whether their current work aligns with comps requirements and deadlines."

    with st.container():
        st.markdown("""
        <style>
        .comps-modal {
            background: #faf8f4;
            border: 2px solid #c9983a;
            border-radius: 12px;
            padding: 0;
            margin-bottom: 24px;
        }
        .comps-header {
            background: #1a1410;
            color: #e8c876;
            padding: 14px 20px;
            border-radius: 10px 10px 0 0;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .comps-body { padding: 16px 20px; }
        .comps-msg-user {
            background: #1a1410;
            color: #f5f0e8;
            padding: 10px 14px;
            border-radius: 12px 2px 12px 12px;
            margin: 6px 0 6px 40px;
            font-size: 14px;
            line-height: 1.5;
        }
        .comps-msg-assistant {
            background: #fff;
            border: 1px solid #d4c9b8;
            color: #1a1410;
            padding: 10px 14px;
            border-radius: 2px 12px 12px 12px;
            margin: 6px 40px 6px 0;
            font-size: 14px;
            line-height: 1.5;
        }
        .comps-stats {
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
            margin-bottom: 12px;
        }
        .comps-stat {
            background: #1a1410;
            color: #e8c876;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
        }
        </style>
        """, unsafe_allow_html=True)

        # ── Header ──
        header_col, close_col = st.columns([6, 1])
        with header_col:
            st.markdown("### 🎓 Comps Coach")
            st.caption("CUNY SPH · CHHP Doctoral Program")
        with close_col:
            if st.button("✕", key="comps_close", help="Close"):
                st.session_state.comps_open = False
                st.rerun()

        # ── At-a-glance stats ──
        st.markdown("""
        <div class="comps-stats">
            <span class="comps-stat">30 pages max</span>
            <span class="comps-stat">4 sections</span>
            <span class="comps-stat">3 committee members</span>
            <span class="comps-stat">2-hr defense</span>
        </div>
        """, unsafe_allow_html=True)

        st.divider()

        # ── Quick prompts ──
        if not st.session_state.comps_messages:
            st.markdown("**Quick questions:**")
            cols = st.columns(4)
            for i, (icon, label, prompt) in enumerate(QUICK_PROMPTS):
                with cols[i % 4]:
                    if st.button(f"{icon} {label}", key=f"qp_{i}"):
                        _send(prompt, client, context_prompt)
                        st.rerun()

        # ── Chat history ──
        if st.session_state.comps_messages:
            chat_container = st.container(height=350)
            with chat_container:
                for msg in st.session_state.comps_messages:
                    if msg["role"] == "user":
                        st.markdown(
                            f'<div class="comps-msg-user">👤 {msg["content"]}</div>',
                            unsafe_allow_html=True
                        )
                    else:
                        st.markdown(
                            f'<div class="comps-msg-assistant">🎓 {msg["content"]}</div>',
                            unsafe_allow_html=True
                        )

            if st.session_state.comps_loading:
                st.info("🎓 Thinking...")

        # ── Input ──
        st.markdown("**Ask anything about your comps:**")
        input_col, btn_col = st.columns([5, 1])
        with input_col:
            user_input = st.text_input(
                "comps_input",
                label_visibility="collapsed",
                placeholder="e.g. How do I structure my methods section?",
                key="comps_text_input"
            )
        with btn_col:
            if st.button("Send", key="comps_send", type="primary"):
                if user_input.strip():
                    _send(user_input.strip(), client, context_prompt)
                    st.rerun()

        # ── Clear chat ──
        if st.session_state.comps_messages:
            if st.button("🗑️ Clear chat", key="comps_clear"):
                st.session_state.comps_messages = []
                st.rerun()


# ══════════════════════════════════════════════════════════════════
#  INTEGRATION INSTRUCTIONS FOR CLAUDE CODE
# ══════════════════════════════════════════════════════════════════
#
#  1. DROP THIS FILE next to phd_app.py:
#
#       comps_coach.py   ← this file
#       phd_app.py
#
#  2. ADD THESE IMPORTS at the top of phd_app.py (with your other imports):
#
#       from comps_coach import render_floating_button, render_comps_modal
#
#  3. ADD THESE TWO CALLS inside your main() function or wherever your
#     page renders — AFTER your existing tab/content code so the button
#     floats on top of everything:
#
#       render_floating_button()
#       render_comps_modal(client)   # pass your existing Anthropic client
#
#     If your Anthropic client is named something other than `client`,
#     swap it in. The module uses the same client you already have —
#     no new API key or setup needed.
#
#  That's it. No MongoDB changes needed — chat history lives in
#  session_state only (resets on page refresh, which is intentional
#  for a focused coaching session).
# ══════════════════════════════════════════════════════════════════

import streamlit as st
import streamlit.components.v1 as components
import json
import os
import time
import pandas as pd
from datetime import datetime, timedelta
import random
from pymongo import MongoClient
from pathlib import Path
import base64
@st.cache_data
def get_audio_b64():
    audio_path = Path(__file__).parent / "static" / "bat.sting.wav"
    with open(audio_path, "rb") as f:
        return base64.b64encode(f.read()).decode()

# --- MUST BE FIRST ---
st.set_page_config(layout="wide", page_title="The Dark Knight of Public Health", page_icon="🦇")

# ── PASSWORD GATE ──
def check_password():
    if st.session_state.get("authenticated"):
        return True
    st.markdown("## 🦇 Bat-Computer Access")
    password = st.text_input("Enter password:", type="password")
    if st.button("Enter the Batcave"):
        if password == st.secrets["app"]["password"]:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Access Denied. This is not your city.")
    return False

if not check_password():
    st.stop()
# -- MongoDB --
@st.cache_resource
def get_mongo_db():
    client = MongoClient(
        st.secrets["mongo"]["uri"],
        username=st.secrets["mongo"]["username"],
        password=st.secrets["mongo"]["password"],
        tls=True,
        tlsAllowInvalidCertificates=True
    )
    return client["phd_app"]

def get_db():
    return get_mongo_db()["progress"]

# --- SERVE STATIC FOLDER ===
st.markdown(
    '<link rel="preload" href="app/static/bat_sting.wav" as="audio">',
    unsafe_allow_html=True
)
# ─────────────────────────────────────────────
# 1. PERSISTENCE
# ─────────────────────────────────────────────
def load_all_progress():
    try:
        db = get_db()
        d = db.find_one({"_id": "main"})

        if not d:
            return 0, set(), {}, {}, [], [], {}, ""

        return (d.get("xp", 0),
        set(d.get("completed_tasks", [])),
        d.get("saved_responses", {}),
        d.get("task_timers", {}),
        d.get("custom_rewards", []),
        d.get("claimed_rewards", []),
        d.get("custom_vault", {}),
        d.get("last_task_id", ""),
        d.get("last_worked_section", ""),
        d.get("last_worked_date", ""),
        d.get("notebook_entries", []),
        )
    except Exception as e:
        st.error(f"MongoDB connection error: {e}")
        return 0, set(), {}, {}, [], [], {}, "", []


def save_all_progress():
    try:
        db = get_db()
        data = {
            "_id": "main",
            "xp": st.session_state.xp,
            "completed_tasks": list(st.session_state.completed_tasks),
            "saved_responses": st.session_state.saved_responses,
            "task_timers": st.session_state.task_timers,
            "custom_rewards": st.session_state.custom_rewards,
            "claimed_rewards": st.session_state.claimed_rewards,
            "custom_vault": st.session_state.custom_vault,
            "last_task_id": st.session_state.get("last_task_id", ""),
            "last_worked_section": st.session_state.get("last_worked_section", ""),
            "last_worked_date": st.session_state.get("last_worked_date", ""),
            "notebook_entries": st.session_state.get("notebook_entries", []),
        }
        db.replace_one({"_id": "main"}, data, upsert=True)
    except Exception as e:
        st.error(f"Save failed: {e}")
# ─────────────────────────────────────────────
# 2. INITIALIZATION
# ─────────────────────────────────────────────
if 'initialized' not in st.session_state:
    xp, comp_tasks, resps, timers, custom_r, claimed, vault, last_task, last_worked_section, last_worked_date, notebook = load_all_progress()
    st.session_state.xp = xp
    st.session_state.completed_tasks = comp_tasks
    st.session_state.saved_responses = resps
    st.session_state.task_timers = timers
    st.session_state.custom_rewards = custom_r
    st.session_state.claimed_rewards = claimed
    st.session_state.notebook_entries = notebook
    st.session_state.custom_vault = vault if vault else {
        "🚀 Openers": ["Building upon...", "Premised on...", "Centrally to..."],
        "⚖️ Contrast": ["Notwithstanding", "Conversely", "Paradoxically"],
        "🎯 Result":   ["Consequently", "Accordingly", "Ultimately"],
        "💎 Synonyms": ["Elucidate (Show)", "Bolster (Help)", "Nexus (Link)"]
    }
    st.session_state.last_task_id = last_task
    st.session_state.last_worked_section = last_worked_section
    st.session_state.last_worked_date = last_worked_date
    st.session_state.initialized = True

# Celebration state — read ONCE at top of render, then reset so they don't replay next run
celebration_xp    = st.session_state.get('celebration_xp', 0)
rank_up_title     = st.session_state.get('rank_up_title', '')
pomodoro_done     = st.session_state.get('pomodoro_done', False)
reward_claimed    = st.session_state.get('reward_claimed', '')
st.session_state.celebration_xp  = 0
st.session_state.rank_up_title   = ''
st.session_state.pomodoro_done   = False
st.session_state.reward_claimed  = ''

# Play audio if flagged
if st.session_state.get('play_audio'):
    audio_b64 = get_audio_b64()
    components.html(
        f"""
        <script>
            const audio = new Audio('data:audio/wav;base64,{audio_b64}');
            audio.play().catch(e => console.log('Audio blocked:', e));
        </script>
        """,
        height=0
    )
    st.session_state.play_audio = False

# ─────────────────────────────────────────────
# 3. RANK SYSTEM
# ─────────────────────────────────────────────
RANKS = [
    (0,    "🐦 Robin",          "#7f8c8d"),
    (100,  "🔵 Nightwing",      "#2980b9"),
    (250,  "🟣 Batgirl",        "#8e44ad"),
    (500,  "🟠 Red Hood",       "#e67e22"),
    (750,  "⚫ Batman",         "#2c3e50"),
    (1000, "🦇 Dark Knight",    "#f1c40f"),
    (1500, "💀 World's Finest", "#c0392b"),
    (2500, "🌌 Justice League", "#1abc9c"),
]

def get_rank(xp):
    rank = RANKS[0]
    for item in RANKS:
        if xp >= item[0]:
            rank = item
    return rank

def get_next_rank(xp):
    for threshold, title, color in RANKS:
        if xp < threshold:
            return threshold, title
    return None, None

def render_rank_badge(xp):
    _, title, color = get_rank(xp)
    next_xp, next_title = get_next_rank(xp)
    st.markdown(
        f'<div class="rank-badge" style="border-color:{color};background:{color}22;color:{color};">{title}</div>',
        unsafe_allow_html=True
    )
    if next_xp:
        needed = next_xp - xp
        st.markdown(
            f'<div class="rank-next">🔺 {needed} XP until <b>{next_title}</b></div>',
            unsafe_allow_html=True
        )
    else:
        st.markdown('<div class="rank-next">🏆 Maximum rank achieved!</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────
# 4. BATMAN QUOTES
# ─────────────────────────────────────────────
BATMAN_QUOTES = [
    ("It's not who I am underneath, but what I do that defines me.", "Batman Begins"),
    ("Everything's impossible until somebody does it.", "Batman"),
    ("Why do we fall? So we can learn to pick ourselves up.", "Batman Begins"),
    ("I wear a mask. And that mask, it's not to hide who I am — but to create what I am.", "Batman"),
    ("The night is darkest just before the dawn.", "The Dark Knight"),
    ("I am whatever Gotham needs me to be.", "The Dark Knight"),
    ("Endure. They'll hate you for it, but that's the point of Batman.", "The Dark Knight Rises"),
    ("A hero can be anyone.", "The Dark Knight Rises"),
    ("You either die a hero, or you live long enough to see yourself become the villain.", "The Dark Knight"),
    ("The training is nothing. The will is everything.", "Batman Begins"),
    ("Sometimes it's only madness that makes us what we are.", "Batman"),
    ("I have one rule.", "The Dark Knight"),
    ("I'm Batman.", "Batman"),
]

def quote_box(quote, source, typewriter=True):
    tw_class = "typewriter" if typewriter else ""
    return f"""
    <div class="quote-wrap">
        <div class="quote-inner {tw_class}">
            &ldquo;{quote}&rdquo;
            <div class="quote-src">— {source}</div>
        </div>
    </div>"""

# ─────────────────────────────────────────────
# 5. CSS — ALL AMBIENT ANIMATIONS
# ─────────────────────────────────────────────
st.markdown("""
<style>
/* ── Base ── */
.stApp { background:#ffffff !important; color:#000000 !important; }
.bat-tagline { color:#7f8c8d; font-style:italic; font-size:1.2rem; margin-top:-18px; margin-bottom:4px; }
.rank-badge  { display:inline-block; padding:6px 16px; border-radius:20px; font-weight:bold;
               font-size:1.0rem; margin:4px 0; border:2px solid; animation:badge-pulse 3s ease-in-out infinite; }
.rank-next   { font-size:0.82rem; color:#555; margin-top:2px; }

@keyframes badge-pulse {
    0%,100% { box-shadow: 0 0 4px currentColor; }
    50%      { box-shadow: 0 0 16px currentColor, 0 0 30px currentColor; }
}

/* ── Buttons ── */
.stButton>button {
    border-radius:12px; border:2px solid #f1c40f;
    background:white; color:black; font-weight:bold;
    transition: all 0.15s ease;
    position: relative; overflow: hidden;
}
.stButton>button:hover {
    background: #fffbe6 !important;
    box-shadow: 0 0 16px rgba(241,196,15,0.7), 0 0 32px rgba(241,196,15,0.3) !important;
    transform: translateY(-1px);
}
.stButton>button:active { transform:scale(0.97); }

/* Ripple on click */
.stButton>button::after {
    content:''; position:absolute; border-radius:50%;
    background:rgba(241,196,15,0.4);
    transform:scale(0); opacity:0;
    width:200%; height:200%; left:-50%; top:-50%;
    transition: transform 0.4s, opacity 0.4s;
}
.stButton>button:active::after { transform:scale(1); opacity:0; transition:0s; }

/* ── Progress bars — animated gold shimmer ── */
[data-testid="stProgressBar"] > div > div {
    background: linear-gradient(90deg,
        #c9a227 0%, #f1c40f 25%, #ffe566 50%, #f1c40f 75%, #c9a227 100%) !important;
    background-size: 300% auto !important;
    animation: shimmer-bar 2.2s linear infinite !important;
    border-radius: 6px !important;
}
@keyframes shimmer-bar {
    0%   { background-position: 0%   center; }
    100% { background-position: 300% center; }
}

/* ── Quote box ── */
.quote-wrap  { margin: 10px 0 18px 0; }
.quote-inner {
    background: linear-gradient(135deg,#1a1a2e 0%,#16213e 50%,#0f3460 100%);
    border-left: 4px solid #f1c40f; border-radius: 8px;
    padding: 14px 20px; color: #f0e6c8;
    font-style: italic; font-size: 1.05rem;
    animation: slide-in 0.5s cubic-bezier(0.22,1,0.36,1);
}
.quote-src { color:#f1c40f; font-size:0.8rem; font-style:normal; font-weight:bold; margin-top:6px; }

@keyframes slide-in {
    from { opacity:0; transform:translateX(-20px); }
    to   { opacity:1; transform:translateX(0); }
}

/* Typewriter cursor blink on quote */
.typewriter { border-right: 2px solid transparent; animation: slide-in 0.5s ease, caret-blink 1s step-end 0.5s 6; }
@keyframes caret-blink { 0%,100%{border-color:transparent} 50%{border-color:#f1c40f} }

/* ── Bat Signal ── */
#bat-signal {
    position:fixed; top:65px; right:55px; width:90px; height:90px;
    z-index:9999; pointer-events:none; border-radius:50%;
    background:radial-gradient(circle,#ffe066 0%,#f1c40f 45%,rgba(241,196,15,.25) 70%,transparent 100%);
    animation:bat-pulse 2.5s ease-in-out infinite;
    display:flex; align-items:center; justify-content:center;
}
#bat-signal svg { width:58px; height:58px; filter:drop-shadow(0 0 3px rgba(0,0,0,.5)); }
@keyframes bat-pulse {
    0%,100% { box-shadow:0 0 18px 6px rgba(241,196,15,.55),0 0 40px 10px rgba(241,196,15,.25); }
    50%      { box-shadow:0 0 38px 16px rgba(241,196,15,.95),0 0 80px 30px rgba(241,196,15,.50); }
}

/* ── Flying bats ── */
.fly-bat {
    position:fixed; z-index:9990; pointer-events:none;
    animation: fly-across linear infinite;
    will-change: transform;
}
@keyframes fly-across {
    0%   { transform:translateX(-80px); opacity:0; }
    4%   { opacity:0.55; }
    96%  { opacity:0.55; }
    100% { transform:translateX(calc(100vw + 80px)); opacity:0; }
}

/* Flapping wings via scale pulse */
.fly-bat span { display:inline-block; animation: flap 0.3s ease-in-out infinite alternate; }
@keyframes flap { from{transform:scaleY(1)} to{transform:scaleY(0.6)} }

/* ── Completed task row ── */
.task-done { animation: done-flash 0.6s ease-out; }
@keyframes done-flash {
    0%   { background: rgba(241,196,15,0.5); }
    100% { background: transparent; }
}

/* ── XP metric glow ── */
[data-testid="stMetricValue"] {
    color: #c9a227 !important;
    text-shadow: 0 0 10px rgba(241,196,15,0.5);
    animation: xp-glow 3s ease-in-out infinite;
}
@keyframes xp-glow {
    0%,100% { text-shadow: 0 0 8px rgba(241,196,15,0.4); }
    50%      { text-shadow: 0 0 20px rgba(241,196,15,0.9), 0 0 40px rgba(241,196,15,0.4); }
}

/* ── Reward button available pulse ── */
.reward-available .stButton>button {
    animation: reward-pulse 1.8s ease-in-out infinite;
}
@keyframes reward-pulse {
    0%,100% { box-shadow: 0 0 6px rgba(241,196,15,0.4); }
    50%      { box-shadow: 0 0 22px rgba(241,196,15,1.0), 0 0 44px rgba(241,196,15,0.5); }
}

/* ── Tab glow ── */
[data-baseweb="tab"] { transition: all 0.2s ease; }
[aria-selected="true"][data-baseweb="tab"] {
    text-shadow: 0 0 8px rgba(241,196,15,0.8) !important;
}

/* ── Rank card in Rewards ── */
.rank-card {
    text-align:center; padding:8px 4px; border-radius:10px;
    border:2px solid; margin:2px;
    transition: all 0.3s ease;
}
.rank-card.unlocked { animation: rank-card-pulse 2.5s ease-in-out infinite; }
@keyframes rank-card-pulse {
    0%,100% { transform:scale(1); }
    50%      { transform:scale(1.04); box-shadow:0 0 12px currentColor; }
}
</style>

<!-- Bat Signal -->
<div id="bat-signal">
    <svg viewBox="0 0 100 65" xmlns="http://www.w3.org/2000/svg">
        <path d="M50,18 C50,18 43,8 28,12 C18,15 8,22 5,30 C12,26 20,27 25,32
                 C20,34 14,40 13,48 C19,41 27,40 33,42 L38,52
                 C41,57 44,60 50,60 C56,60 59,57 62,52 L67,42
                 C73,40 81,41 87,48 C86,40 80,34 75,32
                 C80,27 88,26 95,30 C92,22 82,15 72,12
                 C57,8 50,18 50,18 Z" fill="#1a1a1a"/>
    </svg>
</div>

<!-- Flying bats (3 at different heights/speeds) -->
<div class="fly-bat" style="top:9%;font-size:20px;animation-duration:14s;animation-delay:0s;">
    <span>🦇</span>
</div>
<div class="fly-bat" style="top:28%;font-size:13px;animation-duration:21s;animation-delay:-7s;opacity:0.45;">
    <span>🦇</span>
</div>
<div class="fly-bat" style="top:52%;font-size:16px;animation-duration:17s;animation-delay:-11s;opacity:0.35;">
    <span>🦇</span>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# 6. JS CELEBRATION ANIMATIONS  (iframe → window.parent escape)
# ─────────────────────────────────────────────
js_code = f"""
<script>
(function() {{

    // ── helpers ──
    function getParent() {{
        try {{ return window.parent; }} catch(e) {{ return window; }}
    }}
    const pw = getParent();
    const pdoc = pw.document;
    const pbody = pdoc.body;

    // ════════════════════════════════════════
    // A. PARTICLE BURST + FLOATING XP TEXT
    // ════════════════════════════════════════
    const celebXP = {celebration_xp};
    if (celebXP > 0) {{
        // Remove old canvas if exists
        const old = pdoc.getElementById('bat-celebration');
        if (old) old.remove();

        const canvas = pdoc.createElement('canvas');
        canvas.id = 'bat-celebration';
        canvas.style.cssText = 'position:fixed;top:0;left:0;width:100vw;height:100vh;'
            + 'pointer-events:none;z-index:99998;';
        canvas.width  = pw.innerWidth;
        canvas.height = pw.innerHeight;
        pbody.appendChild(canvas);
        const ctx = canvas.getContext('2d');

        const colors = ['#f1c40f','#ffd93d','#ff6b6b','#4ecdc4','#a29bfe','#fd79a8','#55efc4'];
        const particles = [];
        const CX = canvas.width  * 0.5;
        const CY = canvas.height * 0.38;

        // Build particles — mix of confetti rectangles, circles, mini-bats
        for (let i = 0; i < 160; i++) {{
            const angle = Math.random() * Math.PI * 2;
            const spd   = Math.random() * 14 + 3;
            particles.push({{
                x: CX, y: CY,
                vx: Math.cos(angle) * spd,
                vy: Math.sin(angle) * spd - 6,
                color:  colors[Math.floor(Math.random() * colors.length)],
                w: Math.random() * 12 + 4,
                h: Math.random() * 6  + 3,
                life:  1.0,
                decay: Math.random() * 0.016 + 0.007,
                rot:   Math.random() * Math.PI * 2,
                rotV:  (Math.random() - 0.5) * 0.18,
                shape: Math.random() > 0.7 ? 'circle' : 'rect'
            }});
        }}

        // Floating XP text
        let fY = CY - 20, fOpacity = 1;

        function animateCeleb() {{
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            let alive = false;

            for (const p of particles) {{
                if (p.life <= 0) continue;
                alive = true;
                p.x  += p.vx;  p.y  += p.vy;
                p.vy += 0.28;  p.vx *= 0.99;
                p.life -= p.decay;
                p.rot  += p.rotV;

                ctx.save();
                ctx.globalAlpha = Math.max(0, p.life);
                ctx.fillStyle   = p.color;
                ctx.translate(p.x, p.y);
                ctx.rotate(p.rot);
                if (p.shape === 'circle') {{
                    ctx.beginPath();
                    ctx.arc(0, 0, p.w / 2, 0, Math.PI * 2);
                    ctx.fill();
                }} else {{
                    ctx.fillRect(-p.w/2, -p.h/2, p.w, p.h);
                }}
                ctx.restore();
            }}

            // XP float
            if (fOpacity > 0) {{
                alive = true;
                ctx.save();
                ctx.globalAlpha = fOpacity;
                ctx.font        = 'bold 60px system-ui, -apple-system, sans-serif';
                ctx.textAlign   = 'center';
                ctx.shadowColor = '#f1c40f';
                ctx.shadowBlur  = 30;
                ctx.fillStyle   = '#f1c40f';
                ctx.fillText('+' + celebXP + ' XP ⚡', CX, fY);
                // Outline
                ctx.shadowBlur  = 0;
                ctx.strokeStyle = 'rgba(0,0,0,0.3)';
                ctx.lineWidth   = 3;
                ctx.strokeText('+' + celebXP + ' XP ⚡', CX, fY);
                ctx.restore();
                fY       -= 1.6;
                fOpacity -= 0.013;
            }}

            if (alive) requestAnimationFrame(animateCeleb);
            else canvas.remove();
        }}
        animateCeleb();
    }}

    // ════════════════════════════════════════
    // B. RANK-UP DRAMATIC OVERLAY
    // ════════════════════════════════════════
    const rankTitle = {repr(rank_up_title)};
    if (rankTitle) {{
        const old = pdoc.getElementById('rank-up-overlay');
        if (old) old.remove();

        const style = pdoc.createElement('style');
        style.textContent = `
            @keyframes ru-bounce  {{ 0%{{transform:scale(0) rotate(-8deg);opacity:0}}
                                     65%{{transform:scale(1.08) rotate(2deg);opacity:1}}
                                     100%{{transform:scale(1) rotate(0)}} }}
            @keyframes ru-letters {{ from{{letter-spacing:0.3em;opacity:0}} to{{letter-spacing:0.08em;opacity:1}} }}
            @keyframes ru-title   {{ from{{transform:translateY(20px);opacity:0}} to{{transform:translateY(0);opacity:1}} }}
            @keyframes ru-stars   {{ 0%,100%{{opacity:0.3}} 50%{{opacity:1}} }}
        `;
        pdoc.head.appendChild(style);

        const overlay = pdoc.createElement('div');
        overlay.id = 'rank-up-overlay';
        overlay.style.cssText = 'position:fixed;top:0;left:0;width:100vw;height:100vh;'
            + 'background:radial-gradient(ellipse at center,rgba(15,10,30,0.96) 0%,rgba(0,0,0,0.92) 100%);'
            + 'z-index:100000;display:flex;flex-direction:column;align-items:center;'
            + 'justify-content:center;pointer-events:none;';
        overlay.innerHTML = `
            <div style="animation:ru-bounce 0.7s cubic-bezier(.175,.885,.32,1.275) forwards;text-align:center;">
                <div style="font-size:5rem;filter:drop-shadow(0 0 20px #f1c40f);">🦇</div>
                <div style="color:#f1c40f;font-size:1.3rem;font-weight:900;letter-spacing:0.3em;
                             text-shadow:0 0 30px #f1c40f,0 0 60px #f1c40f;
                             font-family:Georgia,serif;margin:8px 0;
                             animation:ru-letters 0.6s 0.3s ease-out both;">
                    ⚡ RANK UP ⚡
                </div>
                <div style="color:white;font-size:3rem;font-weight:bold;
                             text-shadow:0 0 20px rgba(241,196,15,0.8);
                             animation:ru-title 0.5s 0.5s ease-out both;">${{rankTitle}}</div>
                <div style="color:#f1c40f;opacity:0.6;font-size:0.95rem;margin-top:10px;
                             animation:ru-stars 1.5s 0.8s ease-in-out infinite;">
                    ✦ &nbsp; Gotham has a new protector &nbsp; ✦
                </div>
            </div>`;

        pbody.appendChild(overlay);
        setTimeout(() => {{
            overlay.style.transition = 'opacity 0.9s ease';
            overlay.style.opacity    = '0';
            setTimeout(() => {{ overlay.remove(); style.remove(); }}, 900);
        }}, 2800);
    }}

    // ════════════════════════════════════════
    // C. POMODORO COMPLETE — LIGHTNING FLASH
    // ════════════════════════════════════════
    const pomoDone = {'true' if pomodoro_done else 'false'};
    if (pomoDone) {{
        const flash = pdoc.createElement('div');
        flash.style.cssText = 'position:fixed;top:0;left:0;width:100vw;height:100vh;'
            + 'background:rgba(241,196,15,0.25);z-index:99990;pointer-events:none;'
            + 'animation:flash-out 1s ease-out forwards;';
        const fs = pdoc.createElement('style');
        fs.textContent = '@keyframes flash-out{{from{{opacity:1}}to{{opacity:0}}}}';
        pdoc.head.appendChild(fs);

        const msg = pdoc.createElement('div');
        msg.style.cssText = 'position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);'
            + 'background:linear-gradient(135deg,#1a1a2e,#0f3460);color:#f1c40f;'
            + 'font-size:2rem;font-weight:bold;padding:24px 40px;border-radius:16px;'
            + 'border:3px solid #f1c40f;z-index:99991;pointer-events:none;text-align:center;'
            + 'box-shadow:0 0 40px rgba(241,196,15,0.6);'
            + 'animation:flash-out 1s 2s ease-out forwards;';
        msg.innerHTML = '⚡ SPRINT COMPLETE! ⚡<br><span style="font-size:1.1rem;opacity:0.8;">+25 XP earned</span>';

        pbody.appendChild(flash);
        pbody.appendChild(msg);
        setTimeout(() => {{ flash.remove(); msg.remove(); fs.remove(); }}, 3200);
    }}

    // ════════════════════════════════════════
    // D. REWARD CLAIMED — GOLDEN SHOWER
    // ════════════════════════════════════════
    const rewardItem = {repr(reward_claimed)};
    if (rewardItem) {{
        const old2 = pdoc.getElementById('reward-canvas');
        if (old2) old2.remove();

        const rc = pdoc.createElement('canvas');
        rc.id = 'reward-canvas';
        rc.style.cssText = 'position:fixed;top:0;left:0;width:100vw;height:100vh;pointer-events:none;z-index:99998;';
        rc.width  = pw.innerWidth;
        rc.height = pw.innerHeight;
        pbody.appendChild(rc);
        const rctx = rc.getContext('2d');

        // Rain of gold coins from top
        const coins = [];
        for (let i = 0; i < 80; i++) {{
            coins.push({{
                x: Math.random() * rc.width,
                y: -20 - Math.random() * 200,
                vy: Math.random() * 5 + 3,
                vx: (Math.random() - 0.5) * 2,
                r: Math.random() * 10 + 6,
                life: 1.0,
                decay: 0.005,
                phase: Math.random() * Math.PI * 2
            }});
        }}
        let frame2 = 0;

        function animateReward() {{
            rctx.clearRect(0, 0, rc.width, rc.height);
            let alive = false;

            // Banner
            if (frame2 < 180) {{
                alive = true;
                const bannerAlpha = frame2 < 20 ? frame2/20 : frame2 > 160 ? (180-frame2)/20 : 1;
                rctx.save();
                rctx.globalAlpha = bannerAlpha;
                rctx.fillStyle = 'rgba(15,10,30,0.88)';
                const bw = rc.width * 0.7, bh = 90;
                const bx = rc.width/2 - bw/2, by = rc.height * 0.35;
                rctx.beginPath();
                rctx.roundRect(bx, by, bw, bh, 14);
                rctx.fill();
                rctx.strokeStyle = '#f1c40f';
                rctx.lineWidth = 3;
                rctx.stroke();
                rctx.fillStyle = '#f1c40f';
                rctx.font = 'bold 22px system-ui, sans-serif';
                rctx.textAlign = 'center';
                rctx.shadowColor = '#f1c40f';
                rctx.shadowBlur = 15;
                rctx.fillText('🎁 REWARD UNLOCKED!', rc.width/2, by + 38);
                rctx.shadowBlur = 0;
                rctx.fillStyle = 'white';
                rctx.font = '16px system-ui, sans-serif';
                rctx.fillText(rewardItem.length > 44 ? rewardItem.slice(0,44)+'…' : rewardItem, rc.width/2, by + 66);
                rctx.restore();
            }}

            for (const c of coins) {{
                if (c.y > rc.height + 20 || c.life <= 0) continue;
                alive = true;
                c.x  += c.vx; c.y += c.vy;
                c.phase += 0.15;
                // Coin wobble via scaleX
                const scaleX = Math.abs(Math.cos(c.phase));
                rctx.save();
                rctx.globalAlpha = Math.min(1, (rc.height - c.y) / 80);
                rctx.translate(c.x, c.y);
                rctx.scale(scaleX, 1);
                rctx.beginPath();
                rctx.arc(0, 0, c.r, 0, Math.PI*2);
                rctx.fillStyle = '#f1c40f';
                rctx.shadowColor = '#f1c40f';
                rctx.shadowBlur = 8;
                rctx.fill();
                rctx.fillStyle = '#c9a227';
                rctx.font = `bold ${{Math.floor(c.r * 1.2)}}px sans-serif`;
                rctx.textAlign = 'center';
                rctx.textBaseline = 'middle';
                rctx.shadowBlur = 0;
                rctx.fillText('$', 0, 0);
                rctx.restore();
            }}

            frame2++;
            if (alive && frame2 < 240) requestAnimationFrame(animateReward);
            else rc.remove();
        }}
        animateReward();
    }}

}})();
</script>
"""
components.html(js_code, height=1)

# ─────────────────────────────────────────────
# 7. GOTHAM SKYLINE BANNER
# ─────────────────────────────────────────────
st.markdown("""
<svg viewBox="0 0 900 130" xmlns="http://www.w3.org/2000/svg"
     style="width:100%;display:block;margin-bottom:-8px;">
  <defs>
    <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#0a0a1a"/>
      <stop offset="100%" stop-color="#1a1a3a"/>
    </linearGradient>
  </defs>
  <rect width="900" height="130" fill="url(#sky)"/>
  <!-- Stars -->
  <circle cx="50" cy="15" r="1.2" fill="white" opacity="0.7"/>
  <circle cx="120" cy="8" r="0.9" fill="white" opacity="0.5"/>
  <circle cx="200" cy="20" r="1.1" fill="white" opacity="0.6"/>
  <circle cx="310" cy="10" r="0.8" fill="white" opacity="0.5"/>
  <circle cx="420" cy="5" r="1.3" fill="white" opacity="0.8"/>
  <circle cx="530" cy="18" r="1.0" fill="white" opacity="0.6"/>
  <circle cx="640" cy="8" r="0.9" fill="white" opacity="0.5"/>
  <circle cx="750" cy="14" r="1.2" fill="white" opacity="0.7"/>
  <circle cx="840" cy="6" r="1.0" fill="white" opacity="0.6"/>
  <circle cx="160" cy="30" r="0.7" fill="white" opacity="0.4"/>
  <circle cx="470" cy="28" r="0.7" fill="white" opacity="0.4"/>
  <!-- Moon + bat on moon -->
  <circle cx="820" cy="32" r="22" fill="#ffe066" opacity="0.92"/>
  <polygon points="820,54 760,130 880,130" fill="rgba(241,196,15,0.07)"/>
  <g transform="translate(809,22) scale(0.22)">
    <path d="M50,18 C50,18 43,8 28,12 C18,15 8,22 5,30 C12,26 20,27 25,32 C20,34 14,40 13,48
             C19,41 27,40 33,42 L38,52 C41,57 44,60 50,60 C56,60 59,57 62,52 L67,42
             C73,40 81,41 87,48 C86,40 80,34 75,32 C80,27 88,26 95,30 C92,22 82,15 72,12
             C57,8 50,18 50,18 Z" fill="#1a1a1a" opacity="0.75"/>
  </g>
  <!-- Buildings LEFT -->
  <rect x="0"  y="90" width="28" height="40" fill="#111122"/>
  <rect x="5"  y="80" width="14" height="12" fill="#111122"/>
  <rect x="10" y="70" width="5"  height="12" fill="#111122"/>
  <rect x="30" y="75" width="35" height="55" fill="#0d0d22"/>
  <rect x="38" y="65" width="18" height="12" fill="#0d0d22"/>
  <rect x="44" y="55" width="6"  height="12" fill="#0d0d22"/>
  <rect x="33" y="80" width="4" height="4" fill="#f1c40f" opacity="0.6"/>
  <rect x="42" y="80" width="4" height="4" fill="#f1c40f" opacity="0.3"/>
  <rect x="51" y="80" width="4" height="4" fill="#f1c40f" opacity="0.7"/>
  <rect x="33" y="90" width="4" height="4" fill="#f1c40f" opacity="0.4"/>
  <rect x="67" y="40" width="45" height="90" fill="#0a0a1a"/>
  <rect x="75" y="30" width="28" height="12" fill="#0a0a1a"/>
  <rect x="85" y="18" width="8"  height="14" fill="#0a0a1a"/>
  <rect x="71" y="48" width="5" height="5" fill="#f1c40f" opacity="0.5"/>
  <rect x="81" y="48" width="5" height="5" fill="#fffbe6" opacity="0.4"/>
  <rect x="91" y="48" width="5" height="5" fill="#f1c40f" opacity="0.6"/>
  <rect x="71" y="60" width="5" height="5" fill="#fffbe6" opacity="0.6"/>
  <rect x="91" y="72" width="5" height="5" fill="#f1c40f" opacity="0.7"/>
  <rect x="114" y="60" width="60" height="70" fill="#0d0d22"/>
  <rect x="124" y="50" width="40" height="12" fill="#0d0d22"/>
  <rect x="140" y="38" width="10" height="14" fill="#0d0d22"/>
  <rect x="118" y="65" width="5" height="5" fill="#f1c40f" opacity="0.4"/>
  <rect x="130" y="65" width="5" height="5" fill="#f1c40f" opacity="0.6"/>
  <rect x="142" y="65" width="5" height="5" fill="#fffbe6" opacity="0.5"/>
  <rect x="154" y="78" width="5" height="5" fill="#f1c40f" opacity="0.7"/>
  <rect x="130" y="91" width="5" height="5" fill="#f1c40f" opacity="0.5"/>
  <!-- Wayne Tower (CENTER, tallest) -->
  <rect x="205" y="28" width="55" height="102" fill="#080818"/>
  <rect x="215" y="18" width="35" height="12"  fill="#080818"/>
  <rect x="228" y="4"  width="10" height="16"  fill="#080818"/>
  <circle cx="233" cy="10" r="5" fill="#f1c40f" opacity="0.55"/>
  <rect x="210" y="36" width="6" height="6" fill="#f1c40f" opacity="0.7"/>
  <rect x="222" y="36" width="6" height="6" fill="#fffbe6" opacity="0.5"/>
  <rect x="234" y="36" width="6" height="6" fill="#f1c40f" opacity="0.6"/>
  <rect x="246" y="36" width="6" height="6" fill="#f1c40f" opacity="0.4"/>
  <rect x="210" y="50" width="6" height="6" fill="#fffbe6" opacity="0.5"/>
  <rect x="234" y="50" width="6" height="6" fill="#f1c40f" opacity="0.8"/>
  <rect x="210" y="64" width="6" height="6" fill="#f1c40f" opacity="0.6"/>
  <rect x="246" y="64" width="6" height="6" fill="#f1c40f" opacity="0.7"/>
  <rect x="210" y="78" width="6" height="6" fill="#f1c40f" opacity="0.5"/>
  <rect x="234" y="78" width="6" height="6" fill="#fffbe6" opacity="0.6"/>
  <rect x="222" y="92" width="6" height="6" fill="#f1c40f" opacity="0.4"/>
  <rect x="234" y="106" width="6" height="6" fill="#f1c40f" opacity="0.6"/>
  <!-- Buildings RIGHT -->
  <rect x="262" y="55" width="40" height="75" fill="#0d0d22"/>
  <rect x="270" y="44" width="24" height="13" fill="#0d0d22"/>
  <rect x="265" y="62" width="5" height="5" fill="#f1c40f" opacity="0.5"/>
  <rect x="287" y="75" width="5" height="5" fill="#f1c40f" opacity="0.7"/>
  <rect x="304" y="65" width="30" height="65" fill="#111122"/>
  <rect x="316" y="42" width="6"  height="14" fill="#111122"/>
  <rect x="307" y="72" width="4" height="4" fill="#f1c40f" opacity="0.5"/>
  <rect x="325" y="84" width="4" height="4" fill="#f1c40f" opacity="0.5"/>
  <rect x="543" y="50" width="50" height="80" fill="#080818"/>
  <rect x="564" y="24" width="8"  height="16" fill="#080818"/>
  <rect x="547" y="58" width="6" height="6" fill="#f1c40f" opacity="0.6"/>
  <rect x="570" y="72" width="6" height="6" fill="#f1c40f" opacity="0.6"/>
  <rect x="634" y="45" width="28" height="85" fill="#111133"/>
  <rect x="645" y="18" width="6"  height="17" fill="#111133"/>
  <rect x="637" y="53" width="5" height="5" fill="#f1c40f" opacity="0.6"/>
  <rect x="648" y="79" width="5" height="5" fill="#f1c40f" opacity="0.7"/>
  <rect x="665" y="60" width="55" height="70" fill="#0a0a1a"/>
  <rect x="689" y="34" width="8"  height="16" fill="#0a0a1a"/>
  <rect x="669" y="68" width="6" height="6" fill="#f1c40f" opacity="0.4"/>
  <rect x="693" y="82" width="6" height="6" fill="#f1c40f" opacity="0.4"/>
  <rect x="756" y="55" width="42" height="75" fill="#0d0d22"/>
  <rect x="774" y="28" width="8"  height="17" fill="#0d0d22"/>
  <rect x="759" y="63" width="5" height="5" fill="#f1c40f" opacity="0.6"/>
  <rect x="783" y="76" width="5" height="5" fill="#f1c40f" opacity="0.5"/>
  <rect x="829" y="65" width="35" height="65" fill="#0a0a1a"/>
  <rect x="832" y="73" width="5" height="5" fill="#f1c40f" opacity="0.5"/>
  <rect x="867" y="80" width="33" height="50" fill="#111122"/>
  <rect x="880" y="88" width="4" height="4" fill="#f1c40f" opacity="0.5"/>
  <!-- Ground line + text -->
  <rect x="0" y="125" width="900" height="5" fill="#f1c40f" opacity="0.35"/>
  <text x="450" y="116" text-anchor="middle" font-family="Georgia,serif"
        font-size="11" fill="#f1c40f" opacity="0.45" letter-spacing="6">G O T H A M   C I T Y</text>
</svg>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# 8. HEADER
# ─────────────────────────────────────────────
st.title("🦇 The Dark Knight of Public Health")
st.markdown('<p class="bat-tagline">"Everything\'s impossible until somebody does it."</p>', unsafe_allow_html=True)

q, s = random.choice(BATMAN_QUOTES)
st.markdown(quote_box(q, s, typewriter=True), unsafe_allow_html=True)

# ─────────────────────────────────────────────
# 9. TASK DATABASE
# ─────────────────────────────────────────────
master_tasks = {
    "HBMC Essay": [
        {"id": "#7",  "task": "Clarify clinical vs non-medical; Change LTSS to HCBS",    "pts": 20, "type": "Quick Win"},
        {"id": "#12", "task": "Explain exclusion of hospice (EOL scope)",                 "pts": 30, "type": "Deep Work"},
        {"id": "#13", "task": "Change LTSS to HCBS (home-based focus)",                  "pts": 10, "type": "Quick Win"},
        {"id": "#14", "task": "Define HCBS as non-medical care/regulatory mess",          "pts": 30, "type": "Deep Work"},
        {"id": "#19", "task": "Clarify Clinical/Safety limits for HaH",                  "pts": 25, "type": "Deep Work"},
        {"id": "#20", "task": "Address lack of reimbursement model",                      "pts": 40, "type": "Deep Work"},
        {"id": "#23", "task": "Separate staff travel from broadband",                     "pts": 35, "type": "Deep Work"},
        {"id": "#24", "task": "Define Regulatory & Reimbursement",                        "pts": 20, "type": "Quick Win"},
        {"id": "#25", "task": "Add HBPC billing (philanthropy/FFS)",                      "pts": 30, "type": "Deep Work"},
        {"id": "#29", "task": "Clarify workforce shortages",                              "pts": 30, "type": "Deep Work"},
        {"id": "#30", "task": "Mention HCBS is not required for Medicaid",                "pts": 40, "type": "Deep Work"},
        {"id": "#31", "task": "Add payment models / Fong (2020) reference",               "pts": 30, "type": "Resource Hunt"},
        {"id": "#32", "task": "Spell out acronyms in Fig 1",                              "pts": 10, "type": "Quick Win"}
    ],
    "Climate & Disaster": [
        {"id": "#37", "task": "Add disruption of Meals on Wheels",                        "pts": 25, "type": "Deep Work"},
        {"id": "#38", "task": "Incorporate CARA model",                                   "pts": 50, "type": "Deep Work"},
        {"id": "#39", "task": "Successful Aging -> Optimal Aging",                        "pts": 40, "type": "Deep Work"},
        {"id": "#40", "task": "Define Resilience Theory",                                 "pts": 20, "type": "Quick Win"},
        {"id": "#41", "task": "Policies shaping disaster response",                       "pts": 45, "type": "Deep Work"},
        {"id": "#42", "task": "Define Mental Health Impacts",                             "pts": 20, "type": "Quick Win"},
        {"id": "#44", "task": "Add FL/PR hurricane examples",                             "pts": 25, "type": "Deep Work"},
        {"id": "#45", "task": "Specify vulnerabilities",                                  "pts": 25, "type": "Deep Work"},
        {"id": "#49", "task": "Update social isolation (Sue Ann Bell)",                   "pts": 35, "type": "Resource Hunt"},
        {"id": "#50", "task": "Add nursing home examples (FL)",                           "pts": 30, "type": "Deep Work"},
        {"id": "#52", "task": "Cite David Dosa's 4Ms work",                               "pts": 30, "type": "Resource Hunt"},
        {"id": "#54", "task": "Add policy pieces: laws/resources",                        "pts": 50, "type": "Deep Work"},
        {"id": "#55", "task": "Define level of intervention",                             "pts": 40, "type": "Deep Work"},
        {"id": "#58", "task": "Introduce industry siloing earlier",                       "pts": 30, "type": "Deep Work"},
        {"id": "#59", "task": "Infrastructure/Policy categorization",                     "pts": 30, "type": "Deep Work"},
        {"id": "#62", "task": "Add location to Harvey row",                               "pts": 10, "type": "Quick Win"},
        {"id": "#63", "task": "Add equity component (FL vs PR)",                          "pts": 35, "type": "Deep Work"}
    ],
    "Delphi & Policy": [
        {"id": "#65", "task": "Parallelize aging statistics",                             "pts": 15, "type": "Quick Win"},
        {"id": "#71", "task": "Cite 5Ts Framework",                                      "pts": 35, "type": "Resource Hunt"},
        {"id": "#85", "task": "Cite Daniel Beland (SCPA)",                                "pts": 30, "type": "Resource Hunt"},
        {"id": "#89", "task": "Focus on US State-level examples",                         "pts": 60, "type": "Deep Work"},
        {"id": "#92", "task": "Cite ASPR Toolkit",                                        "pts": 45, "type": "Resource Hunt"}
    ]
}

lab_context = {
    "#31": {
        "comment": "Add payment/reimbursement — shift to value-based care and Medicaid rebalancing. Cite Fong (2020).",
        "prefill": "Connect lack of standard billing for home-based care to the broader shift toward value-based models, using Fong (2020) paper."
    },
    "#30": {
        "comment": "Mention HCBS is not required for state Medicaid plans; states operate on waivers likely to be cut.",
        "prefill": "Added section clarifying that HCBS is an optional benefit and not a mandatory requirement for state Medicaid plans."
    }
}
# Maps each comps section to its relevant task IDs
SECTION_TASKS = {
    "Introduction to HBMC": ["#7", "#13", "#14", "#32"],
    "Historical Context": ["#7", "#13"],
    "Who Needs HBMC and Why": ["#7", "#14", "#29"],
    "Models of Home-Based Medical Care": ["#12", "#13", "#14", "#19", "#23", "#32"],
    "Economic and Clinical Impact": ["#20", "#24", "#25", "#31"],
    "Advantages of HBMC": ["#20", "#24", "#25"],
    "Disadvantages of HBMC": ["#19", "#20", "#24", "#25", "#29", "#30"],
    "Successful Aging": ["#39"],
    "Systems Theory and the Socio-ecological Model": ["#38", "#40", "#55"],
    "Physiological Vulnerabilities": ["#45", "#42"],
    "Mental Health Impacts": ["#42", "#49"],
    "Home Loss, Displacement, and Institutionalization": ["#44", "#50", "#52", "#63"],
    "Preparedness Frameworks": ["#38", "#41", "#54", "#58", "#59", "#65", "#71", "#92"],
    "4.2 Scaling Down and Relevant Units of Analysis": ["#85", "#89"],
    "4.3 Variation Under a Shared Federal Framework": ["#85", "#89"],
    "4.4 Causal Complexity in HBMC Emergency Preparedness": ["#85", "#89"],
    "Conclusion (SCPA)": ["#85", "#89"],
}

# Invert SECTION_TASKS: task_id -> [section, ...] — used by sidebar and tabs
task_to_sections = {}
for _st_title, _st_ids in SECTION_TASKS.items():
    for _tid in _st_ids:
        task_to_sections.setdefault(_tid, []).append(_st_title)

# ─────────────────────────────────────────────
# 10. SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.header("🦇 Bat-Computer")
    st.metric("Total XP", st.session_state.xp)
    render_rank_badge(st.session_state.xp)

    with st.expander("⚠️ Reset XP"):
        st.warning("This will set your XP back to 0. This cannot be undone.")
        if st.button("Reset XP to 0", type="primary"):
            st.session_state.xp = 0
            get_db().update_one({"_id": "progress"}, {"$set": {"xp": 0}}, upsert=True)
            st.success("XP reset to 0.")
            st.rerun()

    total_tasks = sum(len(v) for v in master_tasks.values())
    completed_count = len(st.session_state.completed_tasks)
    progress_pct = completed_count / total_tasks if total_tasks > 0 else 0
    st.write(f"**Comps Completion: {int(progress_pct * 100)}%**")
    st.progress(progress_pct)
    st.divider()

    with st.expander("📊 Section Breakdown"):
        for cat, items in master_tasks.items():
            cat_total = len(items)
            cat_done = sum(1 for i in items if i['id'] in st.session_state.completed_tasks)
            st.write(f"{cat}: {cat_done}/{cat_total}")
            st.progress(cat_done / cat_total if cat_total else 0)

    st.divider()
    sq, ss = random.choice(BATMAN_QUOTES)
    st.markdown(
        f'<div style="background:#1a1a2e;border-left:3px solid #f1c40f;border-radius:6px;'
        f'padding:10px;color:#f0e6c8;font-style:italic;font-size:0.82rem;">'
        f'&ldquo;{sq}&rdquo;'
        f'<div style="color:#f1c40f;font-size:0.72rem;font-style:normal;margin-top:4px;">— {ss}</div>'
        f'</div>',
        unsafe_allow_html=True
    )
    st.divider()

    all_tasks_flat = [
        f"{i['id']}: {i['task']}"
        for cat in master_tasks.values()
        for i in cat
        if i['id'] not in st.session_state.completed_tasks
    ]
    selected_mission = st.selectbox("🎯 Current Focus Task:", ["General Deep Work"] + all_tasks_flat)

    @st.fragment(run_every="1s")
    def sidebar_pomodoro():
        if st.session_state.get('timer_running') and st.session_state.get('target_time'):
            if not st.session_state.get('timer_paused'):
                remaining = st.session_state.target_time - datetime.now()
                total_seconds = int(remaining.total_seconds())
                if total_seconds > 0:
                    mins, secs = divmod(total_seconds, 60)
                    label = f"⏳ Slaying: {selected_mission.split(':')[0]}"
                    if mins < 5:
                        label = f"🔥 FINAL PUSH: {selected_mission.split(':')[0]}"
                    st.metric(label, f"{mins:02d}:{secs:02d}")
                else:
                    st.session_state.timer_running = False
                    task_id = selected_mission.split(":")[0]
                    st.session_state.task_timers[task_id] = \
                        st.session_state.task_timers.get(task_id, 0) + 25
                    st.session_state.xp += 25
                    st.session_state.pomodoro_done = True
                    save_all_progress()
                    st.balloons()
                    st.rerun()
            else:
                st.warning("⏸️ Timer paused")

            # Pause/Resume + Stop buttons inside fragment
            p_col1, p_col2 = st.columns(2)
            if st.session_state.get('timer_paused'):
                if p_col1.button("▶️ Resume", use_container_width=True, key="resume_btn"):
                    paused_duration = datetime.now() - st.session_state.pause_start
                    st.session_state.target_time += paused_duration
                    st.session_state.timer_paused = False
                    st.rerun()
            else:
                if p_col1.button("⏸️ Pause", use_container_width=True, key="pause_btn"):
                    st.session_state.timer_paused = True
                    st.session_state.pause_start = datetime.now()
                    st.rerun()

            if p_col2.button("🛑 Stop & Save", use_container_width=True, key="stop_btn"):
                if st.session_state.get('target_time'):
                    elapsed_mins = int((datetime.now() - (st.session_state.target_time - timedelta(minutes=25))).total_seconds() / 60)
                    if elapsed_mins > 0:
                        task_id = selected_mission.split(":")[0]
                        st.session_state.task_timers[task_id] = \
                            st.session_state.task_timers.get(task_id, 0) + elapsed_mins
                        st.session_state.xp += elapsed_mins
                        st.session_state.celebration_xp = elapsed_mins
                        save_all_progress()
                        st.success(f"Saved {elapsed_mins}m! +{elapsed_mins} XP")
                st.session_state.timer_running = False
                st.session_state.timer_paused = False
                st.session_state.target_time = None
                st.rerun()
    sidebar_pomodoro()

    if not st.session_state.get('timer_running'):
        if st.button("🚀 Start 25m Sprint", use_container_width=True):
                st.session_state.target_time = datetime.now() + timedelta(minutes=25)
                st.session_state.timer_running = True
                st.session_state.timer_paused = False
                st.rerun()
        else:
            p_col1, p_col2 = st.columns(2)
            if st.session_state.get('timer_paused'):
                if p_col1.button("▶️ Resume", use_container_width=True):
                    paused_duration = datetime.now() - st.session_state.pause_start
                    st.session_state.target_time += paused_duration
                    st.session_state.timer_paused = False
                    st.rerun()
            else:
                if p_col1.button("⏸️ Pause", use_container_width=True):
                    st.session_state.timer_paused = True
                    st.session_state.pause_start = datetime.now()
                    st.rerun()

            if p_col2.button("🛑 Stop & Save", use_container_width=True):
                if st.session_state.get('target_time'):
                    elapsed_mins = int((datetime.now() - (st.session_state.target_time - timedelta(minutes=25))).total_seconds() / 60)
                    if elapsed_mins > 0:
                        task_id = selected_mission.split(":")[0]
                        st.session_state.task_timers[task_id] = \
                            st.session_state.task_timers.get(task_id, 0) + elapsed_mins
                        st.session_state.xp += elapsed_mins
                        st.session_state.celebration_xp = elapsed_mins
                        save_all_progress()
                        st.success(f"Saved {elapsed_mins}m! +{elapsed_mins} XP")
                st.session_state.timer_running = False
                st.session_state.timer_paused = False
                st.session_state.target_time = None
                st.rerun()

    st.divider()
    st.subheader("📓 Response Lab")
    last_section = st.session_state.get("last_worked_section", "")
    last_date = st.session_state.get("last_worked_date", "")
    if last_section:
        st.markdown(
            f'<div style="background:#1a1a2e;border-left:3px solid #f1c40f;border-radius:6px;'
            f'padding:10px 12px;color:#f0e6c8;font-size:0.83rem;">'
            f'<b style="color:#f1c40f;">Last worked on:</b><br>'
            f'{last_section}<br>'
            f'<span style="color:#aaa;font-size:0.78rem;">🕐 {last_date}</span>'
            f'</div>',
            unsafe_allow_html=True
        )
    else:
        st.caption("No drafts saved yet.")

    st.divider()
    if st.button("💾 Force Manual Save"):
        save_all_progress()
        st.success("Data Secured! 🦇")
    st.divider()
    st.subheader("📝 Writing Toolkit")
    
    toolkit_tab = st.radio(
        "Tool:",
        ["🔄 Synonyms", "📋 Templates"],
        horizontal=True,
        key="toolkit_tab"
    )
    
    if toolkit_tab == "🔄 Synonyms":
        word_input = st.text_input(
            "Word or phrase:",
            placeholder="e.g. 'shows' or 'important'",
            key="synonym_input"
        )
        
        QUICK_SYNONYMS = {
            "shows": ["demonstrates", "reveals", "indicates", "illustrates", "evidences"],
            "important": ["critical", "essential", "paramount", "pivotal", "salient"],
            "used": ["utilized", "employed", "applied", "leveraged", "implemented"],
            "found": ["identified", "observed", "determined", "established", "documented"],
            "increase": ["amplify", "augment", "expand", "escalate", "elevate"],
            "decrease": ["diminish", "attenuate", "reduce", "mitigate", "decline"],
            "many": ["numerous", "substantial", "considerable", "extensive", "myriad"],
            "because": ["given that", "owing to", "in light of", "as a result of", "stemming from"],
            "but": ["however", "nevertheless", "notwithstanding", "conversely", "yet"],
            "also": ["furthermore", "additionally", "moreover", "in addition", "similarly"],
            "says": ["argues", "contends", "posits", "asserts", "maintains"],
            "help": ["facilitate", "support", "advance", "bolster", "undergird"],
            "show": ["demonstrate", "reveal", "illustrate", "highlight", "elucidate"],
            "need": ["require", "necessitate", "demand", "warrant", "call for"],
            "get": ["obtain", "acquire", "attain", "yield", "generate"],
            "use": ["employ", "utilize", "apply", "leverage", "harness"],
            "big": ["substantial", "considerable", "significant", "pronounced", "marked"],
            "small": ["minimal", "modest", "marginal", "limited", "negligible"],
            "problem": ["challenge", "barrier", "impediment", "limitation", "constraint"],
            "change": ["transformation", "shift", "transition", "modification", "evolution"],
        }
        
        if word_input:
            word_lower = word_input.lower().strip()
            if word_lower in QUICK_SYNONYMS:
                st.markdown("**Academic alternatives:**")
                for syn in QUICK_SYNONYMS[word_lower]:
                    st.markdown(
                        f'<div style="background:#1a1a2e;border-left:2px solid #f1c40f;'
                        f'padding:4px 10px;border-radius:4px;color:#f0e6c8;'
                        f'font-size:0.85rem;margin:2px 0;">• {syn}</div>',
                        unsafe_allow_html=True
                    )
            else:
                if st.button("🦇 AI Synonyms", use_container_width=True, key="ai_syn_btn"):
                    with st.spinner("Finding alternatives..."):
                        try:
                            import anthropic
                            client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
                            message = client.messages.create(
                                model="claude-sonnet-4-20250514",
                                max_tokens=200,
                                messages=[{"role": "user", "content": f"""Give 6 academic synonyms for "{word_input}" suitable for a public health dissertation. 
Return ONLY a numbered list, no explanation:
1. word — brief context note
2. word — brief context note
...etc"""}]
                            )
                            st.markdown(
                                f'<div style="background:#1a1a2e;border-left:2px solid #f1c40f;'
                                f'padding:8px 12px;border-radius:6px;color:#f0e6c8;font-size:0.83rem;">'
                                f'{message.content[0].text}</div>',
                                unsafe_allow_html=True
                            )
                        except Exception as e:
                            st.error(f"Failed: {e}")

    else:  # Templates
        TEMPLATES = {
            "🔗 Gap Statement": "While [existing literature] has established [X], less attention has been paid to [Y]. This gap is particularly salient given [context], suggesting a need for [your contribution].",
            "⚖️ Contrast": "In contrast to [X], [Y] demonstrates [difference]. This distinction is consequential because [implication].",
            "📊 Citing Evidence": "[Finding] (Author, Year). This suggests that [your interpretation], with implications for [policy/practice/theory].",
            "🎯 Topic Sentence": "[This section/paper/study] argues that [claim], drawing on [evidence/framework] to demonstrate [contribution].",
            "🔄 Transition": "Having established [previous point], this [section/paper] turns to [next point], examining how [connection].",
            "⚡ Policy Implication": "These findings suggest that [policy recommendation], particularly for [specific population] in [context]. Implementation would require [action] by [actors].",
            "🌍 Equity Framing": "The disproportionate impact on [population] reflects [structural factor], underscoring the need for [equity-focused intervention].",
            "📝 Methods Justification": "[Method] was selected because [rationale]. This approach is particularly appropriate for [research question] given [justification]. A limitation of this method is [limitation], which was addressed by [mitigation].",
            "🏁 Conclusion Move": "This [paper/section] has argued that [main claim]. By [contribution], this work advances [field] and has implications for [policy/practice]. Future research should examine [next steps].",
        }

        selected_template = st.selectbox(
            "Template type:",
            list(TEMPLATES.keys()),
            key="template_select"
        )

        st.markdown(
            f'<div style="background:#1a1a2e;border-left:3px solid #f1c40f;'
            f'border-radius:6px;padding:10px 12px;color:#f0e6c8;'
            f'font-size:0.82rem;margin:6px 0;line-height:1.6;">'
            f'{TEMPLATES[selected_template]}</div>',
            unsafe_allow_html=True
        )

        if st.button("📋 Copy Template", use_container_width=True, key="copy_template_btn"):
            st.code(TEMPLATES[selected_template])
            st.caption("Select all and copy from the box above!")
    st.divider()

    # ── Sidebar Focus Clock ──
    st.subheader("⏱️ Focus Timer")
    _clock_section = st.session_state.get("focus_section_select", "")
    _clock_reviewer = st.session_state.get("focus_reviewer_select", "All")

    # Rebuild items for the current focus section
    _clock_items = []
    if _clock_section:
        _seg_colors = {"high": "#e74c3c", "medium": "#f39c12", "low": "#27ae60", "none": "#2ecc71"}
        _emily_ctx = [
            {"reviewer": "Emily", "feedback": c["comment"],
             "estimated_minutes": 15, "priority": "high"}
            for tid, c in lab_context.items()
            if _clock_section in task_to_sections.get(tid, [])
        ]
        _emma_ctx = []
        try:
            _emma_ctx = list(get_mongo_db()["comps_feedback"].find(
                {"section": _clock_section}, {"_id": 0}
            ))
        except:
            pass
        if _clock_reviewer in ("All", "Emily"):
            _clock_items += _emily_ctx
        if _clock_reviewer in ("All", "Emma Tsui"):
            _clock_items += _emma_ctx

    _segments = []
    for _item in _clock_items:
        _mins = _item.get("estimated_minutes", 0) or 0
        if _mins > 0:
            _segments.append({
                "label": (_item.get("feedback","")[:35] + "...") if len(_item.get("feedback","")) > 35 else _item.get("feedback",""),
                "minutes": _mins,
                "color": _seg_colors.get(_item.get("priority","medium"), "#f39c12"),
                "reviewer": _item.get("reviewer", "Emily"),
            })

    import json as _json
    _seg_json = _json.dumps(_segments)
    _total_mins = sum(s["minutes"] for s in _segments)
    _total_secs = _total_mins * 60

    components.html(f"""
<!DOCTYPE html><html><head>
<style>
  body {{ margin:0; background:transparent; font-family:Arial,sans-serif;
         display:flex; flex-direction:column; align-items:center; padding:8px 0; }}
  canvas {{ display:block; }}
  .controls {{ display:flex; gap:8px; margin-top:10px; }}
  button {{ padding:6px 16px; border:none; border-radius:16px; cursor:pointer;
            font-size:0.8rem; font-weight:bold; }}
  #startBtn {{ background:#f1c40f; color:#1a1a2e; }}
  #resetBtn {{ background:#2c3e50; color:#f0e6c8; }}
  #timeDisplay {{ font-size:1.4rem; font-weight:bold; color:#f1c40f;
                  margin-top:6px; letter-spacing:2px; }}
  #currentItem {{ font-size:0.7rem; color:#aaa; margin-top:3px;
                  max-width:220px; text-align:center; min-height:16px; }}
  .legend {{ display:flex; flex-wrap:wrap; gap:4px; justify-content:center;
             margin-top:8px; max-width:240px; }}
  .leg-item {{ display:flex; align-items:center; gap:3px; font-size:0.65rem; color:#ccc; }}
  .leg-dot {{ width:8px; height:8px; border-radius:50%; flex-shrink:0; }}
</style></head><body>
<canvas id="clock" width="220" height="220"></canvas>
<div id="timeDisplay">{"--:--" if not _segments else f"{_total_mins:02d}:00"}</div>
<div id="currentItem">{"Select a section in Focus tab" if not _segments else f"{len(_segments)} items · {_total_mins} min"}</div>
<div class="controls">
  <button id="startBtn" onclick="toggleTimer()">▶ Start</button>
  <button id="resetBtn" onclick="resetTimer()">↺ Reset</button>
</div>
<div class="legend" id="legend"></div>
<script>
const canvas = document.getElementById('clock');
const ctx = canvas.getContext('2d');
const cx = 110, cy = 110, R = 96, r_inner = 58;
const segments = {_seg_json};
const totalSecs = {_total_secs};
let elapsed = 0, running = false, interval = null, lastTs = null;

const legend = document.getElementById('legend');
segments.forEach(s => {{
  const d = document.createElement('div'); d.className = 'leg-item';
  d.innerHTML = `<div class="leg-dot" style="background:${{s.color}}"></div><span>${{s.reviewer}}: ${{s.minutes}}m</span>`;
  legend.appendChild(d);
}});

function drawClock() {{
  ctx.clearRect(0,0,220,220);
  ctx.beginPath(); ctx.arc(cx,cy,R+6,0,Math.PI*2);
  ctx.fillStyle='#0a0a1a'; ctx.fill();

  const total = segments.reduce((a,s)=>a+s.minutes,0)||1;
  let sa = -Math.PI/2;
  segments.forEach((seg,i) => {{
    const sweep=(seg.minutes/total)*Math.PI*2, ea=sa+sweep;
    const segStart=segments.slice(0,i).reduce((a,s)=>a+s.minutes,0)*60;
    const alpha = elapsed>=segStart+seg.minutes*60 ? 0.2 : 1.0;
    ctx.beginPath(); ctx.moveTo(cx,cy); ctx.arc(cx,cy,R,sa,ea); ctx.closePath();
    ctx.fillStyle=seg.color+Math.round(alpha*255).toString(16).padStart(2,'0'); ctx.fill();
    sa=ea;
  }});

  ctx.beginPath(); ctx.arc(cx,cy,r_inner,0,Math.PI*2);
  ctx.fillStyle='#0a0a1a'; ctx.fill();

  if(elapsed>0&&totalSecs>0){{
    const prog=Math.min(elapsed/totalSecs,1);
    ctx.beginPath(); ctx.arc(cx,cy,r_inner+5,-Math.PI/2,-Math.PI/2+prog*Math.PI*2);
    ctx.strokeStyle='#f1c40f'; ctx.lineWidth=3; ctx.stroke();
  }}

  if(totalSecs>0){{
    const ha=-Math.PI/2+(elapsed/totalSecs)*Math.PI*2;
    ctx.beginPath(); ctx.moveTo(cx,cy);
    ctx.lineTo(cx+R*Math.cos(ha),cy+R*Math.sin(ha));
    ctx.strokeStyle='#fff'; ctx.lineWidth=2;
    ctx.shadowColor='#f1c40f'; ctx.shadowBlur=5; ctx.stroke(); ctx.shadowBlur=0;
    ctx.beginPath(); ctx.arc(cx+R*Math.cos(ha),cy+R*Math.sin(ha),3,0,Math.PI*2);
    ctx.fillStyle='#f1c40f'; ctx.fill();
  }}

  ctx.beginPath(); ctx.arc(cx,cy,4,0,Math.PI*2);
  ctx.fillStyle='#f1c40f'; ctx.fill();

  const rem=Math.max(0,totalSecs-elapsed);
  const m=Math.floor(rem/60).toString().padStart(2,'0');
  const s=Math.floor(rem%60).toString().padStart(2,'0');
  document.getElementById('timeDisplay').textContent=m+':'+s;

  let cum=0, label=elapsed>=totalSecs?'✅ Done!':'';
  for(let i=0;i<segments.length;i++){{
    cum+=segments[i].minutes*60;
    if(elapsed<cum){{label=segments[i].reviewer+': '+segments[i].label; break;}}
  }}
  document.getElementById('currentItem').textContent=label;

  if(elapsed>=totalSecs&&totalSecs>0){{
    ctx.beginPath(); ctx.arc(cx,cy,r_inner-8,0,Math.PI*2);
    ctx.fillStyle='#2ecc7133'; ctx.fill();
  }}
}}

function toggleTimer(){{
  const btn=document.getElementById('startBtn');
  if(running){{ running=false; clearInterval(interval); btn.textContent='▶ Resume'; }}
  else{{
    if(elapsed>=totalSecs) return;
    running=true; lastTs=Date.now();
    interval=setInterval(()=>{{
      const now=Date.now(); elapsed+=(now-lastTs)/1000; lastTs=now;
      if(elapsed>=totalSecs){{ elapsed=totalSecs; running=false; clearInterval(interval); btn.textContent='✅ Done'; }}
      drawClock();
    }},100);
    btn.textContent='⏸ Pause';
  }}
}}
function resetTimer(){{
  running=false; clearInterval(interval); elapsed=0;
  document.getElementById('startBtn').textContent='▶ Start'; drawClock();
}}
drawClock();
</script></body></html>
""", height=380)

    st.divider()
    st.subheader("🦇 Dissertation Coach")

    # ── Build full ordered section list ──
    _wt_sections = list(SECTION_TASKS.keys())
    try:
        _emma_secs = list(get_mongo_db()["comps_feedback"].distinct("section"))
        for s in _emma_secs:
            if s not in _wt_sections:
                _wt_sections.append(s)
    except:
        pass

    # ── Walkthrough state ──
    if "walkthrough_active" not in st.session_state:
        st.session_state.walkthrough_active = False
    if "walkthrough_idx" not in st.session_state:
        st.session_state.walkthrough_idx = 0
    if "walkthrough_introduced" not in st.session_state:
        st.session_state.walkthrough_introduced = -1
    if "coach_messages" not in st.session_state:
        st.session_state.coach_messages = []

    wt_active = st.session_state.walkthrough_active
    wt_idx = st.session_state.walkthrough_idx
    wt_idx = min(wt_idx, len(_wt_sections) - 1)
    current_wt_sec = _wt_sections[wt_idx] if _wt_sections else ""

    # ── Walkthrough controls ──
    if not wt_active:
        if st.button("🗺️ Start Guided Walkthrough", use_container_width=True, key="wt_start"):
            st.session_state.walkthrough_active = True
            st.session_state.walkthrough_idx = 0
            st.session_state.walkthrough_introduced = -1
            st.session_state.coach_messages = []
            st.session_state.focus_section_select = _wt_sections[0] if _wt_sections else ""
            st.rerun()
        _focus_sec = st.session_state.get("focus_section_select", "")
        if _focus_sec:
            st.caption(f"📍 {_focus_sec}")
        else:
            st.caption("General mode — or start a guided walkthrough above")
    else:
        # Section header
        st.markdown(
            f'<div style="background:#1a1a2e;border:1px solid #f1c40f;border-radius:8px;'
            f'padding:8px 12px;margin-bottom:6px;">'
            f'<span style="color:#f1c40f;font-size:0.72rem;">SECTION {wt_idx+1} / {len(_wt_sections)}</span><br>'
            f'<b style="color:#f0e6c8;font-size:0.85rem;">{current_wt_sec}</b>'
            f'</div>',
            unsafe_allow_html=True
        )

        # Progress bar
        st.progress((wt_idx) / len(_wt_sections))

        nav1, nav2, nav3 = st.columns(3)
        if nav1.button("◀ Prev", key="wt_prev", use_container_width=True, disabled=(wt_idx == 0)):
            st.session_state.walkthrough_idx -= 1
            st.session_state.coach_messages = []
            st.session_state.walkthrough_introduced = -1
            st.session_state.focus_section_select = _wt_sections[st.session_state.walkthrough_idx]
            st.rerun()
        if nav2.button("Next ▶", key="wt_next", use_container_width=True, disabled=(wt_idx >= len(_wt_sections)-1)):
            st.session_state.walkthrough_idx += 1
            st.session_state.coach_messages = []
            st.session_state.walkthrough_introduced = -1
            st.session_state.focus_section_select = _wt_sections[st.session_state.walkthrough_idx]
            st.rerun()
        if nav3.button("✖ End", key="wt_end", use_container_width=True):
            st.session_state.walkthrough_active = False
            st.session_state.coach_messages = []
            st.rerun()

        # Auto-generate intro when entering a new section
        if st.session_state.walkthrough_introduced != wt_idx:
            with st.spinner("🦇 Coach is preparing your briefing..."):
                try:
                    import anthropic
                    client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])

                    _fb_items = [
                        {"reviewer": "Emily", "feedback": c["comment"],
                         "priority": "high", "action_type": "substantive"}
                        for tid, c in lab_context.items()
                        if current_wt_sec in task_to_sections.get(tid, [])
                    ]
                    try:
                        _fb_items += list(get_mongo_db()["comps_feedback"].find(
                            {"section": current_wt_sec}, {"_id": 0}
                        ))
                    except:
                        pass
                    _fb_ctx = "\n".join(
                        f"- [{i.get('reviewer','?')}] ({i.get('priority','?')} priority, ~{i.get('estimated_minutes','?')}min) {i.get('feedback','')}"
                        for i in _fb_items
                    ) or "No specific feedback items found."
                    _draft = st.session_state.saved_responses.get(f"focus_draft_{current_wt_sec}", "")

                    _draft_preview = ("Their current draft:\n" + _draft[:300]) if _draft else "No draft written yet."
                    _intro_prompt = (
                        f"You are a dissertation writing coach walking a PhD student through their comprehensive exam revisions section by section. "
                        f"They have their Google Doc open and are ready to edit.\n\n"
                        f"Section: **{current_wt_sec}** ({wt_idx+1} of {len(_wt_sections)})\n\n"
                        f"Committee feedback:\n{_fb_ctx}\n\n"
                        f"{_draft_preview}\n\n"
                        f"In 3-5 sentences: introduce this section, highlight the 1-2 most important feedback items to tackle first, "
                        f"and give one concrete suggestion for how to start. Be direct and doctoral-level. "
                        f"End with a Batman-themed encouragement. Keep it brief — this is a sidebar."
                    )
                    intro_response = client.messages.create(
                        model="claude-sonnet-4-20250514",
                        max_tokens=400,
                        messages=[{"role": "user", "content": _intro_prompt}]
                    )
                    intro_text = intro_response.content[0].text
                    st.session_state.coach_messages = [{"role": "assistant", "content": intro_text}]
                    st.session_state.walkthrough_introduced = wt_idx
                    st.rerun()
                except Exception as e:
                    st.session_state.walkthrough_introduced = wt_idx
                    st.error(f"Intro failed: {e}")

    # ── Chat history ──
    for msg in st.session_state.coach_messages[-6:]:
        if msg["role"] == "user":
            st.markdown(
                f'<div style="background:#1a1a2e;border-left:3px solid #f1c40f;'
                f'border-radius:6px;padding:8px 12px;color:#f0e6c8;'
                f'font-size:0.82rem;margin:4px 0;">👤 {msg["content"]}</div>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f'<div style="background:#0d2b0d;border-left:3px solid #2ecc71;'
                f'border-radius:6px;padding:8px 12px;color:#d5f5e3;'
                f'font-size:0.82rem;margin:4px 0;">🦇 {msg["content"]}</div>',
                unsafe_allow_html=True
            )

    coach_input = st.text_area(
        "Ask your coach:",
        placeholder="Ask a follow-up, paste a paragraph to review, or say 'next' to move on...",
        key="coach_input",
        height=80
    )

    coach_col1, coach_col2 = st.columns(2)

    if coach_col1.button("💬 Send", use_container_width=True, key="coach_send"):
        if coach_input:
            st.session_state.coach_messages.append({"role": "user", "content": coach_input})
            with st.spinner("🦇 Thinking..."):
                try:
                    import anthropic
                    client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])

                    _focus_sec = current_wt_sec if wt_active else st.session_state.get("focus_section_select", "")
                    _fb_items = [
                        {"reviewer": "Emily", "feedback": c["comment"]}
                        for tid, c in lab_context.items()
                        if _focus_sec in task_to_sections.get(tid, [])
                    ]
                    try:
                        _fb_items += list(get_mongo_db()["comps_feedback"].find({"section": _focus_sec}, {"_id": 0}))
                    except:
                        pass
                    _fb_ctx = "\n".join(f"- [{i.get('reviewer','?')}] {i.get('feedback','')}" for i in _fb_items)
                    _draft = st.session_state.saved_responses.get(f"focus_draft_{_focus_sec}", "")

                    system_prompt = f"""You are an expert dissertation writing coach walking a PhD student through their comprehensive exam revisions. They have their Google Doc open.

{"GUIDED WALKTHROUGH MODE — Section " + str(wt_idx+1) + " of " + str(len(_wt_sections)) if wt_active else ""}
Current section: **{_focus_sec}**

Committee feedback:
{_fb_ctx if _fb_ctx else "None loaded."}

{"Student's draft:\n" + _draft if _draft else "No draft yet."}

Be direct, specific, doctoral-level. Keep responses concise — this is a sidebar. Use Batman metaphors occasionally."""

                    response = client.messages.create(
                        model="claude-sonnet-4-20250514",
                        max_tokens=500,
                        system=system_prompt,
                        messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.coach_messages[-10:]]
                    )
                    st.session_state.coach_messages.append({"role": "assistant", "content": response.content[0].text})
                    st.rerun()
                except Exception as e:
                    st.error(f"Coach failed: {e}")
        else:
            st.warning("Type something first!")

    if coach_col2.button("🗑️ Clear", use_container_width=True, key="coach_clear"):
        st.session_state.coach_messages = []
        st.session_state.walkthrough_introduced = -1
        st.rerun()

# ─────────────────────────────────────────────
# 11. TABS
# ─────────────────────────────────────────────
t1, t2, t3, t4, t5, t6, t7 = st.tabs([
    "⚔️ Task Board", "📓 Response Lab", "🎁 Rewards & Analytics", "📜 Writing Guide", "🎓 Comps Review", "🧠 Mind Map", "🎯 Focus"
])

# ── TAB 1: TASK BOARD ──────────────────────
with t1:
    st.header("⚔️ Task Board: Gotham Missions")
    
    # 1. Random Batman Quote
    q2, s2 = random.choice(BATMAN_QUOTES)
    st.markdown(quote_box(q2, s2), unsafe_allow_html=True)

    # 2. Rank & XP Display
    _, rank_title, rank_color = get_rank(st.session_state.xp)
    st.markdown(
        f'<div style="display:inline-block;padding:6px 16px;border-radius:20px;'
        f'font-weight:bold;border:2px solid {rank_color};background:{rank_color}22;'
        f'color:{rank_color};margin-bottom:12px;">'
        f'Current Rank: {rank_title} — {st.session_state.xp} XP</div>',
        unsafe_allow_html=True
    )

    # 3. Triage Radio
    triage = st.radio(
        "Triage Level:", ["All Missions", "Quick Win", "Resource Hunt", "Deep Work"],
        horizontal=True
    )
    st.divider()

    # 4. THE MISSION LOOP (The Engine)
    for category, missions in master_tasks.items():
        filtered = [m for m in missions if triage == "All Missions" or m['type'] == triage]
        
        if filtered:
            st.subheader(f"📁 {category}")
            
            for m in filtered:
                c1, c2 = st.columns([4, 1])
                is_done = m['id'] in st.session_state.completed_tasks
                type_icon = {"Quick Win": "⚡", "Deep Work": "🔬", "Resource Hunt": "🔍"}.get(m['type'], "🎯")

                # COLUMN 1: Task Description
                if is_done:
                    c1.markdown(f'<div style="color:#888;text-decoration:line-through;">✅ {m["id"]}: {m["task"]}</div>', unsafe_allow_html=True)
                else:
                    c1.write(f"{type_icon} **{m['id']}**: {m['task']} *(+{m['pts']} XP)*")

                # COLUMN 2: The Slay/Undo Button
                if c2.button("Slay/Undo", key=f"btn_{m['id']}", use_container_width=True):
                    if is_done:
                        # UNDO: Remove from completed & subtract XP
                        st.session_state.completed_tasks.remove(m['id'])
                        st.session_state.xp -= m['pts']
                    else:
                        # COMPLETE: Add to completed & award XP (once)
                        st.session_state.completed_tasks.add(m['id'])
                        st.session_state.xp += m['pts']  # Fixed: was adding XP twice
                        
                        # Trigger visuals (The "Bat Flash")
                        # COMPLETE: Add to completed & award XP
                        st.session_state.completed_tasks.add(m['id'])
                        st.session_state.xp += m['pts']
                        st.session_state.play_audio = True  # ← flag audio to play on rerun
                        st.toast(f"Justice Served! +{m['pts']} XP", icon="🦇")

                        # Save & Refresh
                        save_all_progress()
                        st.rerun()
                        st.toast(f"Justice Served! +{m['pts']} XP", icon="🦇")
                        time.sleep(30)
                    
                    # Save & Refresh
                    save_all_progress()
                    st.rerun()  # Fixed: was missing ()
# ── TAB 2: RESPONSE LAB ────────────────────
with t2:
    st.header("📓 Strategic Response Lab")
    q3, s3 = random.choice(BATMAN_QUOTES)
    st.markdown(quote_box(q3, s3), unsafe_allow_html=True)

    # ── Load Emma's feedback from MongoDB ──
    emma_items = []
    try:
        emma_items = list(get_mongo_db()["comps_feedback"].find({}, {"_id": 0}))
    except Exception as e:
        st.warning(f"Could not load Emma's feedback: {e}")

    # ── Build Emily's feedback mapped to sections ──
    emily_by_section = {}
    for tid, ctx in lab_context.items():
        sections = task_to_sections.get(tid, ["General"])
        for sec in sections:
            emily_by_section.setdefault(sec, []).append({
                "reviewer": "Emily",
                "task_id": tid,
                "feedback": ctx["comment"],
                "prefill": ctx.get("prefill", ""),
                "section": sec,
            })

    # ── Emma's feedback grouped by section ──
    emma_by_section = {}
    for item in emma_items:
        sec = item.get("section", "General")
        emma_by_section.setdefault(sec, []).append(item)

    # ── Filters ──
    f_col1, f_col2 = st.columns(2)
    paper_opts = ["All Papers", "HBMC", "Climate", "Delphi", "SCPA", "General"]
    sel_paper = f_col1.selectbox("Filter by Paper:", paper_opts, key="lab_paper_filter")
    sel_reviewer = f_col2.selectbox("Filter by Reviewer:", ["All", "Emily", "Emma Tsui"], key="lab_reviewer_filter")

    # Paper keyword map for filtering Emma's items
    paper_keywords = {
        "HBMC": "HBMC", "Climate": "Climate", "Delphi": "Delphi", "SCPA": "SCPA", "General": "General"
    }

    # ── Collect all sections to show ──
    all_sections = sorted(set(list(emily_by_section.keys()) + list(emma_by_section.keys())))

    # Filter sections by paper
    def section_matches_paper(section, paper):
        if paper == "All Papers":
            return True
        kw = paper_keywords.get(paper, paper)
        # Also check via SECTION_TASKS keys (Emily sections) or Emma paper field
        emily_match = any(
            kw.lower() in item.get("section", "").lower()
            for item in emily_by_section.get(section, [])
        )
        emma_match = any(
            item.get("paper", "") == paper
            for item in emma_by_section.get(section, [])
        )
        return emily_match or emma_match or kw.lower() in section.lower()

    filtered_sections = [s for s in all_sections if section_matches_paper(s, sel_paper)]

    if not filtered_sections:
        st.info("No feedback found for this filter.")
    else:
        priority_color = {"high": "#e74c3c", "medium": "#f39c12", "low": "#27ae60", "none": "#2ecc71"}
        type_icon = {"quick_fix": "⚡", "clarification": "💬", "substantive": "📝", "major": "🏗️", "none": "✅", "substantive": "📝"}

        for section in filtered_sections:
            emily_items_sec = emily_by_section.get(section, []) if sel_reviewer in ("All", "Emily") else []
            emma_items_sec  = [i for i in emma_by_section.get(section, []) if sel_reviewer in ("All", "Emma Tsui")]

            all_sec_items = emily_items_sec + emma_items_sec
            if not all_sec_items:
                continue

            pending_count = sum(1 for i in all_sec_items if i.get("status", "pending") == "pending")
            done_count = len(all_sec_items) - pending_count

            with st.expander(f"📄 **{section}** — {pending_count} pending · {done_count} done", expanded=False):

                for item in all_sec_items:
                    reviewer = item.get("reviewer", "Emily")
                    badge = "🔵 Emily" if reviewer == "Emily" else "🟣 Emma Tsui"
                    atype = item.get("action_type", "substantive")
                    priority = item.get("priority", "medium")
                    status = item.get("status", "pending")
                    icon = type_icon.get(atype, "📋")
                    mins = item.get("estimated_minutes", "")
                    color = priority_color.get(priority, "#888")
                    item_id = item.get("id", item.get("task_id", ""))
                    feedback_text = item.get("feedback", item.get("comment", ""))

                    st.markdown(
                        f'<div style="border-left:3px solid {color};background:#1a1a2e;'
                        f'border-radius:6px;padding:10px 14px;margin:6px 0;color:#f0e6c8;">'
                        f'<span style="font-size:0.8rem;color:#aaa;">{badge} · {icon} {atype}'
                        f'{f" · ~{mins}min" if mins else ""} · '
                        f'<span style="color:{color};">{"🔴" if priority=="high" else "🟡" if priority=="medium" else "🟢"} {priority}</span></span><br>'
                        f'<span style="font-size:0.93rem;">{feedback_text}</span>'
                        f'</div>',
                        unsafe_allow_html=True
                    )

                st.markdown("**✍️ Draft Response:**")
                draft_key = f"lab_draft_{section}"
                saved_val = st.session_state.saved_responses.get(draft_key, "")
                draft = st.text_area("", value=saved_val, key=f"textarea_{section}", height=150, label_visibility="collapsed")

                d_col1, d_col2 = st.columns(2)
                if d_col1.button(f"💾 Save Draft (+10 XP)", key=f"save_{section}"):
                    st.session_state.saved_responses[draft_key] = draft
                    st.session_state.last_worked_section = section
                    st.session_state.last_worked_date = datetime.now().strftime("%b %d, %Y at %I:%M %p")
                    old_rank = get_rank(st.session_state.xp)
                    st.session_state.xp += 10
                    new_rank = get_rank(st.session_state.xp)
                    if new_rank[0] != old_rank[0]:
                        st.session_state.rank_up_title = new_rank[1]
                    st.session_state.celebration_xp = 10
                    save_all_progress()
                    st.success("Draft saved! ⚡")
                    st.rerun()

                # ── AI Writing Coach ──
                coach_key = f"coach_msgs_{section}"
                if coach_key not in st.session_state:
                    st.session_state[coach_key] = []

                if d_col2.button("🦇 Ask AI Coach", key=f"coach_open_{section}"):
                    st.session_state[f"coach_open_state_{section}"] = not st.session_state.get(f"coach_open_state_{section}", False)

                if st.session_state.get(f"coach_open_state_{section}", False):
                    st.markdown("---")
                    st.markdown("**🦇 Writing Coach** — asking about this section's feedback")

                    # Build feedback context string
                    feedback_context = "\n".join(
                        f"- [{item.get('reviewer','?')}] {item.get('feedback', item.get('comment',''))}"
                        for item in all_sec_items
                    )
                    current_draft = st.session_state.saved_responses.get(draft_key, "")

                    system_prompt = f"""You are an expert dissertation writing coach specializing in public health, aging, health policy, geriatrics, and disaster preparedness. Your student is a PhD candidate working on comprehensive exams.

You are helping them respond to specific committee feedback for the section: **{section}**

Committee feedback to address:
{feedback_context}

{"Current draft: " + current_draft if current_draft else "No draft yet."}

Help them draft strong, doctoral-level responses to this feedback. Be direct and specific. Use Batman metaphors occasionally."""

                    for msg in st.session_state[coach_key][-6:]:
                        if msg["role"] == "user":
                            st.markdown(
                                f'<div style="background:#1a1a2e;border-left:3px solid #f1c40f;'
                                f'border-radius:6px;padding:8px 12px;margin:4px 0;color:#f0e6c8;font-size:0.88rem;">'
                                f'<b style="color:#f1c40f;">You:</b> {msg["content"]}</div>',
                                unsafe_allow_html=True
                            )
                        else:
                            st.markdown(
                                f'<div style="background:#0d2b0d;border-left:3px solid #2ecc71;'
                                f'border-radius:6px;padding:8px 12px;margin:4px 0;color:#d5f5e3;font-size:0.88rem;">'
                                f'<b style="color:#2ecc71;">🦇 Coach:</b> {msg["content"]}</div>',
                                unsafe_allow_html=True
                            )

                    coach_input = st.text_area(
                        "Ask the coach:",
                        placeholder="e.g. 'Help me draft a response to the resilience theory feedback' or 'How do I strengthen this argument?'",
                        key=f"coach_input_{section}",
                        height=80
                    )

                    cc1, cc2 = st.columns(2)
                    if cc1.button("💬 Send", key=f"coach_send_{section}") and coach_input:
                        st.session_state[coach_key].append({"role": "user", "content": coach_input})
                        with st.spinner("🦇 Thinking..."):
                            try:
                                import anthropic
                                client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
                                response = client.messages.create(
                                    model="claude-sonnet-4-20250514",
                                    max_tokens=600,
                                    system=system_prompt,
                                    messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state[coach_key][-10:]]
                                )
                                st.session_state[coach_key].append({"role": "assistant", "content": response.content[0].text})
                                st.rerun()
                            except Exception as e:
                                st.error(f"Coach error: {e}")

                    if cc2.button("🗑️ Clear", key=f"coach_clear_{section}"):
                        st.session_state[coach_key] = []
                        st.rerun()

# ── TAB 3: REWARDS & ANALYTICS ─────────────
with t3:
    st.header("🎁 Rewards & Analytics")
    q4, s4 = random.choice(BATMAN_QUOTES)
    st.markdown(quote_box(q4, s4), unsafe_allow_html=True)

    # Rank progression
    st.subheader("🦇 Rank Progression")
    rank_cols = st.columns(len(RANKS))
    for i, (threshold, title, color) in enumerate(RANKS):
        with rank_cols[i]:
            unlocked = st.session_state.xp >= threshold
            opacity  = "1" if unlocked else "0.3"
            pulse    = "rank-card unlocked" if unlocked else "rank-card"
            st.markdown(
                f'<div class="{pulse}" style="border-color:{color};opacity:{opacity};">'
                f'<b style="color:{color};font-size:0.78rem;">{title}</b><br>'
                f'<small style="color:#555;">{threshold} XP</small></div>',
                unsafe_allow_html=True
            )
    st.divider()

    col_l, col_r = st.columns(2)
    with col_l:
        st.subheader("🏆 Available Rewards")
        base_rewards = [
            {"xp": 100,  "item": "⚡ 15 min DC Comic Break"},
            {"xp": 150,  "item": "📱 15 min Phone Break"},
            {"xp": 300,  "item": "🐕 Beach Walk with Ranger & Gadget"},
            {"xp": 500,  "item": "🚲 Sunset ride on Electra Townie Go!"},
            {"xp": 1000, "item": "📚 $50 ThriftBooks Shopping Spree"}
        ]
        all_rewards = base_rewards + st.session_state.custom_rewards
        for r in all_rewards:
            if st.session_state.xp >= r['xp']:
                st.markdown('<div class="reward-available">', unsafe_allow_html=True)
                if st.button(f"🎁 Claim: {r['item']}", key=f"clm_{r['xp']}_{r['item']}"):
                    st.session_state.claimed_rewards.append(r['item'])
                    st.session_state.reward_claimed = r['item']
                    st.session_state.celebration_xp = 5
                    save_all_progress()
                    st.balloons()
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
            else:
                st.write(f"🔒 **{r['xp']} XP**: {r['item']}")

    with col_r:
        st.subheader("📊 Focus Time Analytics")
        if st.session_state.task_timers:
            df         = pd.DataFrame(
                list(st.session_state.task_timers.items()), columns=['Task ID', 'Minutes']
            )
            st.bar_chart(df.set_index('Task ID'))
            total_mins = sum(st.session_state.task_timers.values())
            st.metric("Total PhD Focus Time", f"{total_mins // 60}h {total_mins % 60}m")
        else:
            st.info("Start a Pomodoro sprint to track focus time! 🦇")

# ── TAB 4: WRITING GUIDE ───────────────────
with t4:
    st.header("📜 Academic Command Center")
    q5, s5 = random.choice(BATMAN_QUOTES)
    st.markdown(quote_box(q5, s5), unsafe_allow_html=True)
    # ── WRITING WARMUP LAB ──
    st.subheader("🏋️ Writing Warmup Lab")
    st.caption("Daily exercises to sharpen your academic writing before diving into dissertation work.")

    WARMUP_EXERCISES = [
        {
            "title": "🎯 The Argument in One Sentence",
            "prompt": "Summarize the central argument of your dissertation in exactly one sentence. No hedging, no qualifiers — just the claim.",
            "type": "Argument Building",
            "hint": "Start with: 'This dissertation argues that...'"
        },
        {
            "title": "⚔️ Steel-Man the Opposition",
            "prompt": "Pick the strongest possible objection to your research and write 2-3 sentences making that argument as powerfully as you can.",
            "type": "Argument Building",
            "hint": "A strong dissertation anticipates and addresses counterarguments. Make it hurt."
        },
        {
            "title": "🔗 The Gap Statement",
            "prompt": "Write 3 sentences: (1) What the literature says, (2) What it misses, (3) What your research does about it.",
            "type": "Argument Building",
            "hint": "This is the core of your literature review. Every paper needs a clear gap statement."
        },
        {
            "title": "📊 Data to Claim",
            "prompt": "Take a finding from your research and write it as a strong academic claim. Then write 2 sentences of analysis explaining what it means for public health policy.",
            "type": "Argument Building",
            "hint": "Don't just report the finding — interpret it. What does it mean? For whom? So what?"
        },
        {
            "title": "🏥 The Policy Implication Sprint",
            "prompt": "In 3-4 sentences, describe one concrete policy change that your research supports. Name the specific population, the specific intervention, and the specific outcome.",
            "type": "Public Health Writing",
            "hint": "Be specific: not 'improve care for elderly' but 'expand HCBS waiver access for adults 65+ in rural Medicaid programs.'"
        },
        {
            "title": "🌍 The Equity Lens",
            "prompt": "Rewrite this sentence with an explicit equity framing: 'Older adults face challenges accessing home-based care.'",
            "type": "Public Health Writing",
            "hint": "Who specifically? Which populations are most affected? What structural factors drive this?"
        },
        {
            "title": "📝 The Methods Justification",
            "prompt": "In 2-3 sentences, justify why your research methodology is the right approach for your research question. Acknowledge one limitation.",
            "type": "Public Health Writing",
            "hint": "Reviewers always ask: why this method and not another? Answer it preemptively."
        },
        {
            "title": "🔬 Abstract from Scratch",
            "prompt": "Write a 5-sentence abstract for one of your papers: (1) Background, (2) Gap, (3) Methods, (4) Key Finding, (5) Implication.",
            "type": "Public Health Writing",
            "hint": "Each sentence does exactly one job. No sentence should do two jobs."
        }
    ]

    # Filter by type
    warmup_type = st.radio(
        "Exercise Type:",
        ["All", "Argument Building", "Public Health Writing"],
        horizontal=True,
        key="warmup_type"
    )

    filtered_warmups = [
        w for w in WARMUP_EXERCISES
        if warmup_type == "All" or w['type'] == warmup_type
    ]

    # Random exercise picker
    if 'current_warmup_idx' not in st.session_state:
        st.session_state.current_warmup_idx = 0

    col_pick1, col_pick2 = st.columns([1, 3])
    if col_pick1.button("🎲 Random Exercise", use_container_width=True):
        st.session_state.current_warmup_idx = random.randint(0, len(filtered_warmups) - 1)
        st.rerun()

    current_exercise = filtered_warmups[st.session_state.current_warmup_idx % len(filtered_warmups)]

    # Display exercise card
    st.markdown(
        f'<div style="background:linear-gradient(135deg,#1a1a2e,#0f3460);'
        f'border-left:4px solid #f1c40f;border-radius:10px;padding:20px;'
        f'color:#f0e6c8;margin:12px 0;">'
        f'<b style="color:#f1c40f;font-size:1.1rem;">{current_exercise["title"]}</b>'
        f'<span style="float:right;background:#f1c40f22;color:#f1c40f;'
        f'padding:2px 10px;border-radius:12px;font-size:0.78rem;">{current_exercise["type"]}</span><br><br>'
        f'<div style="font-size:1.0rem;line-height:1.7;margin-bottom:12px;">{current_exercise["prompt"]}</div>'
        f'<div style="color:#f1c40f;opacity:0.7;font-size:0.85rem;">💡 {current_exercise["hint"]}</div>'
        f'</div>',
        unsafe_allow_html=True
    )

    # Writing area
    warmup_response = st.text_area(
        "Your response:",
        placeholder="Start writing — no pressure, this is warmup...",
        key=f"warmup_{st.session_state.current_warmup_idx}",
        height=150
    )

    w_col1, w_col2 = st.columns(2)

    if w_col1.button("🦇 Get AI Feedback", use_container_width=True, key="warmup_feedback_btn"):
        if warmup_response:
            with st.spinner("Batman is reviewing your argument..."):
                try:
                    import anthropic
                    client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
                    message = client.messages.create(
                        model="claude-sonnet-4-20250514",
                        max_tokens=1024,
                        messages=[{
                            "role": "user",
                            "content": f"""You are an expert academic writing coach for public health doctoral students.

Exercise prompt: {current_exercise['prompt']}

Student's response:
\"\"\"{warmup_response}\"\"\"

Give concise, specific feedback in this format:
**💪 Strengths:** (1-2 sentences on what works)
**⚔️ Sharpen This:** (1-2 specific improvements)
**✨ Rewritten Version:** (a stronger version of their response)
**🦇 Verdict:** (one punchy Batman-themed line)

Be direct, encouraging, and doctoral-level specific."""
                        }]
                    )
                    feedback = message.content[0].text
                    st.markdown(
                        f'<div style="background:linear-gradient(135deg,#1a3a1a,#0d2b0d);'
                        f'border-left:4px solid #2ecc71;border-radius:10px;padding:20px;'
                        f'color:#d5f5e3;margin:12px 0;animation:slide-in 0.5s ease;">'
                        f'<b style="color:#2ecc71;font-size:1.1rem;">🦇 AI Feedback</b><br><br>'
                        f'<div style="white-space:pre-wrap;line-height:1.7;">{feedback}</div>'
                        f'</div>',
                        unsafe_allow_html=True
                    )
                    st.session_state.xp += 15
                    st.session_state.celebration_xp = 15
                    save_all_progress()
                    st.toast("Warmup Complete! +15 XP", icon="🦇")
                except Exception as e:
                    st.error(f"Feedback failed: {e}")
        else:
            st.warning("Write something first before asking for feedback!")

    if w_col2.button("⏭️ Next Exercise", use_container_width=True, key="next_warmup_btn"):
        st.session_state.current_warmup_idx = (st.session_state.current_warmup_idx + 1) % len(filtered_warmups)
        st.rerun()

    st.divider()
    

    # ── SENTENCE SLAYER ──
    st.subheader("⚡ The Sentence Slayer")
    st.caption("Paste a sentence or paragraph. AI will fix grammar, flag weak writing, and rewrite it.")

    import anthropic

    draft_input = st.text_area(
        "Paste your sentence or paragraph:",
        placeholder="It was found that there are a large number of elderly patients who utilized home-based care...",
        key="slayer_input",
        height=120
    )

    if draft_input:
        # Quick local fixes (instant, no API)
        quick_fix = (draft_input
                     .replace("It was found that ", "Data reveals ")
                     .replace("It was shown that ", "Evidence demonstrates ")
                     .replace("There are ", "Researchers identify ")
                     .replace("There is ", "Evidence shows ")
                     .replace("It is important to note that ", "")
                     .replace("It should be noted that ", "")
                     .replace("In order to ", "To ")
                     .replace("Due to the fact that ", "Because ")
                     .replace("At this point in time ", "Currently ")
                     .replace("Alzheimer and Dementia Related Dementias", "ADRD")
                     .replace("a large number of", "many")
                     .replace("the majority of", "most")
                     .replace("it is clear that", "clearly,")
                     .replace("utilized", "used")
                     .replace("facilitate", "support"))

        st.markdown(
            f'<div style="background:linear-gradient(90deg,#1a3a1a,#0d2b0d);'
            f'border-left:4px solid #2ecc71;border-radius:8px;padding:14px 20px;'
            f'color:#d5f5e3;animation:slide-in 0.4s ease;margin:8px 0;">'
            f'⚡ <b>Quick Fix:</b> {quick_fix}</div>',
            unsafe_allow_html=True
        )

        st.write("")

        if st.button("🦇 Deep AI Analysis", use_container_width=True):
            with st.spinner("The Dark Knight is analyzing your writing..."):
                try:
                    client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])

                    message = client.messages.create(
                        model="claude-opus-4-5",
                        max_tokens=1024,
                        messages=[
                            {
                                "role": "user",
                                "content": f"""You are an expert academic writing coach specializing in public health dissertations. Analyze this text and provide:

1. **Grammar Issues** — list any grammar errors with corrections
2. **Weak Writing Patterns** — identify passive voice, nominalization, hedging stacks, vague quantifiers, wind-up phrases
3. **Strength Rating** — rate the sentence(s) 1-10 for academic rigor and explain why
4. **Rewritten Version** — a stronger, cleaner rewrite in active voice
5. **One-Line Verdict** — a punchy Batman-themed verdict on the writing quality

Be specific and direct. Reference academic writing standards for doctoral dissertations in public health.

Text to analyze:
\"\"\"{draft_input}\"\"\"

Format your response with clear headers for each section."""
                            }
                        ]
                    )

                    analysis = message.content[0].text

                    st.markdown(
                        f'<div style="background:linear-gradient(135deg,#1a1a2e,#0f3460);'
                        f'border-left:4px solid #f1c40f;border-radius:10px;padding:20px;'
                        f'color:#f0e6c8;margin:12px 0;animation:slide-in 0.5s ease;">'
                        f'<b style="color:#f1c40f;font-size:1.1rem;">🦇 Deep Analysis</b><br><br>'
                        f'<div style="white-space:pre-wrap;line-height:1.7;">{analysis}</div>'
                        f'</div>',
                        unsafe_allow_html=True
                    )

                    # Award XP for using the slayer
                    save_all_progress()


                except anthropic.AuthenticationError:
                    st.error("⚠️ No API key found. Set your ANTHROPIC_API_KEY environment variable:\n```\nexport ANTHROPIC_API_KEY='your-key-here'\n```")
                except Exception as e:
                    st.error(f"Analysis failed: {e}")

    # ── TRANSITION VAULT ──
    st.subheader("🔗 Transition Vault")
    v1, v2, v3, v4 = st.columns(4)
    for i, (cat_name, words) in enumerate(st.session_state.custom_vault.items()):
        with [v1, v2, v3, v4][i]:
            st.markdown(f"**{cat_name}**")
            for word in words:
                st.write(f"• {word}")

    st.divider()

    # ── MASTER PROTOCOL ──
    st.header("🏆 The Ph.D. Writing Master Protocol")
    st.caption("Six pillars of doctoral-level academic writing. Reference these on every revision pass.")

    # ROW 1
    pg1, pg2, pg3 = st.columns(3)

    with pg1:
        st.markdown("""
        <div style="background:#f9f9f9;border-radius:10px;padding:16px;border-top:4px solid #f1c40f;min-height:280px;">
        <h4 style="margin-top:0;">🏛️ Logical Architecture</h4>
        <p><b>The Golden Thread:</b> Every sentence must connect back to your central research question. If it doesn't serve the argument, it's a Side Quest — cut it ruthlessly.</p>
        <p><b>MEAL Paragraphs:</b><br>
        &nbsp;&nbsp;• <b>M</b>ain Idea — one clear claim<br>
        &nbsp;&nbsp;• <b>E</b>vidence — cite it<br>
        &nbsp;&nbsp;• <b>A</b>nalysis — your interpretation<br>
        &nbsp;&nbsp;• <b>L</b>ead-out — bridge to next paragraph</p>
        <p><b>Reverse Outlining:</b> After drafting, write one sentence summarizing each paragraph. If the summary reads choppily, your structure is broken — fix the architecture, not just the sentences.</p>
        <p><b>Funnel Structure:</b> Each section should move from broad context → specific gap → your contribution. Never open with your finding.</p>
        </div>
        """, unsafe_allow_html=True)

    with pg2:
        st.markdown("""
        <div style="background:#f9f9f9;border-radius:10px;padding:16px;border-top:4px solid #2980b9;min-height:280px;">
        <h4 style="margin-top:0;">⚖️ Voice & Authority</h4>
        <p><b>Epistemic Modality:</b> Calibrate your certainty carefully.<br>
        &nbsp;&nbsp;• Strong: "demonstrates," "establishes"<br>
        &nbsp;&nbsp;• Medium: "suggests," "indicates," "points to"<br>
        &nbsp;&nbsp;• Weak: "may," "could," "appears to"<br>
        Never use "proves" — science doesn't prove.</p>
        <p><b>Slay Wind-Ups:</b> Delete these entirely:<br>
        &nbsp;&nbsp;✗ "It is important to note that..."<br>
        &nbsp;&nbsp;✗ "It should be mentioned that..."<br>
        &nbsp;&nbsp;✗ "One could argue that..."<br>
        Just state the thing.</p>
        <p><b>Signposting:</b> Guide the reader explicitly:<br>
        &nbsp;&nbsp;• "Having established X, this section examines Y."<br>
        &nbsp;&nbsp;• "This finding extends prior work by..."<br>
        &nbsp;&nbsp;• "In contrast to X, the present study..."</p>
        <p><b>First Person:</b> "I argue" is stronger than "it is argued." Own your claims.</p>
        </div>
        """, unsafe_allow_html=True)

    with pg3:
        st.markdown("""
        <div style="background:#f9f9f9;border-radius:10px;padding:16px;border-top:4px solid #8e44ad;min-height:280px;">
        <h4 style="margin-top:0;">🧪 Technical Rigor</h4>
        <p><b>Conceptual Consistency:</b> Identify your 3–5 core constructs on page 1 and use them verbatim throughout. Never substitute "Community Resilience" with "Neighborhood Strength" mid-paper.</p>
        <p><b>Acronym Discipline:</b> Define on first use, then use consistently. Apply Mt. Sinai/CUNY style for all medical terms (ADRD, HCBS, HaH, HBPC).</p>
        <p><b>Citation Synthesis:</b> Don't just stack citations — synthesize them:<br>
        &nbsp;&nbsp;✗ "Smith (2020) found X. Jones (2021) found Y."<br>
        &nbsp;&nbsp;✓ "X is well established in the literature (Smith, 2020; Jones, 2021), though..."</p>
        <p><b>Table & Figure Discipline:</b> Every table/figure must be interpretable standalone. Spell out all acronyms in captions, not just the body text.</p>
        </div>
        """, unsafe_allow_html=True)

    st.write("")

    # ROW 2
    pg4, pg5, pg6 = st.columns(3)

    with pg4:
        st.markdown("""
        <div style="background:#f9f9f9;border-radius:10px;padding:16px;border-top:4px solid #e67e22;min-height:260px;">
        <h4 style="margin-top:0;">🔬 Literature Integration</h4>
        <p><b>The 3-Move Citation:</b><br>
        &nbsp;&nbsp;1. State the claim<br>
        &nbsp;&nbsp;2. Cite the evidence<br>
        &nbsp;&nbsp;3. Interpret what it means <i>for your argument</i><br>
        Most writers do 1 and 2. The third move is what makes it doctoral.</p>
        <p><b>Recency Rule:</b> For fast-moving fields (policy, technology, COVID-era health), prioritize sources from the last 5 years. Flag older seminal works explicitly: "In their foundational work, X (2004)..."</p>
        <p><b>Avoid Citation Drive-Bys:</b> Citing without engaging is a missed opportunity. If a source is worth citing, it's worth one sentence of analysis.</p>
        </div>
        """, unsafe_allow_html=True)

    with pg5:
        st.markdown("""
        <div style="background:#f9f9f9;border-radius:10px;padding:16px;border-top:4px solid #c0392b;min-height:260px;">
        <h4 style="margin-top:0;">✂️ Editing & Revision</h4>
        <p><b>The 3-Pass System:</b><br>
        &nbsp;&nbsp;1. <b>Structure pass</b> — reverse outline, fix logic flow<br>
        &nbsp;&nbsp;2. <b>Sentence pass</b> — active voice, cut filler, vary length<br>
        &nbsp;&nbsp;3. <b>Detail pass</b> — acronyms, citations, formatting</p>
        <p><b>Sentence Length Variation:</b> Short sentences hit hard. Long sentences, which carry multiple ideas and build momentum toward a conclusion, create a different rhythm. Alternate between them intentionally.</p>
        <p><b>Read Aloud Test:</b> If you stumble reading it aloud, the reader will stumble too. Every stumble = a rewrite needed.</p>
        <p><b>Kill Your Darlings:</b> Your most beautiful sentence is probably also your most indulgent. If it doesn't serve the argument, it goes.</p>
        </div>
        """, unsafe_allow_html=True)

    with pg6:
        st.markdown("""
        <div style="background:#f9f9f9;border-radius:10px;padding:16px;border-top:4px solid #1abc9c;min-height:260px;">
        <h4 style="margin-top:0;">🧠 ADHD & Productivity</h4>
        <p><b>Shitty First Draft:</b> The only goal of draft 1 is to exist. Silence your internal editor entirely. Word count first, quality second — always.</p>
        <p><b>Body Doubling:</b> Write in the presence of others (café, library, co-working). The social context activates accountability even without interaction.</p>
        <p><b>Time-Boxing by Section:</b> Don't write "the methods section." Write "methods paragraph 2, the sampling rationale" for 25 minutes. Specificity defeats avoidance.</p>
        <p><b>Reward Stacking:</b> Don't wait until a chapter is done to reward yourself. Every task completed is a win. Use the XP system — that's what it's for. 🦇</p>
        <p><b>Transition Sentences as Anchors:</b> When resuming after a break, rewrite the last paragraph's final sentence before continuing. It re-engages working memory instantly.</p>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

# ── REFERENCE SEARCH ──
    st.divider()
    st.subheader("🔍 Reference Finder")
    st.caption("Search PubMed and Google Scholar for citations. Paste results directly into your paper.")

    search_query = st.text_input(
        "Search for references:",
        placeholder="e.g. HCBS Medicaid waiver older adults home-based care",
        key="ref_search"
    )

    col_search1, col_search2 = st.columns(2)
    search_pubmed  = col_search1.button("🔬 Search PubMed",         use_container_width=True)
    search_scholar = col_search2.button("🎓 Search Google Scholar",  use_container_width=True)

    if search_query:
        if search_pubmed:
            import urllib.parse
            encoded = urllib.parse.quote(search_query)
            pubmed_url = f"https://pubmed.ncbi.nlm.nih.gov/?term={encoded}&sort=date"
            st.markdown(
                f'<div style="background:linear-gradient(135deg,#1a1a2e,#0f3460);'
                f'border-left:4px solid #3498db;border-radius:10px;padding:16px 20px;'
                f'color:#f0e6c8;margin:8px 0;">'
                f'<b style="color:#3498db;">🔬 PubMed Search Ready</b><br><br>'
                f'<a href="{pubmed_url}" target="_blank" style="color:#f1c40f;font-size:1.05rem;">'
                f'→ Open PubMed results for: "{search_query}"</a><br><br>'
                f'<span style="font-size:0.85rem;opacity:0.7;">Sorted by most recent. '
                f'Filter by Free Full Text on the left sidebar for accessible papers.</span>'
                f'</div>',
                unsafe_allow_html=True
            )

        if search_scholar:
            import urllib.parse
            encoded = urllib.parse.quote(search_query)
            scholar_url = f"https://scholar.google.com/scholar?q={encoded}&sort=date"
            st.markdown(
                f'<div style="background:linear-gradient(135deg,#1a1a2e,#0f3460);'
                f'border-left:4px solid #e74c3c;border-radius:10px;padding:16px 20px;'
                f'color:#f0e6c8;margin:8px 0;">'
                f'<b style="color:#e74c3c;">🎓 Google Scholar Search Ready</b><br><br>'
                f'<a href="{scholar_url}" target="_blank" style="color:#f1c40f;font-size:1.05rem;">'
                f'→ Open Scholar results for: "{search_query}"</a><br><br>'
                f'<span style="font-size:0.85rem;opacity:0.7;">Click "Cite" under any result '
                f'for APA/AMA/MLA format.</span>'
                f'</div>',
                unsafe_allow_html=True
            )

    st.divider()
    st.subheader("🤖 AI Reference Assistant")
    st.caption("Describe what you need a citation for and Claude will suggest search terms and likely sources.")

    ref_question = st.text_area(
        "What do you need a reference for?",
        placeholder="e.g. I need a citation for the claim that HCBS is an optional Medicaid benefit and states use waivers",
        key="ref_question",
        height=80
    )

    if ref_question and st.button("🦇 Find References", use_container_width=True):
        with st.spinner("Searching the Bat-Database..."):
            try:
                import anthropic
                client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
                message = client.messages.create(
                    model="claude-opus-4-5",
                    max_tokens=1024,
                    messages=[{
                        "role": "user",
                        "content": f"""You are a research librarian specializing in public health, aging, health policy, geriatrics, and disaster preparedness.

The researcher needs a citation for this claim:
\"\"\"{ref_question}\"\"\"

Please provide:
1. **Best PubMed Search Terms** — 2-3 specific search strings they should try
2. **Likely Key Authors/Sources** — name researchers or organizations known for this topic
3. **Suggested Journals** — which journals most likely publish on this
4. **Seminal Papers to Look For** — any well-known papers or reports on this topic you're aware of (be honest if uncertain — say "search for" rather than inventing citations)
5. **Quick Citation Template** — a placeholder APA citation they can fill in once they find the paper

Be specific to public health / aging / health policy. Do NOT invent fake citations — if you're not sure of exact details, describe what to search for instead."""
                    }]
                )

                result = message.content[0].text
                st.markdown(
                    f'<div style="background:linear-gradient(135deg,#1a1a2e,#0f3460);'
                    f'border-left:4px solid #f1c40f;border-radius:10px;padding:20px;'
                    f'color:#f0e6c8;margin:12px 0;animation:slide-in 0.5s ease;">'
                    f'<b style="color:#f1c40f;font-size:1.1rem;">🦇 Reference Intelligence</b><br><br>'
                    f'<div style="white-space:pre-wrap;line-height:1.7;">{result}</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )
                save_all_progress()

            except anthropic.AuthenticationError:
                st.error("⚠️ Set your API key: export ANTHROPIC_API_KEY='your-key-here'")
            except Exception as e:
                st.error(f"Search failed: {e}")

    # ── SAVED REFERENCES ──
    st.divider()
    st.subheader("📌 Saved References")
    st.caption("Save references here and export them directly to Zotero with one click.")

    if 'saved_refs' not in st.session_state:
        st.session_state.saved_refs = []

    # ── Add reference manually ──
    with st.expander("➕ Add Reference Manually"):
        r_col1, r_col2 = st.columns(2)
        ref_author  = r_col1.text_input("Author(s)",       placeholder="Smith, J., Jones, A.",    key="r_author")
        ref_year    = r_col2.text_input("Year",            placeholder="2023",                    key="r_year")
        ref_title   = st.text_input(   "Title",            placeholder="Full article title",      key="r_title")
        r_col3, r_col4 = st.columns(2)
        ref_journal = r_col3.text_input("Journal/Source",  placeholder="Health Affairs",          key="r_journal")
        ref_doi     = r_col4.text_input("DOI (optional)",  placeholder="10.1000/xyz123",          key="r_doi")
        ref_volume  = r_col3.text_input("Volume",          placeholder="42",                      key="r_volume")
        ref_pages   = r_col4.text_input("Pages",           placeholder="100-115",                 key="r_pages")
        ref_url     = st.text_input(   "URL (optional)",   placeholder="https://...",             key="r_url")
        ref_notes   = st.text_input(   "Notes (optional)", placeholder="Key quote or why saved",  key="r_notes")

        if st.button("📌 Save Reference", use_container_width=True):
            if ref_title:
                st.session_state.saved_refs.append({
                    "author":  ref_author,
                    "year":    ref_year,
                    "title":   ref_title,
                    "journal": ref_journal,
                    "doi":     ref_doi,
                    "volume":  ref_volume,
                    "pages":   ref_pages,
                    "url":     ref_url,
                    "notes":   ref_notes
                })
                st.success("Reference saved! 🦇")
                st.rerun()
            else:
                st.warning("Title is required at minimum.")

    # ── Add from raw APA paste ──
    with st.expander("📋 Paste Raw APA Reference"):
        raw_ref = st.text_area(
            "Paste APA citation:",
            placeholder="Smith, J. A., & Jones, B. (2023). Title of article. Journal Name, 42(3), 100–115. https://doi.org/10.1000/xyz",
            key="raw_ref_input",
            height=80
        )
        if st.button("📌 Save Raw Reference", use_container_width=True) and raw_ref:
            st.session_state.saved_refs.append({
                "author": "", "year": "", "title": raw_ref,
                "journal": "", "doi": "", "volume": "",
                "pages": "", "url": "", "notes": "(raw paste)"
            })
            st.success("Raw reference saved!")
            st.rerun()

    # ── Display saved refs ──
    if st.session_state.saved_refs:
        st.write(f"**{len(st.session_state.saved_refs)} reference(s) saved:**")
        for i, ref in enumerate(st.session_state.saved_refs):
            with st.expander(f"📄 {ref.get('title', 'Untitled')[:80]}{'...' if len(ref.get('title','')) > 80 else ''}"):
                if ref.get('author'):  st.write(f"**Author:** {ref['author']}")
                if ref.get('year'):    st.write(f"**Year:** {ref['year']}")
                if ref.get('journal'): st.write(f"**Journal:** {ref['journal']}")
                if ref.get('doi'):     st.write(f"**DOI:** {ref['doi']}")
                if ref.get('url'):     st.write(f"**URL:** {ref['url']}")
                if ref.get('notes'):   st.write(f"**Notes:** {ref['notes']}")
                if st.button("🗑️ Delete", key=f"del_ref_{i}"):
                    st.session_state.saved_refs.pop(i)
                    st.rerun()

        st.divider()

        # ── ZOTERO EXPORT ──
        st.subheader("📤 Export to Zotero")

        def generate_ris(refs):
            ris_lines = []
            for ref in refs:
                ris_lines.append("TY  - JOUR")
                if ref.get('title'):
                    # Check if it's a raw paste (whole citation in title field)
                    if ref.get('notes') == '(raw paste)':
                        ris_lines.append(f"TI  - {ref['title']}")
                    else:
                        ris_lines.append(f"TI  - {ref['title']}")
                if ref.get('author'):
                    for author in ref['author'].split(','):
                        a = author.strip()
                        if a:
                            ris_lines.append(f"AU  - {a}")
                if ref.get('year'):
                    ris_lines.append(f"PY  - {ref['year']}")
                if ref.get('journal'):
                    ris_lines.append(f"JO  - {ref['journal']}")
                if ref.get('volume'):
                    ris_lines.append(f"VL  - {ref['volume']}")
                if ref.get('pages'):
                    start, *end = ref['pages'].replace('–','-').split('-')
                    ris_lines.append(f"SP  - {start.strip()}")
                    if end:
                        ris_lines.append(f"EP  - {end[0].strip()}")
                if ref.get('doi'):
                    ris_lines.append(f"DO  - {ref['doi']}")
                if ref.get('url'):
                    ris_lines.append(f"UR  - {ref['url']}")
                if ref.get('notes') and ref['notes'] != '(raw paste)':
                    ris_lines.append(f"N1  - {ref['notes']}")
                ris_lines.append("ER  - ")
                ris_lines.append("")
            return "\n".join(ris_lines)

        def generate_bibtex(refs):
            bib_lines = []
            for i, ref in enumerate(refs):
                author_key = ref.get('author','unknown').split(',')[0].strip().replace(' ','').lower()
                year_key   = ref.get('year', '0000')
                cite_key   = f"{author_key}{year_key}_{i}"
                bib_lines.append(f"@article{{{cite_key},")
                if ref.get('title'):
                    bib_lines.append(f"  title   = {{{ref['title']}}},")
                if ref.get('author'):
                    bib_lines.append(f"  author  = {{{ref['author']}}},")
                if ref.get('year'):
                    bib_lines.append(f"  year    = {{{ref['year']}}},")
                if ref.get('journal'):
                    bib_lines.append(f"  journal = {{{ref['journal']}}},")
                if ref.get('volume'):
                    bib_lines.append(f"  volume  = {{{ref['volume']}}},")
                if ref.get('pages'):
                    bib_lines.append(f"  pages   = {{{ref['pages']}}},")
                if ref.get('doi'):
                    bib_lines.append(f"  doi     = {{{ref['doi']}}},")
                if ref.get('url'):
                    bib_lines.append(f"  url     = {{{ref['url']}}},")
                bib_lines.append("}")
                bib_lines.append("")
            return "\n".join(bib_lines)

        ex_col1, ex_col2, ex_col3 = st.columns(3)

        # RIS download
        ris_data = generate_ris(st.session_state.saved_refs)
        ex_col1.download_button(
            label="⬇️ Download .ris (Zotero)",
            data=ris_data,
            file_name="dark_knight_references.ris",
            mime="application/x-research-info-systems",
            use_container_width=True,
            help="Open Zotero → File → Import → select this file"
        )

        # BibTeX download
        bib_data = generate_bibtex(st.session_state.saved_refs)
        ex_col2.download_button(
            label="⬇️ Download .bib (LaTeX)",
            data=bib_data,
            file_name="dark_knight_references.bib",
            mime="text/plain",
            use_container_width=True,
            help="For LaTeX / Overleaf users"
        )

        # Plain APA text download
        apa_lines = []
        for ref in st.session_state.saved_refs:
            if ref.get('notes') == '(raw paste)':
                apa_lines.append(ref['title'])
            else:
                apa = ""
                if ref.get('author'): apa += f"{ref['author']} "
                if ref.get('year'):   apa += f"({ref['year']}). "
                if ref.get('title'):  apa += f"{ref['title']}. "
                if ref.get('journal'):apa += f"{ref['journal']}"
                if ref.get('volume'): apa += f", {ref['volume']}"
                if ref.get('pages'):  apa += f", {ref['pages']}"
                if ref.get('doi'):    apa += f". https://doi.org/{ref['doi']}"
                apa_lines.append(apa.strip())
        apa_text = "\n\n".join(apa_lines)

        ex_col3.download_button(
            label="⬇️ Download .txt (APA)",
            data=apa_text,
            file_name="dark_knight_references.txt",
            mime="text/plain",
            use_container_width=True,
            help="Plain text APA list to paste anywhere"
        )

        st.markdown("""
        <div style="background:#1a1a2e;border-left:3px solid #f1c40f;border-radius:6px;
        padding:12px 16px;color:#f0e6c8;font-size:0.85rem;margin-top:8px;">
        <b style="color:#f1c40f;">🦇 How to import into Zotero:</b><br>
        1. Click <b>Download .ris</b> above<br>
        2. Open Zotero desktop app<br>
        3. <b>File → Import → </b>select the <code>.ris</code> file<br>
        4. All references land in a new collection instantly ✅
        </div>
        """, unsafe_allow_html=True)

    else:
        st.info("No references saved yet. Use the Reference Finder above to find sources, then save them here.")

    # ── COMMON MISTAKES CHEATSHEET ──
    st.subheader("🚨 Common Mistakes Cheatsheet")
    mistakes = {
        "❌ Passive voice overload": "\"It was found that X\" → \"Data reveals X\"",
        "❌ Nominalization": "\"The implementation of\" → \"Implementing\"",
        "❌ Vague quantifiers": "\"A large number of\" → \"Many\" or give the actual number",
        "❌ Throat-clearing openers": "\"This paper will discuss...\" → Just discuss it",
        "❌ Undefined acronyms in figures": "Spell out ALL acronyms in every figure caption",
        "❌ Orphaned citations": "Every citation needs at least one sentence of your analysis",
        "❌ Hedging stacks": "\"It may perhaps suggest...\" → Pick one hedge, not three",
        "❌ Inconsistent tense": "Literature review = past tense. Your findings = past tense. Implications = present tense.",
        "❌ Burying the lede": "State your main finding in the first 2 sentences of every section",
    }
    for mistake, fix in mistakes.items():
        with st.expander(mistake):
            st.write(f"✅ **Fix:** {fix}")

    st.info("💡 **Batman Rule:** Gotham doesn't need a perfect hero. It needs one who shows up. Your draft doesn't need to be perfect — it needs to exist.")
# ── TAB 5: COMPS REVIEW ────────────────────
with t5:
    st.header("🎓 Comprehensive Exam Review")
    q6, s6 = random.choice(BATMAN_QUOTES)
    st.markdown(quote_box(q6, s6), unsafe_allow_html=True)
    st.caption("Section-by-section AI feedback on your comprehensive exams draft.")

    COMPS_SECTIONS = [
        {"title": "Introduction to HBMC", "paper": "Paper 1: HBMC", "content": """Home-based medical care (HBMC) is comprised of the set of healthcare services delivered to a patient in their home. An interdisciplinary team typically leads HBMC programs, delivering care to homebound, frail, seriously ill older adults who otherwise cannot access conventional primary care due to age, disability, mobility or other issues."""},
        {"title": "Historical Context", "paper": "Paper 1: HBMC", "content": """HBMC has evolved significantly over the past few decades, driven by shifts in healthcare policy and patient preferences. The COVID-19 pandemic accelerated the adoption of telehealth and remote patient monitoring (RPM), catalyzing the adoption of HBMC into the broader healthcare system. Another key historical factor was the 2010 Affordable Care Act (ACA), which expanded home and community-based services (HCBS). This facilitated a move away from institutional care, and an increased focus on quality, patient-centered care and cost-efficiency."""},
        {"title": "Who Needs HBMC and Why", "paper": "Paper 1: HBMC", "content": """HBMC's expansion reflects the changing needs of America's oldest adults. It is currently projected that the number of American adults ages 85 and older (the 'oldest old'), the cohort that needs the most support with activities of daily living (ADLs), will more than double from 6.5 million (2022) to 13.7 million in 2040 (a 111 percent increase). This cohort experiences aging, related declines in function, including reduced walking ability, muscle strength, and flexibility. Mental health is also impacted by neurological mechanisms due to aging, leading to cognitive decline, dementia, and depression. HBMC models such as Home-Based Primary Care (HBPC) and Home Health Services (HHS) address these challenges by providing care directly in the home, increasing access to healthcare and quality of life these adults would likely go without."""},
        {"title": "Models of Home-Based Medical Care", "paper": "Paper 1: HBMC", "content": """There is a range of HBMC models that allow people to remain in their home. These vary according to acuity, intensity, and length of care. Home-Based Primary Care (HBPC) is one HBMC healthcare model designed to address the needs of the homebound, chronically ill, frail population. HBPC is a longitudinal model of care which delivers care to homebound adults, particularly older adults with complex chronic medical comorbidities. Home Health Services (HHS) refer to the suite of medical services provided by nurses, rehabilitation therapists, including physical and occupational therapists, and home health aides (HHAs). These services are time-limited and are typically provided to post-acute patients discharged from the hospital. Hospital-at-Home (HaH) is acute, hospital-level treatment delivered in the patient's home, and is a substitute for inpatient hospitalization."""},
        {"title": "Economic and Clinical Impact", "paper": "Paper 1: HBMC", "content": """HBMC not only reduces avoidable hospitalizations among the homebound older adult population, but also demonstrates significant cost savings. Studies have shown that HBMC can reduce hospital admissions by 20-30% and emergency department visits by up to 25%. The economic benefits extend beyond direct cost savings to include improved quality of life, reduced caregiver burden, and better alignment with patient preferences for aging in place."""},
        {"title": "Advantages of HBMC", "paper": "Paper 1: HBMC", "content": """Home-based medical care presents a number of benefits, including expanded access to underserved communities, reduced hospital-acquired infections, improved patient satisfaction, and the ability to provide personalized care in familiar surroundings. HBMC also reduces the burden on formal caregivers and enables more efficient use of healthcare resources by targeting high-need, high-cost patients."""},
        {"title": "Disadvantages of HBMC", "paper": "Paper 1: HBMC", "content": """Home-based medical care offers many benefits, but it also presents distinct risks and limitations. These include challenges related to reimbursement and payment models, workforce shortages, regulatory complexity, technology infrastructure requirements, and the clinical limitations of delivering acute care outside of a hospital setting. The lack of a standardized reimbursement model remains one of the most significant barriers to widespread HBMC adoption."""},
        {"title": "Successful Aging", "paper": "Paper 2: Climate & Aging", "content": """The concept of Successful Aging (SA) emerged as a concept in the early 1960s, and is widely used in gerontology to describe aging well. The most cited model of SA is Rowe and Kahn's (1997) three-component framework, which defines successful aging as: (1) low probability of disease and disease-related disability, (2) high cognitive and physical functional capacity, and (3) active engagement with life. However, this model has been criticized for its narrow focus on individual-level factors and its failure to account for structural determinants of health."""},
        {"title": "Systems Theory and the Socio-ecological Model", "paper": "Paper 2: Climate & Aging", "content": """Although Resilience Theory acknowledges social and structural influences beyond the individual, it does not fully capture the multi-level systemic dynamics that shape older adults' vulnerability and adaptive capacity. Systems Theory and the Socio-ecological Model (SEM) provide a complementary framework. Bronfenbrenner's ecological systems theory conceptualizes human development as embedded within nested environmental systems: the microsystem, mesosystem, exosystem, and macrosystem."""},
        {"title": "Physiological Vulnerabilities", "paper": "Paper 2: Climate & Aging", "content": """Older adults are more likely to have one or more conditions that make them especially vulnerable to climate-related health impacts. These include cardiovascular disease, respiratory conditions, diabetes, and neurological disorders. Thermoregulatory impairment, reduced kidney function, and polypharmacy further increase vulnerability to heat-related illness. Frailty, defined as a state of increased vulnerability to stressors, is particularly prevalent among community-dwelling older adults aged 80 and older."""},
        {"title": "Mental Health Impacts", "paper": "Paper 2: Climate & Aging", "content": """Extreme weather events may worsen anxiety, depression, post-traumatic stress disorder (PTSD), and social isolation among older adults. The psychological impact of losing one's home, community, or sense of place can be profound, particularly for older adults with deep community ties. Climate grief and eco-anxiety are emerging constructs that describe the psychological distress associated with awareness of climate change and its impacts."""},
        {"title": "Home Loss, Displacement, and Institutionalization", "paper": "Paper 2: Climate & Aging", "content": """Natural disasters disproportionately affect older adults' housing stability. Home loss and displacement can trigger a cascade of negative health outcomes, including accelerated functional decline, increased mortality, and premature institutionalization. Studies of Hurricane Katrina found that older adults who were displaced were significantly more likely to be admitted to nursing homes in the aftermath, even controlling for pre-disaster health status."""},
        {"title": "Preparedness Frameworks", "paper": "Paper 3: Delphi & Policy", "content": """Clinical protocols for high-risk older adults have also been derived from Delphi studies. The 5Ts Framework identifies five domains of disaster preparedness for older adults: transportation, medications, medical equipment, medical records, and treatment decisions. The ASPR Toolkit provides guidance for healthcare coalitions on integrating older adult needs into emergency operations plans."""},
        {"title": "4.2 Scaling Down and Relevant Units of Analysis", "paper": "Paper 4: SCPA", "content": """Scaling down in SCPA means shifting the unit of analysis from the national to the subnational level. In the context of HBMC emergency preparedness, this means examining state-level variation in how federal preparedness guidelines are implemented. States represent the appropriate unit of analysis because they are the primary locus of Medicaid administration, healthcare licensing, and emergency management coordination."""},
        {"title": "4.3 Variation Under a Shared Federal Framework", "paper": "Paper 4: SCPA", "content": """Despite sharing a common federal regulatory framework, states exhibit substantial variation in HBMC emergency preparedness policies. This variation is driven by differences in state Medicaid programs, emergency management infrastructure, political context, and the strength of advocacy coalitions. SCPA provides tools to analyze this variation systematically, identifying which configurations of state-level factors are associated with stronger preparedness outcomes."""},
        {"title": "4.4 Causal Complexity in HBMC Emergency Preparedness", "paper": "Paper 4: SCPA", "content": """HBMC emergency preparedness is causally complex in ways that make conventional regression-based analysis insufficient. Multiple causal pathways may lead to the same outcome (equifinality), and the same factor may have different effects in different contexts (causal asymmetry). SCPA's set-theoretic methods, particularly Qualitative Comparative Analysis (QCA), are well-suited to capture this complexity."""},
        {"title": "Conclusion (SCPA)", "paper": "Paper 4: SCPA", "content": """This paper has argued that Subnational Comparative Policy Analysis (SCPA) provides a methodologically rigorous and theoretically appropriate framework for studying variation in HBMC emergency preparedness across states. By scaling down to the state level, designing controlled comparisons, and applying set-theoretic logic to account for causal complexity, researchers can generate actionable insights for policy reform."""},
    ]

    SECTION_TASKS = {
        "Introduction to HBMC": ["#7", "#13", "#14", "#32"],
        "Historical Context": ["#7", "#13"],
        "Who Needs HBMC and Why": ["#7", "#14", "#29"],
        "Models of Home-Based Medical Care": ["#12", "#13", "#14", "#19", "#23", "#32"],
        "Economic and Clinical Impact": ["#20", "#24", "#25", "#31"],
        "Advantages of HBMC": ["#20", "#24", "#25"],
        "Disadvantages of HBMC": ["#19", "#20", "#24", "#25", "#29", "#30"],
        "Successful Aging": ["#39"],
        "Systems Theory and the Socio-ecological Model": ["#38", "#40", "#55"],
        "Physiological Vulnerabilities": ["#45", "#42"],
        "Mental Health Impacts": ["#42", "#49"],
        "Home Loss, Displacement, and Institutionalization": ["#44", "#50", "#52", "#63"],
        "Preparedness Frameworks": ["#38", "#41", "#54", "#58", "#59", "#65", "#71", "#92"],
        "4.2 Scaling Down and Relevant Units of Analysis": ["#85", "#89"],
        "4.3 Variation Under a Shared Federal Framework": ["#85", "#89"],
        "4.4 Causal Complexity in HBMC Emergency Preparedness": ["#85", "#89"],
        "Conclusion (SCPA)": ["#85", "#89"],
    }

    # 1. Paper filter
    papers = sorted(set(s['paper'] for s in COMPS_SECTIONS))
    selected_paper = st.selectbox("Filter by Paper:", ["All Papers"] + papers, key="comps_paper_filter")

    filtered_sections = [
        s for s in COMPS_SECTIONS
        if selected_paper == "All Papers" or s['paper'] == selected_paper
    ]

    # 2. Section selector
    section_titles = [f"{s['paper']} — {s['title']}" for s in filtered_sections]
    offset = st.session_state.get('comps_next_offset', 0)
    default_idx = offset % len(filtered_sections)

    selected_idx = st.selectbox(
        "Select Section:",
        range(len(section_titles)),
        index=default_idx,
        format_func=lambda i: section_titles[i],
        key="comps_section_select"
    )

    # 3. Current section
    current_section = filtered_sections[selected_idx]

    # 4. Display section card
    st.markdown(
        f'<div style="background:linear-gradient(135deg,#1a1a2e,#0f3460);'
        f'border-left:4px solid #f1c40f;border-radius:10px;padding:20px;'
        f'color:#f0e6c8;margin:12px 0;">'
        f'<b style="color:#f1c40f;font-size:1.1rem;">{current_section["title"]}</b>'
        f'<span style="float:right;background:#f1c40f22;color:#f1c40f;'
        f'padding:2px 10px;border-radius:12px;font-size:0.78rem;">{current_section["paper"]}</span><br><br>'
        f'<div style="font-size:0.92rem;line-height:1.8;white-space:pre-wrap;">{current_section["content"]}</div>'
        f'</div>',
        unsafe_allow_html=True
    )

    # 5. Linked tasks
    section_task_ids = SECTION_TASKS.get(current_section['title'], [])
    if section_task_ids:
        all_tasks_lookup = {i['id']: i for cat in master_tasks.values() for i in cat}
        linked_tasks = [all_tasks_lookup[tid] for tid in section_task_ids if tid in all_tasks_lookup]
        if linked_tasks:
            st.markdown("**📌 Tasks linked to this section:**")
            for task in linked_tasks:
                is_done = task['id'] in st.session_state.completed_tasks
                type_icon = {"Quick Win": "⚡", "Deep Work": "🔬", "Resource Hunt": "🔍"}.get(task['type'], "🎯")
                status = "✅" if is_done else "⬜"
                color = "#888" if is_done else "#000"
                strikethrough = "text-decoration:line-through;" if is_done else ""
                st.markdown(
                    f'<div style="background:#f9f9f9;border-left:3px solid #f1c40f;'
                    f'border-radius:6px;padding:8px 12px;margin:4px 0;{strikethrough}color:{color};">'
                    f'{status} {type_icon} <b>{task["id"]}</b>: {task["task"]} '
                    f'<span style="float:right;color:#f1c40f;font-weight:bold;">+{task["pts"]} XP</span>'
                    f'</div>',
                    unsafe_allow_html=True
                )

    st.divider()

    # 6. Feedback type
    feedback_type = st.radio(
        "Feedback Focus:",
        ["📋 General Review", "🔬 Argument Strength", "📚 Literature & Citations", "✍️ Academic Voice", "🎯 Emily's Lens"],
        horizontal=True,
        key="comps_feedback_type"
    )

    feedback_prompts = {
        "📋 General Review": "Give a comprehensive review covering argument clarity, evidence quality, academic voice, and structure. Be specific and doctoral-level.",
        "🔬 Argument Strength": "Focus specifically on the strength of the argument. Is the claim clear? Is it well-supported? Are there logical gaps? What counterarguments are missing?",
        "📚 Literature & Citations": "Focus on the literature review quality. Are citations used effectively? Is there synthesis or just stacking? Are there key sources missing? Is recency appropriate?",
        "✍️ Academic Voice": "Focus on writing quality — passive voice, nominalization, hedging, vague quantifiers, wind-up phrases. Provide specific rewrites for weak sentences.",
        "🎯 Emily's Lens": "You are Emily, a dissertation committee member in public health and aging policy. Give direct, constructive feedback as a committee member would during a comps review. Be rigorous but supportive."
    }

    # 7. Optional notes
    user_notes = st.text_area(
        "Add context or specific questions (optional):",
        placeholder="e.g. 'I'm worried the argument in paragraph 2 is too weak' or 'Does this section address the CARA model adequately?'",
        key="comps_notes",
        height=80
    )

    col_fb1, col_fb2 = st.columns(2)

    # 8. Feedback button
    if col_fb1.button("🦇 Get Section Feedback", use_container_width=True, key="comps_feedback_btn"):
        with st.spinner("Analyzing your comps..."):
            try:
                import anthropic
                client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])

                prompt = f"""You are an expert dissertation committee member specializing in public health, aging, health policy, geriatrics, and disaster preparedness.

Paper: {current_section['paper']}
Section: {current_section['title']}

Section content:
\"\"\"{current_section['content']}\"\"\"

{f'Student notes: {user_notes}' if user_notes else ''}

{feedback_prompts[feedback_type]}

Format your response with these headers:
**📋 Overall Assessment** (2-3 sentences)
**💪 Strengths** (bullet points)
**⚔️ Weaknesses & Gaps** (bullet points, be specific)
**✨ Priority Revisions** (top 3 most important changes, numbered)
**🦇 Committee Verdict** (one direct sentence on whether this section is ready)"""

                message = client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=1500,
                    messages=[{"role": "user", "content": prompt}]
                )

                feedback = message.content[0].text
                st.markdown(
                    f'<div style="background:linear-gradient(135deg,#1a3a1a,#0d2b0d);'
                    f'border-left:4px solid #2ecc71;border-radius:10px;padding:20px;'
                    f'color:#d5f5e3;margin:12px 0;">'
                    f'<b style="color:#2ecc71;font-size:1.1rem;">🦇 Section Feedback — {current_section["title"]}</b><br><br>'
                    f'<div style="white-space:pre-wrap;line-height:1.7;">{feedback}</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )
                st.session_state.xp += 20
                st.session_state.celebration_xp = 20
                save_all_progress()
                st.toast("Section reviewed! +20 XP", icon="🦇")

            except Exception as e:
                st.error(f"Feedback failed: {e}")

    # 9. Next section button
    if col_fb2.button("⏭️ Next Section", use_container_width=True, key="comps_next_btn"):
        if 'comps_next_offset' not in st.session_state:
            st.session_state.comps_next_offset = 0
        st.session_state.comps_next_offset += 1
        st.rerun()

    st.divider()

    # 10. Committee Feedback
    st.subheader("👥 Committee Feedback")

    reviewer_filter = st.selectbox(
        "Filter by Committee Member:",
        ["All", "Emily", "Emma Tsui"],
        key="reviewer_filter"
    )

    # Emily's feedback from lab_context
    emily_feedback = [
        {"reviewer": "Emily", "paper": "HBMC", "section": "Economic Impact", "feedback": ctx["comment"], "task_id": tid, "priority": "high", "action_type": "substantive"}
        for tid, ctx in lab_context.items()
    ]

    # Emma's feedback from MongoDB
    emma_feedback = []
    try:
        emma_feedback = list(get_mongo_db()["comps_feedback"].find({"reviewer": "Emma Tsui"}, {"_id": 0}))
    except Exception as e:
        st.warning(f"Could not load Emma's feedback: {e}")

    all_committee_feedback = []
    if reviewer_filter in ("All", "Emily"):
        all_committee_feedback += emily_feedback
    if reviewer_filter in ("All", "Emma Tsui"):
        all_committee_feedback += emma_feedback

    if all_committee_feedback:
        pending = [f for f in all_committee_feedback if f.get("status", "pending") == "pending"]
        done = [f for f in all_committee_feedback if f.get("status", "pending") != "pending"]
        st.progress(len(done) / len(all_committee_feedback), text=f"{len(done)}/{len(all_committee_feedback)} addressed")

        priority_color = {"high": "#e74c3c", "medium": "#f39c12", "low": "#27ae60", "none": "#888"}
        type_icon = {"quick_fix": "⚡", "clarification": "💬", "substantive": "📝", "major": "🏗️", "none": "✅"}

        for item in all_committee_feedback:
            reviewer = item.get("reviewer", "Emily")
            paper = item.get("paper", "")
            section = item.get("section", "")
            feedback_text = item.get("feedback", item.get("comment", ""))
            priority = item.get("priority", "medium")
            atype = item.get("action_type", "substantive")
            status = item.get("status", "pending")
            mins = item.get("estimated_minutes", "")
            task_id = item.get("task_id", item.get("id", ""))
            color = priority_color.get(priority, "#888")
            icon = type_icon.get(atype, "📋")
            reviewer_badge = "🔵 Emily" if reviewer == "Emily" else "🟣 Emma Tsui"
            time_str = f" · ~{mins}min" if mins else ""
            label = f"{icon} {reviewer_badge} | [{paper}] {section}{time_str}"

            with st.expander(label, expanded=(priority == "high" and status == "pending")):
                st.markdown(f"**Feedback:** {feedback_text}")
                if task_id:
                    st.caption(f"ID: {task_id} · {atype} · Priority: {priority}")
    else:
        st.info("No committee feedback found.")

    st.divider()

    # 11. Progress tracker
    st.subheader("📊 Review Progress")
    if 'reviewed_sections' not in st.session_state:
        st.session_state.reviewed_sections = set()

    if st.button("✅ Mark Section as Reviewed", key="mark_reviewed"):
        st.session_state.reviewed_sections.add(current_section['title'])
        st.success(f"Marked '{current_section['title']}' as reviewed!")

    reviewed_count = len(st.session_state.reviewed_sections)
    total_count = len(COMPS_SECTIONS)
    st.progress(reviewed_count / total_count if total_count else 0)
    st.write(f"**{reviewed_count}/{total_count} sections reviewed**")

    if st.session_state.reviewed_sections:
        with st.expander("📋 Reviewed Sections"):
            for s in st.session_state.reviewed_sections:
                st.write(f"✅ {s}")
# ── TAB 6: MIND MAP & NOTEBOOK ────────────────────
with t6:
    st.header("🧠 Mind Map & Idea Notebook")
    q7, s7 = random.choice(BATMAN_QUOTES)
    st.markdown(quote_box(q7, s7), unsafe_allow_html=True)
    st.caption("Capture thoughts, connect ideas across papers, and generate visual mind maps.")

    # Initialize notebook state
    if 'notebook_entries' not in st.session_state:
        st.session_state.notebook_entries = []
    if 'mindmap_data' not in st.session_state:
        st.session_state.mindmap_data = None

    # ── THOUGHT CAPTURE ──
    st.subheader("💭 Capture a Thought")

    nb_col1, nb_col2 = st.columns([3, 1])
    thought_input = nb_col1.text_area(
        "What's on your mind?",
        placeholder="e.g. 'HCBS waivers connect to disaster preparedness because states that have stronger waiver programs may also have better emergency protocols for home-based patients...'",
        key="thought_input",
        height=100
    )

    paper_tag = nb_col2.selectbox(
        "Tag to paper:",
        ["General", "Paper 1: HBMC", "Paper 2: Climate & Aging", "Paper 3: Delphi & Policy", "Paper 4: SCPA"],
        key="thought_paper_tag"
    )

    theme_tag = nb_col2.text_input(
        "Theme tag:",
        placeholder="e.g. policy, equity, methods",
        key="thought_theme_tag"
    )

    if st.button("➕ Add to Notebook", use_container_width=True, key="add_thought_btn"):
        if thought_input:
            st.session_state.notebook_entries.append({
                "id": len(st.session_state.notebook_entries),
                "thought": thought_input,
                "paper": paper_tag,
                "theme": theme_tag,
                "timestamp": datetime.now().strftime("%m/%d %H:%M")
            })
            save_all_progress()
            st.success("Thought captured! 🦇")
            st.rerun()
        else:
            st.warning("Type something first!")

    st.divider()

    # ── NOTEBOOK ENTRIES ──
    if st.session_state.notebook_entries:
        st.subheader(f"📓 Notebook ({len(st.session_state.notebook_entries)} thoughts)")

        # Filter
        filter_col1, filter_col2 = st.columns(2)
        filter_paper = filter_col1.selectbox(
            "Filter by paper:",
            ["All"] + ["General", "Paper 1: HBMC", "Paper 2: Climate & Aging", "Paper 3: Delphi & Policy", "Paper 4: SCPA"],
            key="nb_filter_paper"
        )
        filter_theme = filter_col2.text_input("Filter by theme:", key="nb_filter_theme")

        filtered_entries = [
            e for e in st.session_state.notebook_entries
            if (filter_paper == "All" or e['paper'] == filter_paper)
            and (not filter_theme or filter_theme.lower() in e.get('theme', '').lower())
        ]

        for i, entry in enumerate(filtered_entries):
            paper_colors = {
                "Paper 1: HBMC": "#3498db",
                "Paper 2: Climate & Aging": "#2ecc71",
                "Paper 3: Delphi & Policy": "#e67e22",
                "Paper 4: SCPA": "#9b59b6",
                "General": "#f1c40f"
            }
            color = paper_colors.get(entry['paper'], "#f1c40f")
            with st.expander(f"💭 {entry['thought'][:60]}{'...' if len(entry['thought']) > 60 else ''} — {entry['timestamp']}"):
                st.markdown(
                    f'<div style="border-left:3px solid {color};padding:8px 12px;'
                    f'background:#f9f9f9;border-radius:6px;">'
                    f'{entry["thought"]}<br><br>'
                    f'<span style="background:{color}22;color:{color};padding:2px 8px;'
                    f'border-radius:10px;font-size:0.8rem;font-weight:bold;">{entry["paper"]}</span>'
                    f'{f" &nbsp; <span style=\'color:#888;font-size:0.8rem;\'>#{entry[chr(116)+chr(104)+chr(101)+chr(109)+chr(101)]}</span>" if entry.get("theme") else ""}'
                    f'</div>',
                    unsafe_allow_html=True
                )
                if st.button("🗑️ Delete", key=f"del_thought_{entry['id']}"):
                    st.session_state.notebook_entries = [
                        e for e in st.session_state.notebook_entries if e['id'] != entry['id']
                    ]
                    save_all_progress()
                    st.rerun()

        st.divider()

        # ── AI MIND MAP GENERATOR ──
        st.subheader("🗺️ Generate Mind Map")
        st.caption("AI will analyze your notebook entries and generate an interactive visual mind map.")

        focus_area = st.text_input(
            "Focus on a specific theme (optional):",
            placeholder="e.g. 'policy barriers' or 'equity' or leave blank for all thoughts",
            key="map_focus"
        )

        if st.button("🦇 Generate Mind Map", use_container_width=True, key="gen_mindmap_btn"):
            entries_to_map = [
                e for e in st.session_state.notebook_entries
                if not focus_area or focus_area.lower() in e['thought'].lower()
                or focus_area.lower() in e.get('theme', '').lower()
            ]

            if entries_to_map:
                with st.spinner("Batman is connecting the dots..."):
                    try:
                        import anthropic
                        client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])

                        entries_text = "\n".join([
                            f"[{e['paper']} | {e.get('theme', 'general')}]: {e['thought']}"
                            for e in entries_to_map
                        ])

                        prompt = f"""You are a doctoral writing coach helping a PhD student in public health connect ideas across their dissertation papers.

The student's notebook entries are:
{entries_text}

Their dissertation covers:
- Paper 1: Home-Based Medical Care (HBMC)
- Paper 2: Climate disasters and older adults
- Paper 3: Delphi methodology and disaster preparedness
- Paper 4: Subnational Comparative Policy Analysis (SCPA)

Return ONLY valid JSON in this exact format, nothing else:
{{
  "central": "One overarching theme connecting all thoughts",
  "branches": [
    {{
      "id": "b1",
      "label": "Branch Theme Name",
      "color": "#3498db",
      "nodes": [
        {{
          "id": "n1",
          "label": "Idea from notes (keep under 8 words)",
          "paper": "Paper 1: HBMC"
        }}
      ]
    }}
  ],
  "connections": [
    {{
      "from": "n1",
      "to": "n2",
      "label": "why they connect (under 6 words)"
    }}
  ]
}}

Use these colors per paper:
- Paper 1: HBMC = #3498db
- Paper 2: Climate & Aging = #2ecc71  
- Paper 3: Delphi & Policy = #e67e22
- Paper 4: SCPA = #9b59b6
- General = #f1c40f

Create 2-4 branches with 2-4 nodes each. Make connections across papers where ideas genuinely link."""

                        message = client.messages.create(
                            model="claude-sonnet-4-20250514",
                            max_tokens=2000,
                            messages=[{"role": "user", "content": prompt}]
                        )

                        import json
                        raw = message.content[0].text.strip()
                        # Strip markdown fences if present
                        if raw.startswith("```"):
                            raw = raw.split("```")[1]
                            if raw.startswith("json"):
                                raw = raw[4:]
                        map_data = json.loads(raw.strip())
                        st.session_state.mindmap_data = map_data

                        st.session_state.xp += 25
                        st.session_state.celebration_xp = 25
                        save_all_progress()
                        st.toast("Mind map generated! +25 XP", icon="🦇")

                    except Exception as e:
                        st.error(f"Mind map failed: {e}")
            else:
                st.warning("No matching entries — add some thoughts first!")

        # ── RENDER VISUAL MIND MAP ──
        if st.session_state.get('mindmap_data'):
            map_data = st.session_state.mindmap_data
            import json
            map_json = json.dumps(map_data)

            components.html(f"""
<!DOCTYPE html>
<html>
<head>
<style>
  body {{ margin: 0; background: #0a0a1a; font-family: Arial, sans-serif; overflow: hidden; }}
  canvas {{ display: block; }}
  #tooltip {{
    position: absolute; background: rgba(0,0,0,0.85); color: #f0e6c8;
    padding: 6px 12px; border-radius: 8px; font-size: 13px;
    pointer-events: none; display: none; border: 1px solid #f1c40f;
    max-width: 200px; word-wrap: break-word;
  }}
</style>
</head>
<body>
<canvas id="mindmap"></canvas>
<div id="tooltip"></div>
<script>
const data = {map_json};
const canvas = document.getElementById('mindmap');
const ctx = canvas.getContext('2d');
const tooltip = document.getElementById('tooltip');

canvas.width = window.innerWidth;
canvas.height = 520;

const W = canvas.width, H = canvas.height;
const cx = W / 2, cy = H / 2;

// Build node positions
const nodes = [];
const edges = [];

// Central node
nodes.push({{ id: 'central', label: data.central, x: cx, y: cy, r: 50, color: '#f1c40f', textColor: '#000', type: 'central' }});

const branchCount = data.branches.length;
data.branches.forEach((branch, bi) => {{
  const bAngle = (bi / branchCount) * Math.PI * 2 - Math.PI / 2;
  const bx = cx + Math.cos(bAngle) * 170;
  const by = cy + Math.sin(bAngle) * 140;
  nodes.push({{ id: branch.id, label: branch.label, x: bx, y: by, r: 38, color: branch.color, textColor: '#fff', type: 'branch' }});
  edges.push({{ from: 'central', to: branch.id, color: branch.color, label: '' }});

  const nodeCount = branch.nodes.length;
  branch.nodes.forEach((node, ni) => {{
    const spread = 0.7;
    const nAngle = bAngle + (ni - (nodeCount - 1) / 2) * spread;
    const nx = bx + Math.cos(nAngle) * 150;
    const ny = by + Math.sin(nAngle) * 120;
    nodes.push({{ id: node.id, label: node.label, x: nx, y: ny, r: 28, color: branch.color + 'cc', textColor: '#fff', type: 'node', paper: node.paper }});
    edges.push({{ from: branch.id, to: node.id, color: branch.color, label: '' }});
  }});
}});

// Cross-paper connections
if (data.connections) {{
  data.connections.forEach(conn => {{
    edges.push({{ from: conn.from, to: conn.to, color: '#f1c40f44', label: conn.label, dashed: true }});
  }});
}}

function getNode(id) {{ return nodes.find(n => n.id === id); }}

function drawWrappedText(text, x, y, maxWidth, lineHeight, color) {{
  ctx.fillStyle = color;
  const words = text.split(' ');
  let line = '';
  const lines = [];
  words.forEach(word => {{
    const test = line + word + ' ';
    if (ctx.measureText(test).width > maxWidth && line) {{
      lines.push(line.trim());
      line = word + ' ';
    }} else {{ line = test; }}
  }});
  lines.push(line.trim());
  const startY = y - ((lines.length - 1) * lineHeight) / 2;
  lines.forEach((l, i) => {{
    ctx.fillText(l, x, startY + i * lineHeight);
  }});
}}

function draw() {{
  ctx.clearRect(0, 0, W, H);

  // Background
  const grad = ctx.createRadialGradient(cx, cy, 0, cx, cy, W * 0.7);
  grad.addColorStop(0, '#0f0f2e');
  grad.addColorStop(1, '#0a0a1a');
  ctx.fillStyle = grad;
  ctx.fillRect(0, 0, W, H);

  // Draw edges
  edges.forEach(edge => {{
    const from = getNode(edge.from);
    const to = getNode(edge.to);
    if (!from || !to) return;
    ctx.beginPath();
    ctx.strokeStyle = edge.color || '#ffffff44';
    ctx.lineWidth = edge.dashed ? 1.5 : 2;
    if (edge.dashed) ctx.setLineDash([5, 5]);
    else ctx.setLineDash([]);
    ctx.moveTo(from.x, from.y);
    ctx.lineTo(to.x, to.y);
    ctx.stroke();
    ctx.setLineDash([]);

    // Edge label
    if (edge.label) {{
      ctx.font = '10px Arial';
      ctx.fillStyle = '#f1c40f99';
      ctx.textAlign = 'center';
      ctx.fillText(edge.label, (from.x + to.x) / 2, (from.y + to.y) / 2 - 6);
    }}
  }});

  // Draw nodes
  nodes.forEach(node => {{
    // Glow
    const glow = ctx.createRadialGradient(node.x, node.y, 0, node.x, node.y, node.r * 1.5);
    glow.addColorStop(0, node.color + '44');
    glow.addColorStop(1, 'transparent');
    ctx.fillStyle = glow;
    ctx.beginPath();
    ctx.arc(node.x, node.y, node.r * 1.5, 0, Math.PI * 2);
    ctx.fill();

    // Circle
    ctx.beginPath();
    ctx.arc(node.x, node.y, node.r, 0, Math.PI * 2);
    ctx.fillStyle = node.color;
    ctx.fill();
    ctx.strokeStyle = node.type === 'central' ? '#fff' : node.color + 'ff';
    ctx.lineWidth = node.type === 'central' ? 3 : 1.5;
    ctx.stroke();

    // Text
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    const fontSize = node.type === 'central' ? 11 : node.type === 'branch' ? 10 : 9;
    ctx.font = `bold ${{fontSize}}px Arial`;
    drawWrappedText(node.label, node.x, node.y, node.r * 1.7, fontSize + 3, node.textColor);
  }});
}}

draw();

// Tooltip on hover
canvas.addEventListener('mousemove', e => {{
  const rect = canvas.getBoundingClientRect();
  const mx = e.clientX - rect.left;
  const my = e.clientY - rect.top;
  let found = false;
  nodes.forEach(node => {{
    const dx = mx - node.x, dy = my - node.y;
    if (Math.sqrt(dx*dx + dy*dy) < node.r) {{
      tooltip.style.display = 'block';
      tooltip.style.left = (e.clientX + 10) + 'px';
      tooltip.style.top = (e.clientY - 30) + 'px';
      tooltip.innerHTML = node.paper ? `<b>${{node.label}}</b><br><i>${{node.paper}}</i>` : `<b>${{node.label}}</b>`;
      found = true;
    }}
  }});
  if (!found) tooltip.style.display = 'none';
}});

// Drag nodes
let dragging = null, dragOffX = 0, dragOffY = 0;
canvas.addEventListener('mousedown', e => {{
  const rect = canvas.getBoundingClientRect();
  const mx = e.clientX - rect.left, my = e.clientY - rect.top;
  nodes.forEach(node => {{
    const dx = mx - node.x, dy = my - node.y;
    if (Math.sqrt(dx*dx + dy*dy) < node.r) {{
      dragging = node; dragOffX = dx; dragOffY = dy;
    }}
  }});
}});
canvas.addEventListener('mousemove', e => {{
  if (!dragging) return;
  const rect = canvas.getBoundingClientRect();
  dragging.x = e.clientX - rect.left - dragOffX;
  dragging.y = e.clientY - rect.top - dragOffY;
  draw();
}});
canvas.addEventListener('mouseup', () => {{ dragging = null; }});
</script>
</body>
</html>
""", height=540)

            if st.button("🗑️ Clear Mind Map", key="clear_mindmap"):
                st.session_state.mindmap_data = None
                st.rerun()

# ── TAB 7: FOCUS MODE ────────────────────
with t7:
    st.header("🎯 Focus Mode")
    st.caption("One section. All feedback. Full coach. No distractions.")

    # Load Emma's feedback
    focus_emma_items = []
    try:
        focus_emma_items = list(get_mongo_db()["comps_feedback"].find({}, {"_id": 0}))
    except Exception as e:
        st.warning(f"Could not load Emma's feedback: {e}")

    # Build section list from Emily + Emma
    focus_emily_by_section = {}
    for tid, ctx in lab_context.items():
        for sec in task_to_sections.get(tid, ["General"]):
            focus_emily_by_section.setdefault(sec, []).append({
                "reviewer": "Emily", "task_id": tid,
                "feedback": ctx["comment"], "action_type": "substantive",
                "priority": "high", "status": "pending", "estimated_minutes": "",
            })

    focus_emma_by_section = {}
    for item in focus_emma_items:
        sec = item.get("section", "General")
        focus_emma_by_section.setdefault(sec, []).append(item)

    all_focus_sections = sorted(set(list(focus_emily_by_section.keys()) + list(focus_emma_by_section.keys())))

    # ── Section picker ──
    focus_col1, focus_col2 = st.columns([3, 1])
    focus_section = focus_col1.selectbox("Choose a section to work on:", all_focus_sections, key="focus_section_select")
    focus_reviewer = focus_col2.selectbox("Reviewer:", ["All", "Emily", "Emma Tsui"], key="focus_reviewer_select")

    focus_items = []
    if focus_reviewer in ("All", "Emily"):
        focus_items += focus_emily_by_section.get(focus_section, [])
    if focus_reviewer in ("All", "Emma Tsui"):
        focus_items += focus_emma_by_section.get(focus_section, [])

    st.divider()

    if not focus_items:
        st.info("No feedback for this section/reviewer combination.")
    else:
        priority_color = {"high": "#e74c3c", "medium": "#f39c12", "low": "#27ae60", "none": "#2ecc71"}
        type_icon = {"quick_fix": "⚡", "clarification": "💬", "substantive": "📝", "major": "🏗️", "none": "✅"}

        # ── Feedback cards ──
        st.subheader(f"📋 Feedback for: {focus_section}")
        for item in focus_items:
            reviewer = item.get("reviewer", "Emily")
            badge = "🔵 Emily" if reviewer == "Emily" else "🟣 Emma Tsui"
            atype = item.get("action_type", "substantive")
            priority = item.get("priority", "medium")
            color = priority_color.get(priority, "#888")
            icon = type_icon.get(atype, "📋")
            mins = item.get("estimated_minutes", "")
            feedback_text = item.get("feedback", item.get("comment", ""))
            st.markdown(
                f'<div style="border-left:4px solid {color};background:#1a1a2e;'
                f'border-radius:8px;padding:12px 16px;margin:6px 0;color:#f0e6c8;">'
                f'<span style="font-size:0.8rem;color:#aaa;">{badge} · {icon} {atype}'
                f'{f" · ~{mins}min" if mins else ""} · '
                f'<span style="color:{color};">{"🔴" if priority=="high" else "🟡" if priority=="medium" else "🟢"} {priority}</span></span><br><br>'
                f'<span style="font-size:0.95rem;line-height:1.6;">{feedback_text}</span>'
                f'</div>',
                unsafe_allow_html=True
            )

        st.divider()

        # ── Draft area ──
        focus_draft_key = f"focus_draft_{focus_section}"
        st.subheader("✍️ Your Draft Response")
        focus_saved = st.session_state.saved_responses.get(focus_draft_key, "")
        focus_draft = st.text_area(
            "",
            value=focus_saved,
            key=f"focus_textarea_{focus_section}",
            height=220,
            placeholder="Write your response to this feedback here...",
            label_visibility="collapsed"
        )
        if st.button("💾 Save Draft (+10 XP)", key=f"focus_save_{focus_section}", use_container_width=True):
            st.session_state.saved_responses[focus_draft_key] = focus_draft
            st.session_state.last_worked_section = focus_section
            st.session_state.last_worked_date = datetime.now().strftime("%b %d, %Y at %I:%M %p")
            old_rank = get_rank(st.session_state.xp)
            st.session_state.xp += 10
            new_rank = get_rank(st.session_state.xp)
            if new_rank[0] != old_rank[0]:
                st.session_state.rank_up_title = new_rank[1]
            st.session_state.celebration_xp = 10
            save_all_progress()
            st.success("Draft saved! ⚡")
            st.rerun()

    # ── GOOGLE DOC EMBED ──────────────────────────────────
    st.divider()
    st.subheader("📝 Google Doc Editor")

    gdoc_url = st.text_input(
        "Paste your Google Doc URL:",
        value=st.session_state.get("gdoc_url", ""),
        placeholder="https://docs.google.com/document/d/YOUR_DOC_ID/edit",
        key="gdoc_url_input"
    )

    if gdoc_url != st.session_state.get("gdoc_url", ""):
        st.session_state.gdoc_url = gdoc_url

    if gdoc_url:
        # Convert any sharing URL to an embeddable URL
        if "/edit" in gdoc_url:
            embed_url = gdoc_url.split("/edit")[0] + "/edit"
        elif "/view" in gdoc_url:
            embed_url = gdoc_url.split("/view")[0] + "/edit"
        else:
            embed_url = gdoc_url

        components.html(
            f'<iframe src="{embed_url}" width="100%" height="700" '
            f'style="border:1px solid #f1c40f;border-radius:8px;" '
            f'allow="autoplay" frameborder="0"></iframe>',
            height=710
        )
        st.caption("Make sure the doc is shared with 'Anyone with the link can edit' for full editing access.")
    else:
        st.info("Paste a Google Doc link above to edit it here. Set sharing to 'Anyone with the link can edit'.")

    # ── EXPORT & DAILY UPDATE ──────────────────────────────
    st.divider()
    exp_col1, exp_col2 = st.columns(2)

    # ── Export All Drafts ──
    with exp_col1:
        st.subheader("📤 Export All Drafts")

        # Collect all saved focus drafts
        all_drafts = {
            k.replace("focus_draft_", ""): v
            for k, v in st.session_state.saved_responses.items()
            if k.startswith("focus_draft_") and v.strip()
        }

        if all_drafts:
            today = datetime.now().strftime("%B %d, %Y")
            lines = [
                "=" * 60,
                "🦇 THE DARK KNIGHT OF PUBLIC HEALTH",
                "COMPREHENSIVE EXAM — FOCUS MODE DRAFT RESPONSES",
                f"Exported: {today}",
                "=" * 60, ""
            ]

            # Group by paper using Emma's section→paper mapping
            paper_map = {}
            for item in focus_emma_items:
                paper_map[item.get("section", "")] = item.get("paper", "General")

            grouped = {}
            for section, draft in sorted(all_drafts.items()):
                paper = paper_map.get(section, "General")
                grouped.setdefault(paper, []).append((section, draft))

            for paper, entries in sorted(grouped.items()):
                lines += [f"\n{'─' * 50}", f"📄 {paper}", f"{'─' * 50}"]
                for section, draft in entries:
                    lines += [f"\n## {section}\n", draft, ""]

            export_text = "\n".join(lines)

            st.download_button(
                label="⬇️ Download All Drafts (.txt)",
                data=export_text,
                file_name=f"comps_drafts_{datetime.now().strftime('%Y%m%d')}.txt",
                mime="text/plain",
                use_container_width=True
            )

            # Printable HTML version
            html_sections = ""
            for paper, entries in sorted(grouped.items()):
                html_sections += f"<h2 style='color:#1a1a2e;border-bottom:2px solid #f1c40f;padding-bottom:6px'>{paper}</h2>"
                for section, draft in entries:
                    html_sections += f"""
                    <div style='margin:16px 0;padding:16px;border-left:4px solid #f1c40f;background:#fafafa;border-radius:6px;'>
                        <h3 style='margin:0 0 8px 0;color:#333'>{section}</h3>
                        <p style='white-space:pre-wrap;margin:0;color:#444;line-height:1.7'>{draft}</p>
                    </div>"""

            printable_html = f"""<!DOCTYPE html><html><head>
<title>Comps Draft Responses — {today}</title>
<style>body{{font-family:Georgia,serif;max-width:800px;margin:40px auto;color:#333}}
@media print{{button{{display:none}}}}</style></head>
<body>
<h1 style='color:#1a1a2e'>🦇 Comprehensive Exam Draft Responses</h1>
<p style='color:#888'>Exported: {today}</p><hr>
{html_sections}
<br><button onclick='window.print()' style='padding:10px 24px;background:#1a1a2e;color:#f1c40f;border:none;border-radius:6px;cursor:pointer;font-size:1rem'>🖨️ Print</button>
</body></html>"""

            st.download_button(
                label="🖨️ Download Printable HTML",
                data=printable_html,
                file_name=f"comps_drafts_{datetime.now().strftime('%Y%m%d')}.html",
                mime="text/html",
                use_container_width=True
            )
            st.caption(f"{len(all_drafts)} sections with saved drafts")
        else:
            st.info("No drafts saved yet — write responses in Focus Mode above.")

    # ── Daily Update ──
    with exp_col2:
        st.subheader("📅 Daily Update")

        # Track daily activity
        if "daily_activity" not in st.session_state:
            st.session_state.daily_activity = {}

        today_key = datetime.now().strftime("%Y-%m-%d")
        today_sections = st.session_state.daily_activity.get(today_key, [])

        # Show what's been saved today
        today_drafts = {
            k.replace("focus_draft_", ""): v
            for k, v in st.session_state.saved_responses.items()
            if k.startswith("focus_draft_") and v.strip()
        }

        total_sections = len(all_focus_sections)
        done_sections = len(today_drafts)

        st.metric("Sections with Drafts", f"{done_sections} / {total_sections}")

        if today_drafts:
            st.markdown("**Sections addressed:**")
            for sec in sorted(today_drafts.keys()):
                st.markdown(f"✅ {sec}")

        st.write("")
        if st.button("🦇 Generate Daily Update", use_container_width=True, key="daily_update_btn"):
            if today_drafts:
                with st.spinner("Generating your daily update..."):
                    try:
                        import anthropic
                        client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])

                        drafts_summary = "\n\n".join(
                            f"**{sec}:**\n{draft[:300]}{'...' if len(draft) > 300 else ''}"
                            for sec, draft in sorted(today_drafts.items())
                        )

                        update_response = client.messages.create(
                            model="claude-sonnet-4-20250514",
                            max_tokens=500,
                            messages=[{"role": "user", "content": f"""You are a PhD writing coach. Based on these draft responses written today for a comprehensive exam, write a brief daily progress update (3-5 sentences) that:
1. Notes what sections were addressed
2. Highlights the strongest work
3. Identifies what still needs attention
4. Ends with one motivating sentence (Batman-themed)

Today's drafts:
{drafts_summary}"""}]
                        )
                        update_text = update_response.content[0].text
                        st.session_state["latest_daily_update"] = f"{today_key}: {update_text}"
                        st.success(update_text)
                    except Exception as e:
                        st.error(f"Daily update failed: {e}")
            else:
                st.warning("Save some drafts first!")

        if st.session_state.get("latest_daily_update"):
            with st.expander("📋 Last Update"):
                st.write(st.session_state["latest_daily_update"])

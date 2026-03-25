import streamlit as st
import streamlit.components.v1 as components
import json
import os
import time
import pandas as pd
from datetime import datetime, timedelta
import random
from pathlib import Path
import base64
def get_audio_b64():
    audio_path = Path(__file__).parent / "static" / "bat.sting.wav"
    with open(audio_path, "rb") as f:
        return base64.b64encode(f.read()).decode()

# --- MUST BE FIRST ---
st.set_page_config(layout="wide", page_title="The Dark Knight of Public Health", page_icon="🦇")

# --- SERVE STATIC FOLDER ===
st.markdown(
    '<link rel="preload" href="app/static/bat_sting.wav" as="audio">',
    unsafe_allow_html=True
)
# ─────────────────────────────────────────────
# 1. PERSISTENCE
# ─────────────────────────────────────────────
SAVE_FILE = "slayer_progress.json"

def save_all_progress():
    data = {
        "xp": st.session_state.xp,
        "completed_tasks": list(st.session_state.completed_tasks),
        "saved_responses": st.session_state.saved_responses,
        "task_timers": st.session_state.task_timers,
        "custom_rewards": st.session_state.custom_rewards,
        "claimed_rewards": st.session_state.claimed_rewards,
        "custom_vault": st.session_state.custom_vault,
        "last_task_id": st.session_state.get("last_task_id", "")
    }
    with open(SAVE_FILE, "w") as f:
        json.dump(data, f)

def load_all_progress():
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, "r") as f:
                d = json.load(f)
                return (d.get("xp", 0), set(d.get("completed_tasks", [])),
                        d.get("saved_responses", {}), d.get("task_timers", {}),
                        d.get("custom_rewards", []), d.get("claimed_rewards", []),
                        d.get("custom_vault", {}),
                        d.get("last_task_id", ""))
        except:
            pass
    return 0, set(), {}, {}, [], [], {}, ""

# ─────────────────────────────────────────────
# 2. INITIALIZATION
# ─────────────────────────────────────────────
if 'initialized' not in st.session_state:
    xp, comp_tasks, resps, timers, custom_r, claimed, vault, last_task = load_all_progress()
    st.session_state.xp = xp
    st.session_state.completed_tasks = comp_tasks
    st.session_state.saved_responses = resps
    st.session_state.task_timers = timers
    st.session_state.custom_rewards = custom_r
    st.session_state.claimed_rewards = claimed
    st.session_state.custom_vault = vault if vault else {
        "🚀 Openers": ["Building upon...", "Premised on...", "Centrally to..."],
        "⚖️ Contrast": ["Notwithstanding", "Conversely", "Paradoxically"],
        "🎯 Result":   ["Consequently", "Accordingly", "Ultimately"],
        "💎 Synonyms": ["Elucidate (Show)", "Bolster (Help)", "Nexus (Link)"]
    }
    st.session_state.last_task_id = last_task
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

# ─────────────────────────────────────────────
# 10. SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.header("🦇 Bat-Computer")
    st.metric("Total XP", st.session_state.xp)
    render_rank_badge(st.session_state.xp)

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

    sidebar_pomodoro()

    if not st.session_state.get('timer_running'):
        if st.button("🚀 Start 25m Sprint", use_container_width=True):
            st.session_state.target_time = datetime.now() + timedelta(minutes=25)
            st.session_state.timer_running = True
            st.rerun()
    else:
        if st.button("🛑 Stop & Save Progress", use_container_width=True):
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
            st.session_state.target_time = None
            st.rerun()

    st.divider()
    st.subheader("📓 Response Lab")
    all_ids = sorted(list(set(
        list(lab_context.keys()) +
        [i['id'] for cat in master_tasks.values() for i in cat]
    )))
    last = st.session_state.get("last_task_id", "")
    default_ix = all_ids.index(last) if last in all_ids else 0
    sel_id = st.selectbox("Task ID:", all_ids, index=default_ix, key="sidebar_lab_id")
    if st.session_state.get("last_task_id") != sel_id:
        st.session_state.last_task_id = sel_id
        save_all_progress()
    ctx = lab_context.get(sel_id, {"comment": "Address feedback.", "prefill": ""})
    st.warning(f"📝 {ctx['comment']}")
    val = st.session_state.saved_responses.get(sel_id, ctx['prefill'])
    draft = st.text_area(
        "Your response:",
        value=val,
        key=f"sidebar_lab_{sel_id}",
        height=200
    )
    #
      # ← ADD THIS LINE HERE
    st.session_state.saved_responses[sel_id] = st.session_state.get(f"sidebar_lab_{sel_id}", val)
    save_all_progress()
    if st.button("✅ Save Draft", use_container_width=True, key="save_draft_btn"):
        current_text = st.session_state.get(f"sidebar_lab_{sel_id}", val)
        if current_text:
            st.session_state.saved_responses[sel_id] = current_text
            save_all_progress()
            st.success(f"Saved: {current_text[:50]}...")
        else:
            st.warning("Nothing to save — type your response first.")
        st.rerun()

    st.divider()
    if st.button("💾 Force Manual Save"):
        save_all_progress()
        st.success("Data Secured! 🦇")

# ─────────────────────────────────────────────
# 11. TABS
# ─────────────────────────────────────────────
t1, t2, t3, t4 = st.tabs([
    "⚔️ Task Board", "📓 Response Lab", "🎁 Rewards & Analytics", "📜 Writing Guide"
])

# ── TAB 1: TASK BOARD ──────────────────────
st.write(os.listdir(Path(__file__).parent / "static"))
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
                        audio_b64 = get_audio_b64()
                        st.write(Path(__file__).parent / "static" / "bat.sting.wav")
                        components.html(
                            f"""
                            <div style='position:fixed;top:0;left:0;width:100vw;height:100vh;background:rgba(255,215,0,0.1);border:10px solid #FFD700;pointer-events:none;z-index:999;'></div>
                            <script>
                                 const audio = new Audio('data:audio/wav;base64,{audio_b64}');
                                audio.play().catch(e => console.log('Audio blocked:', e));
                            </script>
                            """,
                            height=0
                         )
                        st.toast(f"Justice Served! +{m['pts']} XP", icon="🦇")
                        time.sleep(1.2)
                    
                    # Save & Refresh
                    save_all_progress()
                    st.rerun()  # Fixed: was missing ()
# ── TAB 2: RESPONSE LAB ────────────────────
with t2:
    st.header("📓 Strategic Response Lab")
    q3, s3 = random.choice(BATMAN_QUOTES)
    st.markdown(quote_box(q3, s3), unsafe_allow_html=True)

    all_ids = sorted(list(set(
        list(lab_context.keys()) +
        [i['id'] for cat in master_tasks.values() for i in cat]
    )))
    sel_id = st.selectbox("Select Task ID:", all_ids)
    ctx    = lab_context.get(sel_id, {"comment": "Address feedback.", "prefill": ""})
    st.warning(f"**Emily's Feedback:** {ctx['comment']}")
    val   = st.session_state.saved_responses.get(sel_id, ctx['prefill'])
    draft = st.text_area("Finalized Response:", value=val, key=f"lab_{sel_id}", height=200)
    if st.button("Mark Draft Complete (+10 XP)"):
        st.session_state.saved_responses[sel_id] = draft
        old_rank = get_rank(st.session_state.xp)
        st.session_state.xp += 10
        new_rank = get_rank(st.session_state.xp)
        if new_rank[0] != old_rank[0]:
            st.session_state.rank_up_title = new_rank[1]
        st.session_state.celebration_xp = 10
        save_all_progress()
        st.success("Draft Secured! ⚡")
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
                    client = anthropic.Anthropic()
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
                client = anthropic.Anthropic()
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
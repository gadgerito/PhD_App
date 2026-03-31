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
from comps_coach import render_floating_button, render_comps_modal
@st.cache_data
def get_audio_b64():
    audio_path = Path(__file__).parent / "static" / "bat.sting.wav"
    with open(audio_path, "rb") as f:
        return base64.b64encode(f.read()).decode()

# --- MUST BE FIRST ---
st.set_page_config(layout="wide", page_title="The Dark Knight of Public Health", page_icon="🦇")

# ── PASSWORD GATE ──
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    # Inject skyline via JS (st.markdown sanitizes SVG; components.html escapes to parent)
    components.html("""
<script>
(function(){
  var pw = window.parent;
  var pdoc = pw.document;

  // Dark background on the whole page
  var styleEl = pdoc.getElementById('login-style');
  if (!styleEl) {
    styleEl = pdoc.createElement('style');
    styleEl.id = 'login-style';
    styleEl.textContent = [
      'body, .stApp { background:#0a0a14 !important; }',
      '.stApp > div { background:#0a0a14 !important; }',
      '[data-testid="stAppViewContainer"] { background:#0a0a14 !important; }',
      '[data-testid="stHeader"] { background:#0a0a14 !important; }',
      '.stTextInput input { background:rgba(255,255,255,0.06) !important; color:#f0e6c8 !important;',
      '  border:1px solid rgba(241,196,15,0.35) !important; border-radius:2px !important; }',
      '.stTextInput input::placeholder { color:#666 !important; }',
      '.stButton > button { background:transparent !important; color:#f1c40f !important;',
      '  border:1px solid #f1c40f !important; border-radius:2px !important; font-family:monospace !important;',
      '  letter-spacing:0.1em !important; }',
      '.stButton > button:hover { background:rgba(241,196,15,0.1) !important; }',
      'h2 { color:#f1c40f !important; font-family:monospace !important; letter-spacing:0.15em !important; }',
      '.stAlert { background:rgba(180,30,30,0.2) !important; border:1px solid #7A1A1A !important; }',
    ].join('');
    pdoc.head.appendChild(styleEl);
  }

  // Build NYC skyline SVG if not already there
  if (pdoc.getElementById('nyc-skyline')) return;
  var ns = 'http://www.w3.org/2000/svg';

  function r(x,y,w,h,fill,op) {
    var el = pdoc.createElementNS(ns,'rect');
    el.setAttribute('x',x); el.setAttribute('y',y);
    el.setAttribute('width',w); el.setAttribute('height',h);
    if(fill) el.setAttribute('fill',fill);
    if(op)   el.setAttribute('opacity',op);
    return el;
  }
  function tri(pts,fill) {
    var el = pdoc.createElementNS(ns,'polygon');
    el.setAttribute('points',pts);
    el.setAttribute('fill',fill);
    return el;
  }

  var svg = pdoc.createElementNS(ns,'svg');
  svg.setAttribute('viewBox','0 0 1440 340');
  svg.setAttribute('preserveAspectRatio','xMidYMax meet');
  svg.style.cssText = 'position:fixed;bottom:0;left:0;width:100%;pointer-events:none;z-index:0;opacity:0.22;';
  svg.id = 'nyc-skyline';

  // ── Far layer ──
  var g1 = pdoc.createElementNS(ns,'g');
  g1.setAttribute('fill','#c8d4e8'); g1.setAttribute('opacity','0.4');
  [[0,280,60,60],[30,258,22,82],[65,268,45,72],[112,260,38,80],[152,265,50,75],
   [205,270,40,70],[248,255,55,85],[305,262,42,78],[352,252,60,88],[415,268,44,72],
   [462,258,38,82],[502,250,52,90],[558,262,46,78],[606,255,40,85],[650,268,55,72],
   [708,252,42,88],[752,260,38,80],[793,245,50,95],[846,262,44,78],[894,255,60,85],
   [957,268,40,72],[1000,250,46,90],[1048,258,38,82],[1090,265,55,75],[1148,252,42,88],
   [1192,262,48,78],[1244,255,40,85],[1286,268,58,72],[1347,250,44,90],[1394,260,46,80]
  ].forEach(function(d){ g1.appendChild(r(d[0],d[1],d[2],d[3])); });
  svg.appendChild(g1);

  // ── Mid layer ──
  var g2 = pdoc.createElementNS(ns,'g');
  g2.setAttribute('fill','#9aaece'); g2.setAttribute('opacity','0.55');
  // Financial left
  [[0,262,28,78],[6,242,14,22],[32,238,34,102],[40,215,16,25],[68,248,30,92],
   [74,228,14,22],[100,240,40,100],[110,215,18,27],[142,252,28,88],[172,232,36,108],
   [182,208,14,25],[210,245,32,95],
   // Midtown left
   [292,228,38,112],[304,202,12,28],[332,240,44,100],[346,215,16,27],[378,232,36,108],
   [416,222,50,118],[430,195,20,30],[470,238,34,102],
   // Empire-ish
   [542,182,42,158],[554,158,18,26],[560,145,6,15],[586,215,30,125],
   // Chrysler-ish
   [642,198,36,142],[650,175,20,25],[680,225,28,115],
   // Midtown right
   [712,218,40,122],[722,195,18,25],[754,232,34,108],[790,212,48,128],[802,185,22,30],[840,228,36,112],
   // Upper
   [882,238,44,102],[928,225,38,115],[938,202,16,25],[968,242,32,98],
   // Right cluster
   [1012,250,36,90],[1050,235,44,105],[1060,212,20,25],[1096,245,38,95],
   [1136,232,46,108],[1150,208,18,25],[1184,248,34,92],[1220,240,40,100],
   [1230,218,16,24],[1262,252,36,88],[1300,238,48,102],[1314,215,18,25],
   [1350,250,36,90],[1388,242,54,98]
  ].forEach(function(d){ g2.appendChild(r(d[0],d[1],d[2],d[3])); });
  svg.appendChild(g2);

  // ── Front layer ──
  var g3 = pdoc.createElementNS(ns,'g');
  g3.setAttribute('fill','#7888b0'); g3.setAttribute('opacity','0.8');
  // Financial / lower manhattan
  [[0,272,22,68],[25,255,18,85],[46,245,26,95],[52,225,12,22],[74,252,20,88],
   [96,238,32,102],[102,215,18,26],[130,258,24,82],[156,242,28,98],[162,222,14,22],
   [186,250,22,90],[210,235,30,105],[220,212,12,25],
   // Midtown
   [262,220,36,120],[274,195,14,27],[300,235,28,105],[330,212,44,128],[342,188,18,26],
   // One WTC
   [376,98,30,242],[382,80,18,20],[386,62,8,20],[408,192,22,148],
   // Empire State
   [432,155,48,185],[444,132,24,25],[450,115,12,20],[452,103,6,14],[482,208,26,132],
   // Chrysler
   [512,170,44,170],[522,145,24,27],[558,222,22,118],
   // Dense mid
   [582,208,38,132],[592,185,18,25],[622,222,30,118],[654,202,42,138],[666,180,18,25],
   [698,218,34,122],[708,195,14,25],
   // Right midtown
   [734,212,40,128],[746,188,16,26],[776,225,32,115],[810,208,46,132],[822,185,20,26],
   [858,222,36,118],
   // Upper
   [896,235,28,105],[926,218,40,122],[936,195,18,26],[968,228,32,112],
   [1002,242,30,98],[1034,228,38,112],[1044,205,16,25],[1074,240,28,100],
   [1104,225,44,115],[1116,202,18,25],[1150,238,32,102],[1184,222,40,118],
   [1194,200,18,22],[1226,235,34,105],[1262,245,28,95],[1292,228,44,112],
   [1304,208,18,22],[1338,242,30,98],[1370,228,42,112],[1414,240,28,100]
  ].forEach(function(d){ g3.appendChild(r(d[0],d[1],d[2],d[3])); });

  // Chrysler spire triangle
  g3.appendChild(tri('534,118 546,118 540,94','#7888b0'));
  // One WTC top taper
  g3.appendChild(tri('376,98 406,98 391,60','#7888b0'));

  svg.appendChild(g3);

  // Ground line
  var ground = r(0,337,1440,4,'#5868a0',0.7);
  svg.appendChild(ground);

  pdoc.body.appendChild(svg);

  // ── Animated plane — shape-tracing skywriter ──
  if (pdoc.getElementById('login-plane')) return;

  var W = pw.innerWidth  || 1440;
  var H = pw.innerHeight || 900;
  var CX = W * 0.5;
  var CY = H * 0.38;

  var planeWrap = pdoc.createElement('div');
  planeWrap.id = 'login-plane';
  planeWrap.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;pointer-events:none;z-index:2;';

  var planeSvg = pdoc.createElementNS(ns,'svg');
  planeSvg.setAttribute('viewBox','0 0 120 40');
  planeSvg.style.cssText = 'position:absolute;width:80px;height:27px;opacity:0.6;filter:drop-shadow(0 0 4px rgba(180,200,255,0.5));transform-origin:45px 20px;';

  var fuse = pdoc.createElementNS(ns,'ellipse');
  fuse.setAttribute('cx','55'); fuse.setAttribute('cy','20'); fuse.setAttribute('rx','45'); fuse.setAttribute('ry','7'); fuse.setAttribute('fill','#a0b4d0');
  planeSvg.appendChild(fuse);
  var nose = pdoc.createElementNS(ns,'polygon');
  nose.setAttribute('points','100,20 115,22 115,18'); nose.setAttribute('fill','#b8cce0');
  planeSvg.appendChild(nose);
  var tail = pdoc.createElementNS(ns,'polygon');
  tail.setAttribute('points','10,20 18,20 14,8'); tail.setAttribute('fill','#8898b8');
  planeSvg.appendChild(tail);
  var wing = pdoc.createElementNS(ns,'polygon');
  wing.setAttribute('points','50,20 70,20 80,32 40,32'); wing.setAttribute('fill','#8898b8');
  planeSvg.appendChild(wing);
  var stab = pdoc.createElementNS(ns,'polygon');
  stab.setAttribute('points','18,20 28,20 30,27 16,27'); stab.setAttribute('fill','#7888a8');
  planeSvg.appendChild(stab);
  var wins = pdoc.createElementNS(ns,'rect');
  wins.setAttribute('x','58'); wins.setAttribute('y','15'); wins.setAttribute('width','28'); wins.setAttribute('height','4'); wins.setAttribute('rx','2'); wins.setAttribute('fill','rgba(220,235,255,0.5)');
  planeSvg.appendChild(wins);

  planeWrap.appendChild(planeSvg);
  pdoc.body.appendChild(planeWrap);

  var trail = pdoc.createElement('canvas');
  trail.id = 'login-plane-trail';
  trail.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;pointer-events:none;z-index:1;';
  trail.width = W; trail.height = H;
  pdoc.body.appendChild(trail);
  var tctx = trail.getContext('2d');

  // ── Shape generators ──────────────────────────────────
  function ptDist(a,b){ var dx=b.x-a.x,dy=b.y-a.y; return Math.sqrt(dx*dx+dy*dy); }
  function lerp(a,b,t){ return a+(b-a)*t; }

  // Densify a path so every segment is ≤ maxSeg px
  function densify(pts, maxSeg) {
    var out = [];
    for (var i = 0; i < pts.length-1; i++) {
      var p0=pts[i], p1=pts[i+1], d=ptDist(p0,p1), steps=Math.max(1,Math.ceil(d/maxSeg));
      for (var j=0;j<steps;j++) out.push({x:lerp(p0.x,p1.x,j/steps), y:lerp(p0.y,p1.y,j/steps)});
    }
    out.push(pts[pts.length-1]);
    return out;
  }

  function genHeart(cx,cy,sc) {
    var pts=[],N=200;
    for(var i=0;i<=N;i++){
      var t=(i/N)*Math.PI*2-Math.PI;
      pts.push({x:cx+sc*16*Math.pow(Math.sin(t),3),
                y:cy-sc*(13*Math.cos(t)-5*Math.cos(2*t)-2*Math.cos(3*t)-Math.cos(4*t))});
    }
    return densify(pts,4);
  }

  function genInfinity(cx,cy,a) {
    var pts=[],N=200;
    for(var i=0;i<=N;i++){
      var t=(i/N)*Math.PI*2;
      var d=1+Math.sin(t)*Math.sin(t);
      pts.push({x:cx+a*Math.cos(t)/d, y:cy+a*0.5*Math.sin(2*t)/d});
    }
    return densify(pts,4);
  }

  function genStar(cx,cy,R,r) {
    var raw=[],N=5;
    for(var i=0;i<N;i++){
      var a1=(i*2*Math.PI/N)-Math.PI/2, a2=((i+0.5)*2*Math.PI/N)-Math.PI/2;
      raw.push({x:cx+R*Math.cos(a1),y:cy+R*Math.sin(a1)});
      raw.push({x:cx+r*Math.cos(a2),y:cy+r*Math.sin(a2)});
    }
    raw.push(raw[0]);
    return densify(raw,4);
  }

  function genBat(cx,cy,sc) {
    // Simplified bat: two swept wing arcs, ears, body
    var pts=[], N=50;
    // Right wing arc
    for(var i=0;i<=N;i++){
      var t=(i/N)*Math.PI;
      pts.push({x:cx+sc*(0.25+1.1*Math.sin(t)), y:cy+sc*(-0.3+0.65*Math.sin(2*t)-0.25*Math.cos(t))});
    }
    // Right ear
    pts.push({x:cx+sc*0.38,y:cy-sc*0.85});
    pts.push({x:cx+sc*0.52,y:cy-sc*1.25});
    pts.push({x:cx+sc*0.22,y:cy-sc*0.95});
    // Top centre
    pts.push({x:cx,y:cy-sc*0.78});
    // Left ear
    pts.push({x:cx-sc*0.22,y:cy-sc*0.95});
    pts.push({x:cx-sc*0.52,y:cy-sc*1.25});
    pts.push({x:cx-sc*0.38,y:cy-sc*0.85});
    // Left wing arc
    for(var i=N;i>=0;i--){
      var t=(i/N)*Math.PI;
      pts.push({x:cx-sc*(0.25+1.1*Math.sin(t)), y:cy+sc*(-0.3+0.65*Math.sin(2*t)-0.25*Math.cos(t))});
    }
    pts.push(pts[0]);
    return densify(pts,4);
  }

  function genCap(cx,cy,sc) {
    // Mortarboard: flat square top + wide brim + tassel drop
    var s=sc, pts=[];
    // Brim (wide flat line)
    pts.push({x:cx-s*1.5,y:cy});
    pts.push({x:cx+s*1.5,y:cy});
    // Right side down to cap top-right
    pts.push({x:cx+s,y:cy});
    pts.push({x:cx+s,y:cy+s*0.55});
    pts.push({x:cx-s,y:cy+s*0.55});
    pts.push({x:cx-s,y:cy});
    // Back to brim centre, then tassel drop
    pts.push({x:cx,y:cy});
    pts.push({x:cx+s*0.35,y:cy});
    pts.push({x:cx+s*0.35,y:cy+s*0.9});
    pts.push({x:cx+s*0.55,y:cy+s*1.25});
    // Swing back and close
    pts.push({x:cx+s*0.35,y:cy+s*0.9});
    pts.push({x:cx+s*0.35,y:cy});
    pts.push({x:cx-s*1.5,y:cy});
    return densify(pts,4);
  }

  // Build transit (fast straight-ish path between shapes)
  function genTransit(from,to) {
    var pts=[], N=30;
    // Slight arc through the midpoint above both
    var midX=(from.x+to.x)/2, midY=Math.min(from.y,to.y)-80;
    for(var i=0;i<=N;i++){
      var t=i/N;
      // Quadratic bezier
      var bx=lerp(lerp(from.x,midX,t),lerp(midX,to.x,t),t);
      var by=lerp(lerp(from.y,midY,t),lerp(midY,to.y,t),t);
      pts.push({x:bx,y:by});
    }
    return pts;
  }

  var sc = Math.min(W,H)*0.013;
  var shapes = [
    {pts:genHeart(CX,CY,sc),      r:255,g:120,b:150},
    {pts:genBat(CX,CY,sc*7),      r:241,g:196,b: 15},
    {pts:genStar(CX,CY,sc*13,sc*5.5), r:255,g:235,b:120},
    {pts:genInfinity(CX,CY,sc*16),r:130,g:200,b:255},
    {pts:genCap(CX,CY,sc*10),     r:160,g:235,b:185},
  ];

  var SHAPE_SPEED   = 95;   // px/s — slow deliberate skywriting
  var TRANSIT_SPEED = 420;  // px/s — fast repositioning

  var shapeIdx = 0, segIdx = 0, segT = 0;
  var inTransit = false, transitPts = null;
  var trailDots = [];
  var planeX = shapes[0].pts[0].x;
  var planeY = shapes[0].pts[0].y;
  var planeAngle = 0;
  var lastTs = null;

  function currentPts(){ return inTransit ? transitPts : shapes[shapeIdx].pts; }

  function startTransit(){
    var nextIdx=(shapeIdx+1)%shapes.length;
    var cur=currentPts(), from=cur[cur.length-1];
    var to=shapes[nextIdx].pts[0];
    transitPts=genTransit(from,to);
    inTransit=true; segIdx=0; segT=0;
    // Mark all current trail dots as fading
    for(var i=0;i<trailDots.length;i++) trailDots[i].fading=true;
  }

  function advancePlane(ts) {
    if(!lastTs){ lastTs=ts; requestAnimationFrame(advancePlane); return; }
    var dt=Math.min((ts-lastTs)/1000, 0.05);
    lastTs=ts;

    var pts=currentPts();
    var speed=inTransit?TRANSIT_SPEED:SHAPE_SPEED;
    var distLeft=speed*dt;

    while(distLeft>0){
      if(segIdx>=pts.length-1){
        // Reached end of segment list
        if(inTransit){
          shapeIdx=(shapeIdx+1)%shapes.length;
          inTransit=false; segIdx=0; segT=0;
          pts=currentPts();
        } else {
          startTransit(); pts=currentPts(); segIdx=0; segT=0;
        }
        break;
      }
      var p0=pts[segIdx], p1=pts[segIdx+1];
      var seg=ptDist(p0,p1);
      if(seg<0.5){ segIdx++; continue; }
      var traveled=segT*seg, remaining=seg-traveled;
      if(distLeft>=remaining){ distLeft-=remaining; segIdx++; segT=0; }
      else { segT+=distLeft/seg; distLeft=0; }
    }

    if(segIdx<pts.length-1){
      var p0=pts[segIdx],p1=pts[segIdx+1];
      planeX=lerp(p0.x,p1.x,segT);
      planeY=lerp(p0.y,p1.y,segT);
      planeAngle=Math.atan2(p1.y-p0.y, p1.x-p0.x);
    }

    // Trail dots
    if(!inTransit){
      var sh=shapes[shapeIdx];
      trailDots.push({x:planeX,y:planeY,a:0.72,fading:false,r:sh.r,g:sh.g,b:sh.b});
    }

    // Draw
    tctx.clearRect(0,0,trail.width,trail.height);
    for(var i=trailDots.length-1;i>=0;i--){
      var d=trailDots[i];
      if(d.fading) d.a-=0.004;
      if(d.a<=0){ trailDots.splice(i,1); continue; }
      tctx.beginPath();
      tctx.arc(d.x,d.y,2.8,0,Math.PI*2);
      tctx.fillStyle='rgba('+d.r+','+d.g+','+d.b+','+d.a.toFixed(3)+')';
      tctx.fill();
    }

    // Plane position + rotation
    planeSvg.style.left=(planeX-40)+'px';
    planeSvg.style.top =(planeY-14)+'px';
    planeSvg.style.transform='rotate('+(planeAngle*180/Math.PI)+'deg)';

    requestAnimationFrame(advancePlane);
  }
  requestAnimationFrame(advancePlane);

  // ── Batmobile Mini-Game ────────────────────────────────
  if (!pdoc.getElementById('batmobile-wrap')) {
    var BW = 160, BH = 56;
    var LANE_Y = [H - BH - 28, H - BH - 82];  // lower, upper lanes
    var bmX = W * 0.25;

    // ── Build Batmobile SVG ──
    var bmWrap = pdoc.createElement('div');
    bmWrap.id = 'batmobile-wrap';
    bmWrap.style.cssText = 'position:fixed;pointer-events:none;z-index:6;transition:top 0.18s ease;';

    var bmSvg = pdoc.createElementNS(ns,'svg');
    bmSvg.setAttribute('viewBox','0 0 160 56');
    bmSvg.style.cssText = 'width:'+BW+'px;height:'+BH+'px;filter:drop-shadow(0 2px 8px rgba(241,196,15,0.5));';

    var exGlow = pdoc.createElementNS(ns,'ellipse');
    exGlow.setAttribute('cx','16'); exGlow.setAttribute('cy','36'); exGlow.setAttribute('rx','10'); exGlow.setAttribute('ry','5'); exGlow.setAttribute('fill','rgba(241,120,15,0.55)');
    bmSvg.appendChild(exGlow);
    var body = pdoc.createElementNS(ns,'polygon');
    body.setAttribute('points','14,38 28,20 55,14 95,12 128,16 148,24 152,38'); body.setAttribute('fill','#1a1a1a');
    bmSvg.appendChild(body);
    var canopy = pdoc.createElementNS(ns,'ellipse');
    canopy.setAttribute('cx','90'); canopy.setAttribute('cy','18'); canopy.setAttribute('rx','26'); canopy.setAttribute('ry','9'); canopy.setAttribute('fill','#111'); canopy.setAttribute('stroke','#333'); canopy.setAttribute('stroke-width','1');
    bmSvg.appendChild(canopy);
    var cHigh = pdoc.createElementNS(ns,'ellipse');
    cHigh.setAttribute('cx','88'); cHigh.setAttribute('cy','15'); cHigh.setAttribute('rx','16'); cHigh.setAttribute('ry','4'); cHigh.setAttribute('fill','rgba(180,220,255,0.12)');
    bmSvg.appendChild(cHigh);
    var fin = pdoc.createElementNS(ns,'polygon');
    fin.setAttribute('points','14,38 22,20 35,14 28,38'); fin.setAttribute('fill','#222');
    bmSvg.appendChild(fin);
    var scoop = pdoc.createElementNS(ns,'polygon');
    scoop.setAttribute('points','148,24 160,28 160,36 148,36'); scoop.setAttribute('fill','#111');
    bmSvg.appendChild(scoop);
    var hlight = pdoc.createElementNS(ns,'ellipse');
    hlight.setAttribute('cx','152'); hlight.setAttribute('cy','30'); hlight.setAttribute('rx','5'); hlight.setAttribute('ry','3'); hlight.setAttribute('fill','rgba(255,240,180,0.9)');
    bmSvg.appendChild(hlight);
    var beam = pdoc.createElementNS(ns,'polygon');
    beam.setAttribute('points','157,28 220,10 220,50 157,32'); beam.setAttribute('fill','rgba(255,240,180,0.05)');
    bmSvg.appendChild(beam);
    var trim = pdoc.createElementNS(ns,'polyline');
    trim.setAttribute('points','30,20 55,14 95,12 128,16 148,24'); trim.setAttribute('fill','none'); trim.setAttribute('stroke','#f1c40f'); trim.setAttribute('stroke-width','1.2'); trim.setAttribute('opacity','0.7');
    bmSvg.appendChild(trim);
    [[38,42,12],[118,42,12]].forEach(function(w){
      var wc = pdoc.createElementNS(ns,'circle');
      wc.setAttribute('cx',w[0]); wc.setAttribute('cy',w[1]); wc.setAttribute('r',w[2]); wc.setAttribute('fill','#111'); wc.setAttribute('stroke','#333'); wc.setAttribute('stroke-width','2');
      bmSvg.appendChild(wc);
      var hub = pdoc.createElementNS(ns,'circle');
      hub.setAttribute('cx',w[0]); hub.setAttribute('cy',w[1]); hub.setAttribute('r',5); hub.setAttribute('fill','#2a2a2a'); hub.setAttribute('stroke','#f1c40f'); hub.setAttribute('stroke-width','0.8');
      bmSvg.appendChild(hub);
    });
    var wGlow1 = pdoc.createElementNS(ns,'circle');
    wGlow1.setAttribute('cx','38'); wGlow1.setAttribute('cy','42'); wGlow1.setAttribute('r','13'); wGlow1.setAttribute('fill','none'); wGlow1.setAttribute('stroke','rgba(241,196,15,0.3)'); wGlow1.setAttribute('stroke-width','2');
    bmSvg.appendChild(wGlow1);
    var wGlow2 = pdoc.createElementNS(ns,'circle');
    wGlow2.setAttribute('cx','118'); wGlow2.setAttribute('cy','42'); wGlow2.setAttribute('r','13'); wGlow2.setAttribute('fill','none'); wGlow2.setAttribute('stroke','rgba(241,196,15,0.3)'); wGlow2.setAttribute('stroke-width','2');
    bmSvg.appendChild(wGlow2);
    bmWrap.appendChild(bmSvg);
    pdoc.body.appendChild(bmWrap);

    // ── Road ──
    var roadDiv = pdoc.createElement('div');
    roadDiv.id = 'bm-road';
    roadDiv.style.cssText = 'position:fixed;bottom:0;left:0;width:100%;height:'+( BH + 36)+'px;'
      +'background:linear-gradient(180deg,transparent,rgba(10,14,28,0.55));pointer-events:none;z-index:2;';
    pdoc.body.appendChild(roadDiv);

    // Lane divider dashes drawn on canvas
    var gameCanvas = pdoc.createElement('canvas');
    gameCanvas.id = 'bm-game-canvas';
    gameCanvas.style.cssText = 'position:fixed;top:0;left:0;pointer-events:none;z-index:5;';
    gameCanvas.width = W; gameCanvas.height = H;
    pdoc.body.appendChild(gameCanvas);
    var gctx = gameCanvas.getContext('2d');

    // ── Game state ──
    var GS = {
      phase: 'idle',   // idle | countdown | playing | gameover
      score: 0, hiScore: 0, lives: 3,
      lane: 0,         // 0=lower 1=upper
      bmVel: 0,        // horizontal px/s; player controls with ←→
      obstacles: [],   // {x, lane, kind, w}
      coins: [],       // {x, lane, pulse}
      spawnCd: 1.8, coinCd: 2.2,
      baseSpeed: 160,  // obstacle approach speed
      speed: 160,
      time: 0,
      countdown: 3, cdTimer: 0,
      hitCool: 0,      // invincibility after hit
      flashAlpha: 0,   // red flash on hit
      combo: 0, comboTimer: 0,
      laneChangeCd: 0,
    };

    var keys = {};
    pw.addEventListener('keydown', function(e){
      var k = e.key;
      if (!keys[k]) {
        keys[k] = true;
        if (k === ' ') {
          if (GS.phase === 'idle' || GS.phase === 'gameover') startGame();
        }
        if (GS.phase === 'playing') {
          if (k === 'ArrowUp'   && GS.lane === 0 && GS.laneChangeCd <= 0) { GS.lane = 1; GS.laneChangeCd = 0.22; }
          if (k === 'ArrowDown' && GS.lane === 1 && GS.laneChangeCd <= 0) { GS.lane = 0; GS.laneChangeCd = 0.22; }
        }
      }
      if (['ArrowUp','ArrowDown','ArrowLeft','ArrowRight',' '].indexOf(k) > -1) e.preventDefault();
    });
    pw.addEventListener('keyup', function(e){ keys[e.key] = false; });

    function startGame() {
      GS.phase = 'countdown'; GS.countdown = 3; GS.cdTimer = 1;
      GS.score = 0; GS.lives = 3; GS.lane = 0;
      GS.obstacles = []; GS.coins = [];
      GS.speed = GS.baseSpeed; GS.spawnCd = 1.8; GS.coinCd = 2.2;
      GS.time = 0; GS.hitCool = 0; GS.flashAlpha = 0; GS.combo = 0;
      GS.bmVel = 0;
      bmX = W * 0.18;
    }

    function spawnObstacle() {
      var lane = Math.random() > 0.5 ? 1 : 0;
      var kind = Math.random();
      GS.obstacles.push({ x: W + 60, lane: lane,
        kind: kind < 0.5 ? 'car' : kind < 0.8 ? 'bomb' : 'riddler', w: 52 });
    }
    function spawnCoin() {
      GS.coins.push({ x: W + 30, lane: Math.random() > 0.5 ? 1 : 0, pulse: 0 });
    }

    function bmCollides(obj) {
      if (obj.lane !== GS.lane) return false;
      var bmLeft = bmX + 20, bmRight = bmX + BW - 20;
      var obLeft = obj.x, obRight = obj.x + obj.w;
      return bmRight > obLeft && bmLeft < obRight;
    }
    function coinCollides(c) {
      if (c.lane !== GS.lane) return false;
      var bmCx = bmX + BW * 0.5;
      return Math.abs(bmCx - c.x) < 55;
    }

    var bmLastTs = null, glowPhase = 0;

    function gameLoop(ts) {
      if (!bmLastTs) { bmLastTs = ts; requestAnimationFrame(gameLoop); return; }
      var dt = Math.min((ts - bmLastTs) / 1000, 0.05);
      bmLastTs = ts;
      var sw = pw.innerWidth || 1440;
      glowPhase += dt * 4;

      // ── Phase logic ──
      if (GS.phase === 'countdown') {
        GS.cdTimer -= dt;
        if (GS.cdTimer <= 0) {
          GS.countdown--;
          if (GS.countdown <= 0) { GS.phase = 'playing'; }
          else GS.cdTimer = 1;
        }
      }

      if (GS.phase === 'playing') {
        GS.time += dt;
        GS.score = Math.floor(GS.time * 10);
        // Ramp difficulty
        GS.baseSpeed = 160 + Math.floor(GS.time / 10) * 20;
        GS.speed = GS.baseSpeed;

        // Spawn
        GS.spawnCd -= dt;
        if (GS.spawnCd <= 0) { spawnObstacle(); GS.spawnCd = Math.max(0.9, 1.8 - GS.time * 0.015); }
        GS.coinCd -= dt;
        if (GS.coinCd <= 0) { spawnCoin(); GS.coinCd = 2.5 + Math.random() * 1.5; }

        // Move obstacles
        for (var i = GS.obstacles.length-1; i >= 0; i--) {
          GS.obstacles[i].x -= GS.speed * dt;
          if (GS.obstacles[i].x < -120) { GS.obstacles.splice(i,1); continue; }
          if (GS.hitCool <= 0 && bmCollides(GS.obstacles[i])) {
            GS.lives--; GS.hitCool = 1.8; GS.flashAlpha = 0.55;
            GS.combo = 0; GS.comboTimer = 0;
            GS.obstacles.splice(i,1);
            if (GS.lives <= 0) { GS.phase = 'gameover'; GS.hiScore = Math.max(GS.hiScore, GS.score); }
            continue;
          }
        }
        // Move coins
        for (var j = GS.coins.length-1; j >= 0; j--) {
          GS.coins[j].x -= GS.speed * dt * 0.85;
          GS.coins[j].pulse += dt * 3;
          if (GS.coins[j].x < -60) { GS.coins.splice(j,1); continue; }
          if (coinCollides(GS.coins[j])) {
            GS.combo++; GS.comboTimer = 3;
            var bonus = GS.combo >= 3 ? 50 : 20;
            GS.score += bonus;
            GS.coins.splice(j,1);
          }
        }
        if (GS.hitCool > 0) GS.hitCool -= dt;
        if (GS.comboTimer > 0) GS.comboTimer -= dt; else if (GS.combo > 0) GS.combo = 0;
        if (GS.laneChangeCd > 0) GS.laneChangeCd -= dt;
        GS.flashAlpha = Math.max(0, GS.flashAlpha - dt * 1.2);
      }

      // ── Move batmobile (←→ keys control car, ↑↓ switch lanes) ──
      if (GS.phase === 'playing') {
        var targetVel = 0;
        if (keys['ArrowRight']) targetVel = 420;
        else if (keys['ArrowLeft']) targetVel = -420;
        var accel = 1800;
        if (GS.bmVel < targetVel) GS.bmVel = Math.min(GS.bmVel + accel * dt, targetVel);
        else if (GS.bmVel > targetVel) GS.bmVel = Math.max(GS.bmVel - accel * dt, targetVel);
      } else {
        GS.bmVel = 0;
      }
      bmX += GS.bmVel * dt;
      if (bmX < 0) bmX = 0;
      if (bmX > sw - BW) bmX = sw - BW;

      // Position
      var targetY = LANE_Y[GS.lane];
      bmWrap.style.left = bmX + 'px';
      bmWrap.style.top  = targetY + 'px';
      // Blink during invincibility
      bmSvg.style.opacity = (GS.hitCool > 0 && Math.floor(GS.hitCool * 10) % 2 === 0) ? '0.25' : '0.95';

      // Wheel glow
      var gA = (0.1 + 0.3 * Math.abs(Math.sin(glowPhase))).toFixed(2);
      wGlow1.setAttribute('stroke','rgba(241,196,15,'+gA+')');
      wGlow2.setAttribute('stroke','rgba(241,196,15,'+gA+')');
      var exA = (0.3 + 0.25 * Math.abs(Math.sin(glowPhase * 2.1))).toFixed(2);
      exGlow.setAttribute('fill','rgba(241,120,15,'+exA+')');

      // ── Draw canvas ──
      gctx.clearRect(0, 0, gameCanvas.width, gameCanvas.height);

      // Lane divider dashes
      var divY = (LANE_Y[0] + LANE_Y[1]) / 2 + BH * 0.5;
      gctx.setLineDash([28, 18]);
      gctx.strokeStyle = 'rgba(100,130,180,0.18)';
      gctx.lineWidth = 2;
      gctx.beginPath(); gctx.moveTo(0, divY); gctx.lineTo(sw, divY);
      gctx.stroke(); gctx.setLineDash([]);

      // Draw obstacles
      GS.obstacles.forEach(function(o) {
        var oy = LANE_Y[o.lane] + 4;
        if (o.kind === 'car') {
          // Enemy car silhouette
          gctx.fillStyle = '#8B1A1A';
          gctx.fillRect(o.x, oy + 14, 80, 26);
          gctx.fillStyle = '#AA2222';
          gctx.fillRect(o.x + 8, oy + 4, 56, 18);
          // Wheels
          [[14,40],[66,40]].forEach(function(w){
            gctx.beginPath(); gctx.arc(o.x+w[0], oy+w[1], 9, 0, Math.PI*2);
            gctx.fillStyle='#222'; gctx.fill();
            gctx.strokeStyle='#555'; gctx.lineWidth=1.5; gctx.stroke();
          });
          // Headlights (facing left = threat)
          gctx.fillStyle='rgba(255,60,60,0.8)';
          gctx.fillRect(o.x, oy+17, 5, 8);
          // Warning glow
          var warnA = 0.15 + 0.15 * Math.abs(Math.sin(glowPhase * 3));
          gctx.beginPath(); gctx.ellipse(o.x+40,oy+28,44,22,0,0,Math.PI*2);
          gctx.fillStyle='rgba(200,30,30,'+warnA+')'; gctx.fill();
        } else if (o.kind === 'bomb') {
          gctx.beginPath(); gctx.arc(o.x+20, oy+22, 18, 0, Math.PI*2);
          gctx.fillStyle='#1a1a1a'; gctx.fill();
          gctx.strokeStyle='#e74c3c'; gctx.lineWidth=2; gctx.stroke();
          // Fuse
          gctx.beginPath(); gctx.moveTo(o.x+28,oy+6); gctx.quadraticCurveTo(o.x+36,oy,o.x+34,oy-8);
          gctx.strokeStyle='#f39c12'; gctx.lineWidth=2; gctx.stroke();
          // Spark
          var spkA = 0.6 + 0.4*Math.abs(Math.sin(glowPhase*5));
          gctx.beginPath(); gctx.arc(o.x+34,oy-8,4,0,Math.PI*2);
          gctx.fillStyle='rgba(255,200,0,'+spkA+')'; gctx.fill();
          gctx.font='bold 13px monospace'; gctx.fillStyle='#e74c3c'; gctx.textAlign='center';
          gctx.fillText('💣',o.x+20,oy+27);
        } else {
          // Riddler ?
          gctx.beginPath(); gctx.arc(o.x+20,oy+22,18,0,Math.PI*2);
          gctx.fillStyle='#0a2a0a'; gctx.fill();
          gctx.strokeStyle='#2ecc71'; gctx.lineWidth=2; gctx.stroke();
          gctx.font='bold 20px monospace'; gctx.fillStyle='#2ecc71'; gctx.textAlign='center';
          gctx.fillText('?',o.x+20,oy+29);
        }
      });

      // Draw coins (bat signal tokens)
      GS.coins.forEach(function(c) {
        var cy2 = LANE_Y[c.lane] + BH*0.5;
        var pA = 0.55 + 0.3*Math.abs(Math.sin(c.pulse));
        gctx.beginPath(); gctx.arc(c.x,cy2,14,0,Math.PI*2);
        gctx.fillStyle='rgba(241,196,15,0.15)'; gctx.fill();
        gctx.strokeStyle='rgba(241,196,15,'+pA+')'; gctx.lineWidth=2; gctx.stroke();
        gctx.font='14px serif'; gctx.textAlign='center';
        gctx.fillStyle='rgba(241,196,15,'+pA+')';
        gctx.fillText('🦇',c.x,cy2+5);
      });

      // ── HUD ──
      gctx.textAlign='left';
      if (GS.phase === 'playing' || GS.phase === 'gameover') {
        // Lives
        gctx.font = 'bold 15px monospace';
        gctx.fillStyle = 'rgba(241,196,15,0.85)';
        gctx.fillText('LIVES:', 18, 36);
        for (var l=0; l<3; l++) {
          gctx.font = '16px serif';
          gctx.fillStyle = l < GS.lives ? 'rgba(241,196,15,0.9)' : 'rgba(80,80,80,0.5)';
          gctx.fillText('🦇', 80 + l*24, 36);
        }
        // Score
        gctx.font = 'bold 15px monospace'; gctx.textAlign='right';
        gctx.fillStyle='rgba(241,196,15,0.85)';
        gctx.fillText('SCORE: '+GS.score, sw-18, 36);
        // Combo
        if (GS.combo >= 2 && GS.comboTimer > 0) {
          gctx.textAlign='center';
          gctx.font='bold 13px monospace';
          gctx.fillStyle='rgba(255,220,80,'+(0.6+0.3*Math.abs(Math.sin(glowPhase*3)))+')';
          gctx.fillText('x'+GS.combo+' COMBO!', sw/2, 36);
        }
        // Speed indicator
        gctx.textAlign='left';
        gctx.font='11px monospace'; gctx.fillStyle='rgba(100,150,255,0.5)';
        gctx.fillText('← → speed   ↑ ↓ lane   ⎵ start', 18, H-8);
      }

      // Countdown overlay
      if (GS.phase === 'countdown') {
        gctx.textAlign='center';
        gctx.font='bold 88px monospace';
        var cA = Math.min(1, GS.cdTimer * 2);
        gctx.fillStyle='rgba(241,196,15,'+cA+')';
        gctx.fillText(GS.countdown, sw/2, H/2);
        gctx.font='bold 16px monospace'; gctx.fillStyle='rgba(241,196,15,0.5)';
        gctx.fillText('GET READY', sw/2, H/2 + 50);
      }

      // Idle overlay
      if (GS.phase === 'idle') {
        gctx.textAlign='center';
        var pulseA = 0.45 + 0.3*Math.abs(Math.sin(glowPhase*0.9));
        gctx.font='bold 14px monospace'; gctx.fillStyle='rgba(241,196,15,'+pulseA+')';
        gctx.fillText('⎵  PRESS SPACE TO PLAY  ⎵', sw/2, LANE_Y[0]-10);
        gctx.font='11px monospace'; gctx.fillStyle='rgba(180,200,255,0.38)';
        gctx.fillText('↑ ↓ change lane   ← → adjust speed', sw/2, LANE_Y[0]+8);
        if (GS.hiScore > 0) {
          gctx.fillStyle='rgba(241,196,15,0.4)';
          gctx.fillText('BEST: '+GS.hiScore, sw/2, LANE_Y[0]+26);
        }
      }

      // Game over overlay
      if (GS.phase === 'gameover') {
        gctx.textAlign='center';
        gctx.fillStyle='rgba(0,0,0,0.45)';
        gctx.fillRect(0, H/2-70, sw, 140);
        gctx.font='bold 42px monospace'; gctx.fillStyle='rgba(200,40,40,0.95)';
        gctx.fillText('GAME OVER', sw/2, H/2-12);
        gctx.font='18px monospace'; gctx.fillStyle='rgba(241,196,15,0.85)';
        gctx.fillText('Score: '+GS.score+'  |  Best: '+GS.hiScore, sw/2, H/2+28);
        var goA = 0.5+0.4*Math.abs(Math.sin(glowPhase*1.5));
        gctx.font='bold 13px monospace'; gctx.fillStyle='rgba(241,196,15,'+goA+')';
        gctx.fillText('⎵  PRESS SPACE TO PLAY AGAIN  ⎵', sw/2, H/2+62);
      }

      // Hit flash
      if (GS.flashAlpha > 0) {
        gctx.fillStyle='rgba(200,30,30,'+GS.flashAlpha.toFixed(2)+')';
        gctx.fillRect(0,0,sw,H);
      }

      if (pdoc.getElementById('batmobile-wrap')) requestAnimationFrame(gameLoop);
    }
    requestAnimationFrame(gameLoop);
  }

})();
</script>
""", height=0)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("## 🦇 Bat-Computer Access")
        pwd = st.text_input("Password", type="password", label_visibility="collapsed",
                            placeholder="Enter access code...")
        if st.button("Enter the Batcave", use_container_width=True):
            if pwd == st.secrets["app_password"]:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Access Denied. This is not your city.")
    st.stop()

# Clean up any login page DOM injections (dark background, skyline, plane) that persist across reruns
components.html("""
<script>
(function(){
  var pd = window.parent.document;
  ['login-style','nyc-skyline','login-plane','login-plane-trail',
   'batmobile-wrap','bm-game-canvas','bm-road'].forEach(function(id){
    var el = pd.getElementById(id);
    if (el) el.remove();
  });
  // Also nuke any leftover trail canvas (no id, but parent is body and it's a canvas)
  // The plane animation cleans its own canvas, so nothing extra needed
})();
</script>
""", height=0)

# -- MongoDB --
@st.cache_resource
def get_mongo_db():
    client = MongoClient(
        st.secrets["mongo_uri"],
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
            return 0, set(), {}, {}, [], [], {}, "", "", "", [], {}, {}, {}, {}, {}, {}, []

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
        d.get("section_timers", {}),
        d.get("active_timer", {}),
        d.get("race", {}),
        d.get("daily_briefing", {}),
        d.get("synonym_cache", {}),
        d.get("briefing_cache", {}),
        d.get("coach_log", [])
        )
    except Exception as e:
        st.error(f"MongoDB connection error: {e}")
        return 0, set(), {}, {}, [], [], {}, "", "", "", [], {}, {}, {}, {}, {}, {}, []


def save_all_progress():
    try:
        db = get_db()
        target_str = st.session_state.target_time.isoformat() if st.session_state.get("target_time") else None
        pause_str = st.session_state.pause_start.isoformat() if st.session_state.get("pause_start") else None
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
            "section_timers": st.session_state.get("section_timers", {}),
            "active_timer": {
                "running": st.session_state.get("timer_running", False),
                "paused": st.session_state.get("timer_paused", False),
                "target_time": target_str,
                "pause_start": pause_str,
                "mission": st.session_state.get("active_mission", "")
            },
            "race": {
                "active": st.session_state.get("race_active", False),
                "end_time": st.session_state.race_end_time.isoformat() if st.session_state.get("race_active") and st.session_state.get("race_end_time") else None,
                "target": st.session_state.get("race_target", 5),
                "completed": st.session_state.get("race_completed", 0),
                "bonus": st.session_state.get("race_bonus", 0),
                "streak": st.session_state.get("race_streak", 0),
                "best_streak": st.session_state.get("race_best_streak", 0),
            },
            "daily_briefing": st.session_state.get("daily_briefing", {}),
            "synonym_cache": st.session_state.get("synonym_cache", {}),
            "briefing_cache": st.session_state.get("briefing_cache", {}),
            "coach_log": st.session_state.get("coach_log", []),
        }
        db.replace_one({"_id": "main"}, data, upsert=True)
    except Exception as e:
        st.error(f"Save failed: {e}")
def generate_daily_briefing():
    """Generate a daily Robin mission brief and cache it to DB. Returns briefing text."""
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
        today = datetime.now().strftime("%Y-%m-%d")

        _rank_icon, _rank_title, _ = get_rank(st.session_state.xp)
        _section_timers = st.session_state.get("section_timers", {})
        _last_section = st.session_state.get("last_worked_section", "")
        _last_date = st.session_state.get("last_worked_date", "")

        _top_sections = sorted(_section_timers.items(), key=lambda x: x[1], reverse=True)[:3]
        _sections_str = ", ".join(f"{s} ({m}min)" for s, m in _top_sections) if _top_sections else "none yet"

        _fb_cache = st.session_state.get("comps_feedback_cache", [])
        _pending_count = sum(1 for i in _fb_cache if i.get("status") == "pending")
        _pending_str = f"{_pending_count} feedback items still pending" if _pending_count else "no pending feedback items"

        _last_draft_excerpt = ""
        if _last_section:
            _d = st.session_state.saved_responses.get(f"focus_draft_{_last_section}", "")
            if _d:
                _last_draft_excerpt = f"\nLast draft excerpt ({_last_section}): \"{_d[:200]}\""

        prompt = (
            f"You are Robin, loyal sidekick to the Caped Candidate (a PhD student finishing their dissertation). "
            f"Generate a sharp 3-4 sentence morning mission brief.\n\n"
            f"Status: {st.session_state.xp} XP — Rank: {_rank_title}\n"
            f"Top sections worked: {_sections_str}\n"
            f"Last session: {_last_section or 'none'} on {_last_date or 'unknown'}\n"
            f"Committee feedback: {_pending_str}\n"
            f"{_last_draft_excerpt}\n\n"
            f"Brief: acknowledge recent progress, name today's top priority, close with one motivating line. "
            f"Sound like Robin — sharp, loyal, energetic. 3-4 sentences max."
        )

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}]
        )
        text = response.content[0].text
        st.session_state.daily_briefing = {"date": today, "text": text}
        save_all_progress()
        return text
    except Exception as e:
        return f"(Briefing unavailable: {e})"


def _log_coach_exchange(question: str, answer: str, section_name: str = ""):
    """Append a single user question + Robin answer to the persistent coach log."""
    entry = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "section": section_name or st.session_state.get("last_worked_section", "Unknown"),
        "question": question,
        "answer": answer,
    }
    st.session_state.setdefault("coach_log", []).append(entry)
    save_all_progress()


# ─────────────────────────────────────────────
# 2. INITIALIZATION
# ─────────────────────────────────────────────
if 'initialized' not in st.session_state:
    xp, comp_tasks, resps, timers, custom_r, claimed, vault, last_task, last_worked_section, last_worked_date, notebook, section_timers, active_timer, race_state, daily_briefing, synonym_cache, briefing_cache, coach_log = load_all_progress()
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
    st.session_state.section_timers = section_timers if section_timers else {}

    #OFFLINE TIMER CATCH-UP LOGIC
    if active_timer.get("running"):
        target_str= active_timer.get("target_time")
        if target_str:
            target_time = datetime.fromisoformat(target_str)
            # If it wasn't paused and time is up, auto-log it!
            if not active_timer.get("paused") and datetime.now() >= target_time:
                task_id = active_timer.get("mission", "").split(":")[0]
                if task_id:
                    st.session_state.task_timers[task_id]= st.session_state.task_timers.get(task_id, 0) + 25
                st.session_state.xp += 25
                st.session_state.celebration_xp = 25
                st.session_state.pomodoro_done = True
                # Call save immediately to update DB and clear the active timer
                save_all_progress() 
            else:
                # Still running or paused, restore state
                st.session_state.timer_running = True
                st.session_state.timer_paused = active_timer.get("paused", False)
                st.session_state.target_time = target_time
                st.session_state.active_mission = active_timer.get("mission", "")
                if active_timer.get("pause_start"):
                    st.session_state.pause_start = datetime.fromisoformat(active_timer["pause_start"])

    # Restore race state if still within time window
    if race_state.get("active"):
        _rs_end_str = race_state.get("end_time")
        if _rs_end_str:
            _rs_end = datetime.fromisoformat(_rs_end_str)
            if datetime.now() < _rs_end:
                st.session_state.race_active = True
                st.session_state.race_end_time = _rs_end
                st.session_state.race_target = race_state.get("target", 5)
                st.session_state.race_completed = race_state.get("completed", 0)
                st.session_state.race_bonus = race_state.get("bonus", 0)
                st.session_state.race_streak = race_state.get("streak", 0)
                st.session_state.race_best_streak = race_state.get("best_streak", 0)

    # Cache all comps_feedback once per session
    try:
        st.session_state.comps_feedback_cache = list(get_mongo_db()["comps_feedback"].find({}, {"_id": 0}))
    except:
        st.session_state.comps_feedback_cache = []

    if 'noir_mode' not in st.session_state:
        st.session_state.noir_mode = False
    st.session_state.daily_briefing = daily_briefing
    st.session_state.synonym_cache = synonym_cache
    st.session_state.briefing_cache = briefing_cache
    st.session_state.coach_log = coach_log
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
if st.session_state.get('play_audio') or celebration_xp > 0:
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
# 3b. PROGRESS BADGES
# ─────────────────────────────────────────────
# Each badge: (id, icon, label, color, condition_fn(completed_set, master_tasks))
PROGRESS_BADGES = [
    ("first_strike",  "🥊", "First Strike",    "#e67e22", lambda c, m: len(c) >= 1),
    ("quick_draw",    "⚡", "Quick Draw",       "#f1c40f", lambda c, m: sum(1 for cat in m.values() for t in cat if t["type"] == "Quick Win" and t["id"] in c) >= 3),
    ("into_the_deep", "🔬", "Into the Deep",   "#2980b9", lambda c, m: sum(1 for cat in m.values() for t in cat if t["type"] == "Deep Work" and t["id"] in c) >= 5),
    ("oracle_eye",    "🔍", "Oracle's Eye",    "#8e44ad", lambda c, m: sum(1 for cat in m.values() for t in cat if t["type"] == "Resource Hunt" and t["id"] in c) >= 2),
    ("section_clear", "🏛️", "Section Clear",   "#1abc9c", lambda c, m: any(all(t["id"] in c for t in items) for items in m.values())),
    ("half_knight",   "🌓", "Half Knight",     "#34495e", lambda c, m: len(c) / max(sum(len(v) for v in m.values()), 1) >= 0.5),
    ("dark_knight",   "🦇", "The Dark Knight", "#f1c40f", lambda c, m: len(c) / max(sum(len(v) for v in m.values()), 1) >= 1.0),
]

def render_progress_badges(completed_set, master_tasks):
    earned = [(icon, label, color) for bid, icon, label, color, fn in PROGRESS_BADGES if fn(completed_set, master_tasks)]
    if not earned:
        return
    chips = "".join(
        f'<span style="display:inline-block;margin:2px 3px;padding:3px 9px;border-radius:12px;'
        f'font-size:0.72rem;font-weight:600;background:{col}22;border:1px solid {col};color:{col};">'
        f'{icon} {label}</span>'
        for icon, label, col in earned
    )
    st.markdown(
        f'<div style="margin:6px 0 4px 0;line-height:1.8;">{chips}</div>',
        unsafe_allow_html=True
    )

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

# ─────────────────────────────────────────────
# 5. ROBIN MISSION NAMES
# ─────────────────────────────────────────────
ROBIN_MISSIONS = {
    "Phase 1: The Heavy Lifting (Structural Editing)": [
        ("Operation: Knightfall", "For when you have to break down a massive, clunky chapter and rebuild it from the bones."),
        ("The Lazarus Protocol", "Resurrecting that paragraph you deleted three months ago because it actually makes sense now."),
        ("Architect of Arkham", "Reorganizing your Literature Review so it doesn't look like a madman's cell."),
        ("The Long Halloween", "For those grueling, multi-day editing sessions where you're hunting down one specific argument."),
    ],
    "Phase 2: The Data & Policy Check (Health Specifics)": [
        ("The Oracle Audit", "Verifying every single p-value and data point in your results section."),
        ("Project: Venom", "Strengthening your policy recommendations so they have enough 'punch' to actually change the system."),
        ("The Gotham Census", "Cleaning up your demographic tables and sample size descriptions."),
        ("Social Determinants of Justice", "Polishing the section where you argue for equity in the healthcare system."),
    ],
    "Phase 3: The Final Polish (Proofreading & Formatting)": [
        ("The Bat-Glare", "A final, cold, hard look at your bibliography to catch every missing comma or italicized journal title."),
        ("Neutralizing the Riddler", "Rewriting that one overly academic sentence that literally no one (not even you) understands."),
        ("The Wayne Foundation Grant", "Double-checking all your acknowledgments and funding citations."),
        ("Zero Hour", "The final read-through before you hit 'Submit' and disappear into the night (or just go to sleep)."),
    ],
    "Phase 4: Dealing with Advisors (Feedback)": [
        ("The Joker's Wild", "Processing that one piece of feedback from your committee that completely contradicts everything they said last month."),
        ("Squad Goals (Suicide Mission)", "Integrating the comments from the toughest member of your defense panel."),
        ("Commissioner Gordon's Signal", "Checking the latest emails from your chair to see what 'emergency' needs fixing now."),
    ],
}

# Maps EKT action_type → the Robin mission that best fits it
EKT_MISSION_MAP = {
    "quick_fix":     ("Neutralizing the Riddler",    "Rewriting the overly academic or unclear sentence so it actually says what you mean.",       "Phase 3: The Final Polish (Proofreading & Formatting)"),
    "clarification": ("Commissioner Gordon's Signal", "Responding directly to a committee question that needs a clear, targeted answer.",            "Phase 4: Dealing with Advisors (Feedback)"),
    "substantive":   ("The Long Halloween",           "Deep revision work — hunting down one specific argument and making it bulletproof.",          "Phase 1: The Heavy Lifting (Structural Editing)"),
    "major":         ("Operation: Knightfall",        "Breaking down a major section and rebuilding it from the bones. This one takes endurance.",   "Phase 1: The Heavy Lifting (Structural Editing)"),
}

# Maps master_tasks "type" field → Robin mission (same tuple format as EKT_MISSION_MAP)
TASK_TYPE_MISSION_MAP = {
    "Quick Win":     ("Neutralizing the Riddler",    "A targeted fix — clean it up, sharpen it, and move on. Precision over brute force.",         "Phase 3: The Final Polish (Proofreading & Formatting)"),
    "Deep Work":     ("Operation: Knightfall",       "Breaking down a heavy section and rebuilding it from the bones. This one takes endurance.",  "Phase 1: The Heavy Lifting (Structural Editing)"),
    "Resource Hunt": ("The Oracle Audit",            "Tracking down the right citation or data point and weaving it into the argument cleanly.",   "Phase 2: The Data & Policy Check (Health Specifics)"),
}

# Flat list for easy random selection or display
ROBIN_MISSIONS_FLAT = [
    (phase, name, desc)
    for phase, missions in ROBIN_MISSIONS.items()
    for name, desc in missions
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
_noir = st.session_state.get("noir_mode", False)

if not _noir:
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

<!-- Flying bats (3 at different heights/speeds) -->
<div class="fly-bat" style="top:9%;font-size:20px;animation-duration:14s;animation-delay:0s;"><span>🦇</span></div>
<div class="fly-bat" style="top:28%;font-size:13px;animation-duration:21s;animation-delay:-7s;opacity:0.45;"><span>🦇</span></div>
<div class="fly-bat" style="top:52%;font-size:16px;animation-duration:17s;animation-delay:-11s;opacity:0.35;"><span>🦇</span></div>
""", unsafe_allow_html=True)

else:
    st.markdown("""
<style>
/* ══ NOIR / E-INK MODE ══ */
.stApp { background:#F2EFE8 !important; color:#111111 !important; }
.bat-tagline { color:#555555; font-style:italic; font-size:1.2rem; margin-top:-18px; margin-bottom:4px; }
.rank-badge  { display:inline-block; padding:6px 16px; border-radius:2px; font-weight:bold;
               font-size:1.0rem; margin:4px 0; border:2px solid; }
.rank-next   { font-size:0.82rem; color:#555555; margin-top:2px; }

/* ── Buttons — stark ink, drop-shadow on hover ── */
.stButton>button {
    border-radius:2px; border:2px solid #111111;
    background:#F2EFE8; color:#111111; font-weight:bold;
    transition: all 0.12s ease;
    position: relative;
}
.stButton>button:hover {
    background: #E8E5DE !important;
    box-shadow: 3px 3px 0px #111111 !important;
    transform: translateY(-1px);
}
.stButton>button:active { transform: translate(1px,1px); box-shadow: 1px 1px 0px #111111 !important; }

/* ── Progress bars — solid black fill, no shimmer ── */
[data-testid="stProgressBar"] > div > div {
    background: #111111 !important;
    border-radius: 0px !important;
    animation: none !important;
}

/* ── Quote box — e-ink card ── */
.quote-wrap  { margin: 10px 0 18px 0; }
.quote-inner {
    background: #E8E5DE;
    border-left: 4px solid #111111; border-radius: 0px;
    padding: 14px 20px; color: #111111;
    font-style: italic; font-size: 1.05rem;
}
.quote-src { color:#5C4A1E; font-size:0.8rem; font-style:normal; font-weight:bold; margin-top:6px; }

/* ── Flying bats — ghostly, no flap animation ── */
.fly-bat {
    position:fixed; z-index:9990; pointer-events:none;
    animation: fly-across linear infinite;
    will-change: transform;
}
@keyframes fly-across {
    0%   { transform:translateX(-80px); opacity:0; }
    4%   { opacity:0.12; }
    96%  { opacity:0.12; }
    100% { transform:translateX(calc(100vw + 80px)); opacity:0; }
}
.fly-bat span { display:inline-block; }

/* ── Completed task row ── */
.task-done { animation: done-flash 0.6s ease-out; }
@keyframes done-flash {
    0%   { background: rgba(92,74,30,0.25); }
    100% { background: transparent; }
}

/* ── XP metric — sepia, no glow ── */
[data-testid="stMetricValue"] {
    color: #5C4A1E !important;
    text-shadow: none !important;
    animation: none !important;
}

/* ── Reward button — no pulse ── */
.reward-available .stButton>button { animation: none; }

/* ── Tabs — bold underline, no glow ── */
[data-baseweb="tab"] { transition: all 0.15s ease; }
[aria-selected="true"][data-baseweb="tab"] {
    font-weight: bold !important;
    text-shadow: none !important;
    border-bottom: 2px solid #111111 !important;
}

/* ── Rank card ── */
.rank-card {
    text-align:center; padding:8px 4px; border-radius:0px;
    border:2px solid; margin:2px;
}
.rank-card.unlocked { animation: none; }
</style>

<!-- Flying bats — ghostly -->
<div class="fly-bat" style="top:9%;font-size:20px;animation-duration:14s;animation-delay:0s;"><span>🦇</span></div>
<div class="fly-bat" style="top:28%;font-size:13px;animation-duration:21s;animation-delay:-7s;"><span>🦇</span></div>
<div class="fly-bat" style="top:52%;font-size:16px;animation-duration:17s;animation-delay:-11s;"><span>🦇</span></div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# 5b. BOUNCING BAT SIGNAL (window.parent escape — position:fixed inside st.markdown
#     is clipped to the component iframe, so we inject it directly into the real DOM)
# ─────────────────────────────────────────────
_bat_noir = "true" if _noir else "false"
components.html(f"""
<script>
(function(){{
  var pw;
  try {{ pw = window.parent; }} catch(e) {{ pw = window; }}
  var pdoc = pw.document;

  // Only create once — the rAF loop keeps running across Streamlit reruns
  if (pdoc.getElementById('bat-signal')) return;

  var ns = 'http://www.w3.org/2000/svg';
  var noirMode = {_bat_noir};

  // Wrapper div
  var wrap = pdoc.createElement('div');
  wrap.id = 'bat-signal';
  wrap.style.cssText = 'position:fixed;width:82px;height:82px;z-index:9999;'
    + 'pointer-events:none;display:flex;align-items:center;justify-content:center;'
    + 'border-radius:50%;';

  // Build SVG
  var svg = pdoc.createElementNS(ns,'svg');
  svg.setAttribute('viewBox','0 0 200 160');
  svg.style.cssText = noirMode
    ? 'width:72px;height:72px;opacity:0.6;'
    : 'width:68px;height:68px;filter:drop-shadow(0 0 8px rgba(241,196,15,0.8));';

  var ovalFill = noirMode ? '#2A2A2A' : '#1a1a1a';
  var batFill  = noirMode ? '#F2EFE8' : '#f1c40f';

  var oval = pdoc.createElementNS(ns,'ellipse');
  oval.setAttribute('cx','100'); oval.setAttribute('cy','82');
  oval.setAttribute('rx','96');  oval.setAttribute('ry','74');
  oval.setAttribute('fill', ovalFill);
  svg.appendChild(oval);

  var body = pdoc.createElementNS(ns,'path');
  body.setAttribute('d','M100,38 C100,38 94,28 82,28 C68,28 56,36 48,44 C38,53 34,60 30,62 C38,60 46,61 52,65 C44,70 36,80 34,92 C40,84 50,80 58,82 C56,86 54,92 55,100 C60,91 68,86 76,86 L80,100 C84,112 90,120 100,120 C110,120 116,112 120,100 L124,86 C132,86 140,91 145,100 C146,92 144,86 142,82 C150,80 160,84 166,92 C164,80 156,70 148,65 C154,61 162,60 170,62 C166,60 162,53 152,44 C144,36 132,28 118,28 C106,28 100,38 100,38 Z');
  body.setAttribute('fill', batFill);
  svg.appendChild(body);

  var e1 = pdoc.createElementNS(ns,'polygon');
  e1.setAttribute('points','72,42 62,20 84,36'); e1.setAttribute('fill', batFill);
  svg.appendChild(e1);
  var e2 = pdoc.createElementNS(ns,'polygon');
  e2.setAttribute('points','128,42 138,20 116,36'); e2.setAttribute('fill', batFill);
  svg.appendChild(e2);

  wrap.appendChild(svg);
  pdoc.body.appendChild(wrap);

  // ── Bounce physics ──
  var size = 82;
  var x = pw.innerWidth  - size - 60;   // start near top-right like before
  var y = 65;
  var spd = 1.1;
  var dx =  -(0.6 + Math.random() * 0.5) * spd;
  var dy =   (0.3 + Math.random() * 0.4) * spd;
  var glowFrames = 0;

  function tick() {{
    var sw = pw.innerWidth  || 1200;
    var sh = pw.innerHeight || 800;

    x += dx; y += dy;

    var bounced = false;
    if (x <= 0)          {{ dx = Math.abs(dx);  x = 0;          bounced = true; }}
    if (x >= sw - size)  {{ dx = -Math.abs(dx); x = sw - size;  bounced = true; }}
    if (y <= 0)          {{ dy = Math.abs(dy);  y = 0;          bounced = true; }}
    if (y >= sh - size)  {{ dy = -Math.abs(dy); y = sh - size;  bounced = true; }}

    if (bounced && !noirMode) {{
      glowFrames = 18;
    }}

    if (glowFrames > 0) {{
      var g = Math.round((glowFrames / 18) * 255);
      svg.style.filter = 'drop-shadow(0 0 ' + (6 + glowFrames) + 'px rgba(241,196,15,' + (glowFrames/18).toFixed(2) + '))';
      glowFrames--;
    }} else if (!noirMode) {{
      svg.style.filter = 'drop-shadow(0 0 6px rgba(241,196,15,0.5))';
    }}

    wrap.style.left = x + 'px';
    wrap.style.top  = y + 'px';

    // Keep running — will survive Streamlit reruns since it's in parent window
    if (pdoc.getElementById('bat-signal')) {{
      requestAnimationFrame(tick);
    }}
  }}

  requestAnimationFrame(tick);
}})();
</script>
""", height=0)

# ─────────────────────────────────────────────
# 6. JS CELEBRATION ANIMATIONS  (iframe → window.parent escape)
# Only build + inject when there's actually something to animate
# ─────────────────────────────────────────────
if celebration_xp or rank_up_title or pomodoro_done or reward_claimed:
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

# Structured feedback from Emily's draft review (hbmc_draft_feedback.py)
# comment_type → action_type; severity → priority
_EMILY_COMMENT_TYPE_MAP = {
    "Narrative Flow": "clarification",
    "Content & Frameworks": "substantive",
    "Methodology": "substantive",
    "Argumentation": "substantive",
    "Formatting & Citations": "quick_fix",
    "Grammar/Syntax": "quick_fix",
}
EMILY_DRAFT_FEEDBACK = [
    {
        "id": "FB-001",
        "section": "Introduction to Home-Based Medical Care (HBMC)",
        "comment_type": "Narrative Flow",
        "severity": "Low",
        "feedback": "The introduction provides a solid foundational understanding of HBMC. To strengthen the overarching narrative of the exam, consider briefly foreshadowing the vulnerability of HBMC to natural disasters in this first section. This will better bridge the context with the subsequent chapters."
    },
    {
        "id": "FB-002",
        "section": "Impacts of Disasters",
        "comment_type": "Content & Frameworks",
        "severity": "Medium",
        "feedback": "Excellent application of the Socio-ecological and Resilience frameworks. The transition from general older adult vulnerabilities to specific HBMC challenges (e.g., electricity-dependent devices) is highly effective. Just double-check that all extreme statistical claims (e.g., '1120% increase in heat wave exposure') have a clear, corresponding citation immediately following the claim."
    },
    {
        "id": "FB-003",
        "section": "Delphi Method",
        "comment_type": "Methodology",
        "severity": "Low",
        "feedback": "Strong rationale for using the Delphi method in disaster research where RCTs are unethical or unfeasible. The breakdown of different Delphi variations (Modified vs. Policy vs. Real-Time) and mapping them to specific HBMC scenarios shows a deep, practical understanding of the methodology."
    },
    {
        "id": "FB-004",
        "section": "Subnational CPA",
        "comment_type": "Argumentation",
        "severity": "Medium",
        "feedback": "The justification for scaling down to the state level is very well articulated. The explanation of causal complexity and equifinality correctly identifies why standard behavioralist approaches fail for this specific policy issue. Consider adding a brief concluding paragraph at the very end of the document tying the SCPA framework directly back to the Delphi method—how will the Delphi outputs be analyzed through the SCPA lens?"
    },
    {
        "id": "FB-005",
        "section": "Global/Entire Document",
        "comment_type": "Formatting & Citations",
        "severity": "High",
        "feedback": "There are several instances of artifact superscript numbers left in the text (e.g., 'home.1', 'issues.2', 'cost-efficiency.3') alongside the bracketed '' tags. Recommend running a quick clean-up pass to standardize all in-text citations to a single format before final submission."
    },
    {
        "id": "FB-006",
        "section": "Impacts of Disasters (Conclusion)",
        "comment_type": "Grammar/Syntax",
        "severity": "Low",
        "feedback": "In the paragraph starting 'Moreover, the lack of a universal definition...', the sentence 'Development of gerontological resilience metrics in gerontology is hindered overlooks how the resiliency...' seems to have a syntax error or missing words. Recommend revising for clarity."
    },
]
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
# 11. SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.header("🦇 Bat-Computer")
    _mode_icon = "🌑" if not st.session_state.get("noir_mode", False) else "🌈"
    _mode_label = f"{_mode_icon} {'Noir Mode' if not st.session_state.get('noir_mode', False) else 'Color Mode'}"
    if st.button(_mode_label, use_container_width=True, key="toggle_noir_mode"):
        st.session_state.noir_mode = not st.session_state.get("noir_mode", False)
        st.rerun()
    st.metric("Total XP", st.session_state.xp)
    render_rank_badge(st.session_state.xp)
    render_progress_badges(st.session_state.completed_tasks, master_tasks)

    with st.expander("➕ Add XP Manually"):
        _manual_xp = st.number_input("XP to add", min_value=1, max_value=500, value=10, step=5, key="manual_xp_input")
        _manual_reason = st.text_input("Reason (optional)", placeholder="e.g. Revised intro paragraph", key="manual_xp_reason")
        if st.button("Add XP", key="manual_xp_btn", type="primary"):
            st.session_state.xp += _manual_xp
            save_all_progress()
            _reason_msg = f" — {_manual_reason}" if _manual_reason.strip() else ""
            st.toast(f"🦇 +{_manual_xp} XP added{_reason_msg}!", icon="🦇")
            st.rerun()

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

    _task_lookup = {i['id']: i for cat in master_tasks.values() for i in cat}
    all_tasks_flat = [
        f"{i['id']}: {i['task']}"
        for cat in master_tasks.values()
        for i in cat
        if i['id'] not in st.session_state.completed_tasks
    ]
    selected_mission = st.selectbox("🎯 Current Focus Task:", ["General Deep Work"] + all_tasks_flat, key="sidebar_focus_task")
    # Sync selectbox → active_mission only when no EKT item is active and timer isn't running
    _ekt_focused = bool(st.session_state.get("ekt_active_item", {}).get("id"))
    if not st.session_state.get('timer_running') and not _ekt_focused:
        st.session_state.active_mission = selected_mission
        # Auto-activate Robin mission based on task type (triage)
        if selected_mission != "General Deep Work":
            _sel_id = selected_mission.split(":")[0].strip()
            _sel_task = _task_lookup.get(_sel_id)
            if _sel_task:
                _ttype = _sel_task.get("type", "")
                _mission_tuple = TASK_TYPE_MISSION_MAP.get(_ttype)
                if _mission_tuple:
                    st.session_state.robin_active_mission = _mission_tuple

    # Show active Committee Feedback item when one is selected
    _active_ekt = st.session_state.get("ekt_active_item", {})
    if _active_ekt.get("id"):
        _eid  = _active_ekt.get("id", "")
        _esec = _active_ekt.get("section", "General")
        _erev = _active_ekt.get("reviewer", "")
        _atype_label = {"quick_fix": "⚡ Quick Fix", "clarification": "💬 Clarification",
                        "substantive": "📝 Substantive", "major": "🏗️ Major"}.get(_active_ekt.get("action_type", ""), "📋")
        st.markdown(
            f'<div style="background:#1a1a2e;border-left:3px solid #5C4A1E;border-radius:6px;'
            f'padding:8px 12px;color:#f0e6c8;font-size:0.8rem;margin-top:4px;">'
            f'<b style="color:#f1c40f;">📋 Active Feedback:</b><br>'
            f'<b>{_eid}</b> — {_esec}<br>'
            f'<span style="color:#aaa;font-size:0.75rem;">{_erev} · {_atype_label}</span>'
            f'</div>',
            unsafe_allow_html=True
        )

    @st.fragment(run_every="1s")
    def sidebar_pomodoro():
        _mission = st.session_state.get("active_mission", "General Deep Work")
        if st.session_state.get('timer_running') and st.session_state.get('target_time'):
            if not st.session_state.get('timer_paused'):
                remaining = st.session_state.target_time - datetime.now()
                total_seconds = int(remaining.total_seconds())
                if total_seconds > 0:
                    mins, secs = divmod(total_seconds, 60)
                    label = f"⏳ Slaying: {_mission.split(':')[0]}"
                    if mins < 5:
                        label = f"🔥 FINAL PUSH: {_mission.split(':')[0]}"
                    st.metric(label, f"{mins:02d}:{secs:02d}")
                else:
                    st.session_state.timer_running = False
                    task_id = _mission.split(":")[0]
                    st.session_state.task_timers[task_id] = \
                        st.session_state.task_timers.get(task_id, 0) + 25
                    st.session_state.xp += 25
                    st.session_state.celebration_xp = 25
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
                        task_id = _mission.split(":")[0]
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
                st.session_state.active_mission = selected_mission
                st.session_state.target_time = datetime.now() + timedelta(minutes=25)
                st.session_state.timer_running = True
                st.session_state.timer_paused = False
                save_all_progress()
                st.rerun()
        else:
            p_col1, p_col2, p_col3 = st.columns(3)
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
                        task_id = st.session_state.get("active_mission", "General Deep Work").split(":")[0]
                        st.session_state.task_timers[task_id] = \
                            st.session_state.task_timers.get(task_id, 0) + elapsed_mins
                        st.session_state.xp += elapsed_mins
                        st.session_state.celebration_xp = elapsed_mins
                        save_all_progress()
                        st.success(f"Saved {elapsed_mins}m! +{elapsed_mins} XP")
                st.session_state.timer_running = False
                st.session_state.timer_paused = False
                st.session_state.target_time = None
                st.session_state.active_mission = ""
                st.rerun()

            if p_col3.button("🔄 Reset Timer", use_container_width=True):
                st.session_state.timer_running = False
                st.session_state.timer_paused = False
                st.session_state.target_time = None
                st.session_state.active_mission = ""
                save_all_progress()
                st.rerun()

    st.divider()
    st.subheader("📍 Last Worked")
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
                _syn_cache = st.session_state.get("synonym_cache", {})
                _cached_syn = _syn_cache.get(word_lower)
                if _cached_syn:
                    st.markdown(
                        f'<div style="background:#1a1a2e;border-left:2px solid #f1c40f;'
                        f'padding:8px 12px;border-radius:6px;color:#f0e6c8;font-size:0.83rem;">'
                        f'{_cached_syn}</div>',
                        unsafe_allow_html=True
                    )
                    st.caption("📦 From cache")
                elif st.button("🦇 AI Synonyms", use_container_width=True, key="ai_syn_btn"):
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
                            _syn_text = message.content[0].text
                            st.session_state.setdefault("synonym_cache", {})[word_lower] = _syn_text
                            save_all_progress()
                            st.markdown(
                                f'<div style="background:#1a1a2e;border-left:2px solid #f1c40f;'
                                f'padding:8px 12px;border-radius:6px;color:#f0e6c8;font-size:0.83rem;">'
                                f'{_syn_text}</div>',
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
        _emma_ctx = [i for i in st.session_state.get("comps_feedback_cache", []) if i.get("section") == _clock_section]
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

    # ── Log Focus Time to Section ──
    if _clock_section:
        _log_mins = st.number_input(
            "Minutes to log:", min_value=1, max_value=300,
            value=max(1, _total_mins), step=1, key="clock_log_mins"
        )
        if st.button("💾 Log Focus Time (+XP)", use_container_width=True, key="clock_log_btn"):
            st.session_state.section_timers[_clock_section] = \
                st.session_state.section_timers.get(_clock_section, 0) + _log_mins
            old_rank = get_rank(st.session_state.xp)
            st.session_state.xp += _log_mins
            new_rank = get_rank(st.session_state.xp)
            if new_rank[0] != old_rank[0]:
                st.session_state.rank_up_title = new_rank[1]
            st.session_state.celebration_xp = _log_mins
            st.session_state.last_worked_section = _clock_section
            st.session_state.last_worked_date = datetime.now().strftime("%b %d, %Y at %I:%M %p")
            save_all_progress()
            st.success(f"Logged {_log_mins}m to **{_clock_section}** +{_log_mins} XP ⚡")
            st.rerun()
    else:
        st.caption("Select a section in Focus Mode to log time.")

    st.divider()

    # ── Focus Beats ──
    st.subheader("🎵 Focus Beats")

    # Updated to standard YouTube links for better compatibility with st.video()
    BEATS = {
        "🌙 Gotham Night (Lo-Fi)":   "https://www.youtube.com/watch?v=jfKfPfyJRdk",
        "🌧️ Rain on Gotham":         "https://www.youtube.com/watch?v=mPZkdNFkNps",
        "🔥 Dark Ambient":           "https://www.youtube.com/watch?v=S_MOd40zlYU",
        "📚 Study Jazz":             "https://www.youtube.com/watch?v=HuFYqnbVbzY",
        "🌊 White Noise":            "https://www.youtube.com/watch?v=nMfPqeZjc2c",
        "🦇 Cinematic Batman Vibes": "https://www.youtube.com/watch?v=ordvJNeMjPI",
    }

    # 1. Create a dropdown menu for the user to select a track
    selected_track = st.selectbox("Choose a track to play:", options=list(BEATS.keys()))

    # 2. Get the URL for the selected track
    video_url = BEATS[selected_track]

    # 3. Embed and play the video directly in the app
    st.video(video_url)
    st.divider()

    st.subheader("🐦 Robin — Your Dissertation Sidekick")

    # ── Mission Picker ──
    with st.expander("🎯 Choose Your Mission", expanded=False):
        _phase_options = list(ROBIN_MISSIONS.keys())
        _selected_phase = st.selectbox("Phase:", _phase_options, key="robin_mission_phase")
        _phase_missions = ROBIN_MISSIONS[_selected_phase]
        _mission_labels = [f"{name} — {desc}" for name, desc in _phase_missions]
        _mission_idx = st.radio("Mission:", range(len(_phase_missions)),
                                format_func=lambda i: _mission_labels[i],
                                key="robin_mission_idx")
        _chosen_mission_name, _chosen_mission_desc = _phase_missions[_mission_idx]
        if st.button("🦇 Activate Mission", use_container_width=True, key="robin_mission_activate"):
            st.session_state.robin_active_mission = (_chosen_mission_name, _chosen_mission_desc, _selected_phase)
            st.session_state.coach_messages = []
            st.session_state.walkthrough_introduced = -1
            st.rerun()

    _robin_mission = st.session_state.get("robin_active_mission")
    if _robin_mission:
        _rmn, _rmd, _rmp = _robin_mission
        st.markdown(
            f'<div style="background:#1a1a2e;border:1px solid #f1c40f;border-radius:8px;'
            f'padding:8px 12px;margin-bottom:6px;">'
            f'<span style="color:#f1c40f;font-size:0.7rem;">{_rmp}</span><br>'
            f'<b style="color:#f0e6c8;font-size:0.9rem;">⚡ {_rmn}</b><br>'
            f'<span style="color:#aaa;font-size:0.75rem;">{_rmd}</span>'
            f'</div>',
            unsafe_allow_html=True
        )
        if st.button("✖ Clear Mission", key="robin_mission_clear", use_container_width=False):
            st.session_state.robin_active_mission = None
            st.rerun()

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
    if "coach_messages_by_idx" not in st.session_state:
        st.session_state.coach_messages_by_idx = {}

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
            first_sec = _wt_sections[0] if _wt_sections else ""
            st.session_state.focus_section_select = first_sec
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
            st.session_state.coach_messages_by_idx[wt_idx] = list(st.session_state.coach_messages)
            st.session_state.walkthrough_idx -= 1
            new_idx = st.session_state.walkthrough_idx
            st.session_state.coach_messages = list(st.session_state.coach_messages_by_idx.get(new_idx, []))
            st.session_state.walkthrough_introduced = new_idx if st.session_state.coach_messages else -1
            st.session_state.ekt_active_item = {}
            st.session_state.focus_section_select = _wt_sections[new_idx]
            st.rerun()
        if nav2.button("Next ▶", key="wt_next", use_container_width=True, disabled=(wt_idx >= len(_wt_sections)-1)):
            st.session_state.coach_messages_by_idx[wt_idx] = list(st.session_state.coach_messages)
            st.session_state.walkthrough_idx += 1
            new_idx = st.session_state.walkthrough_idx
            st.session_state.coach_messages = list(st.session_state.coach_messages_by_idx.get(new_idx, []))
            st.session_state.walkthrough_introduced = new_idx if st.session_state.coach_messages else -1
            st.session_state.ekt_active_item = {}
            st.session_state.focus_section_select = _wt_sections[new_idx]
            st.rerun()
        if nav3.button("✖ End", key="wt_end", use_container_width=True):
            st.session_state.coach_messages_by_idx[wt_idx] = list(st.session_state.coach_messages)
            st.session_state.walkthrough_active = False
            st.session_state.coach_messages = []
            st.rerun()

        # Auto-generate intro when entering a new section or EKT item
        if st.session_state.walkthrough_introduced != wt_idx:
            _ekt_item = st.session_state.get("ekt_active_item", {})
            _brief_key = f"ekt:{_ekt_item.get('id')}" if _ekt_item and _ekt_item.get("feedback") else f"section:{current_wt_sec}"
            _cached_brief = st.session_state.get("briefing_cache", {}).get(_brief_key)

            if _cached_brief:
                st.session_state.coach_messages = [{"role": "assistant", "content": _cached_brief}]
                st.session_state.coach_messages_by_idx[wt_idx] = st.session_state.coach_messages
                st.session_state.walkthrough_introduced = wt_idx
                st.rerun()
            else:
                with st.spinner("🐦 Robin is preparing your mission briefing..."):
                    try:
                        import anthropic
                        client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])

                        _ekt_item = st.session_state.get("ekt_active_item", {})

                        if _ekt_item and _ekt_item.get("feedback"):
                            # EKT item mode — brief on the specific task in front of the student
                            _intro_prompt = (
                                f"You are Robin — loyal sidekick to the Caped Candidate, who is a PhD student fighting to finish their dissertation. "
                                f"You are smart, eager, and fully briefed on the mission. You speak with energy and loyalty — "
                                f"you believe in the Caped Candidate completely and your job is to keep them moving forward. "
                                f"The Caped Candidate is currently facing this specific committee feedback item:\n\n"
                                f"ID: {_ekt_item.get('id', '?')}\n"
                                f"Section: {_ekt_item.get('section', '?')}\n"
                                f"Paper: {_ekt_item.get('paper', '?')}\n"
                                f"Triage: {_ekt_item.get('action_type', '?')} | Priority: {_ekt_item.get('priority', '?')} | "
                                f"Est. time: ~{_ekt_item.get('estimated_minutes', '?')} min\n"
                                f"Reviewer: {_ekt_item.get('reviewer', '?')}\n\n"
                                f"Feedback comment:\n\"{_ekt_item.get('feedback', '')}\"\n\n"
                                f"Brief the Caped Candidate in 3-5 sentences: explain exactly what this feedback is asking for, "
                                f"give one concrete first step to address it, and flag any watch-outs. "
                                f"Sound like Robin reporting to the Caped Candidate — sharp, loyal, ready for action. Keep it brief — this is a sidebar."
                            )
                        else:
                            # Section walkthrough mode
                            _fb_items = [
                                {"reviewer": "Emily", "feedback": c["comment"],
                                 "priority": "high", "action_type": "substantive"}
                                for tid, c in lab_context.items()
                                if current_wt_sec in task_to_sections.get(tid, [])
                            ]
                            _fb_items += [i for i in st.session_state.get("comps_feedback_cache", []) if i.get("section") == current_wt_sec]
                            _fb_ctx = "\n".join(
                                f"- [{i.get('reviewer','?')}] ({i.get('priority','?')} priority, ~{i.get('estimated_minutes','?')}min) {i.get('feedback','')}"
                                for i in _fb_items
                            ) or "No specific feedback items found."
                            _draft = st.session_state.saved_responses.get(f"focus_draft_{current_wt_sec}", "")
                            _draft_preview = ("Their current draft:\n" + _draft[:300]) if _draft else "No draft written yet."
                            _intro_prompt = (
                                f"You are Robin — loyal sidekick to the Caped Candidate, who is a PhD student fighting to finish their dissertation. "
                                f"You are smart, eager, fully briefed on every section, and completely devoted to helping the Caped Candidate succeed. "
                                f"The Caped Candidate has just arrived at a new section of their comps revisions. Brief them like a mission report.\n\n"
                                f"Section: **{current_wt_sec}** ({wt_idx+1} of {len(_wt_sections)})\n\n"
                                f"Committee feedback:\n{_fb_ctx}\n\n"
                                f"{_draft_preview}\n\n"
                                f"In 3-5 sentences: introduce this section, call out the 1-2 most critical feedback items to hit first, "
                                f"and give one concrete first move. Sound like Robin reporting to the Caped Candidate — sharp, loyal, ready. "
                                f"Keep it brief — this is a sidebar."
                            )
                        intro_response = client.messages.create(
                            model="claude-sonnet-4-20250514",
                            max_tokens=400,
                            messages=[{"role": "user", "content": _intro_prompt}]
                        )
                        intro_text = intro_response.content[0].text
                        st.session_state.setdefault("briefing_cache", {})[_brief_key] = intro_text
                        save_all_progress()
                        st.session_state.coach_messages = [{"role": "assistant", "content": intro_text}]
                        st.session_state.coach_messages_by_idx[wt_idx] = st.session_state.coach_messages
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
                f'font-size:0.82rem;margin:4px 0;">🐦 {msg["content"]}</div>',
                unsafe_allow_html=True
            )

    coach_input = st.text_area(
        "Message Robin:",
        placeholder="Ask a follow-up, paste a paragraph to review, or say 'next' to move on...",
        key="coach_input",
        height=80
    )

    coach_col1, coach_col2 = st.columns(2)

    if coach_col1.button("💬 Send", use_container_width=True, key="coach_send"):
        if coach_input:
            st.session_state.coach_messages.append({"role": "user", "content": coach_input})
            with st.spinner("🐦 Robin is on it..."):
                try:
                    import anthropic
                    client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])

                    _focus_sec = current_wt_sec if wt_active else st.session_state.get("focus_section_select", "")
                    _fb_items = [
                        {"reviewer": "Emily", "feedback": c["comment"]}
                        for tid, c in lab_context.items()
                        if _focus_sec in task_to_sections.get(tid, [])
                    ]
                    _fb_items += [i for i in st.session_state.get("comps_feedback_cache", []) if i.get("section") == _focus_sec]
                    _fb_ctx = "\n".join(f"- [{i.get('reviewer','?')}] {i.get('feedback','')}" for i in _fb_items)
                    _draft = st.session_state.saved_responses.get(f"focus_draft_{_focus_sec}", "")

                    _ekt_item_chat = st.session_state.get("ekt_active_item", {})
                    _item_ctx = ""
                    if _ekt_item_chat and _ekt_item_chat.get("feedback"):
                        _item_ctx = (
                            f"\nActive hit list item: {_ekt_item_chat.get('id','?')} — {_ekt_item_chat.get('section','?')} "
                            f"({_ekt_item_chat.get('paper','?')}, {_ekt_item_chat.get('action_type','?')})\n"
                            f"Feedback: \"{_ekt_item_chat.get('feedback','')}\"\n"
                        )

                    _active_robin_mission = st.session_state.get("robin_active_mission")
                    _mission_line = ""
                    if _active_robin_mission:
                        _amn, _amd, _amp = _active_robin_mission
                        _mission_line = f"\nACTIVE MISSION: {_amn} ({_amp})\nMission objective: {_amd}\n"

                    _draft_excerpt = (_draft[:300] + "...") if len(_draft) > 300 else _draft
                    _today_brief_text = st.session_state.get("daily_briefing", {})
                    _today_brief_text = _today_brief_text.get("text", "") if _today_brief_text.get("date") == datetime.now().strftime("%Y-%m-%d") else ""

                    system_prompt = f"""You are Robin — loyal sidekick to the Caped Candidate, who is a PhD student fighting to finish their dissertation. You are smart, sharp, and completely devoted to helping the Caped Candidate win. You speak with energy and loyalty. You know every section, every piece of committee feedback, and every deadline. Your job is to keep the Caped Candidate moving forward — no excuses, no stalling, just action.
{_mission_line}
{("Today's mission brief:\n" + _today_brief_text + "\n") if _today_brief_text else ""}{"MISSION BRIEFING — Section " + str(wt_idx+1) + " of " + str(len(_wt_sections)) if wt_active else ""}
Current section: **{_focus_sec}**
{_item_ctx}
Committee feedback:
{_fb_ctx if _fb_ctx else "None loaded."}

{"Current draft (excerpt):\n" + _draft_excerpt if _draft_excerpt else "No draft yet."}

Be direct, specific, doctoral-level. Keep responses concise — this is a sidebar. Sound like Robin: loyal, energetic, mission-focused. When a named mission is active, frame your guidance around its objective and refer to it by name."""

                    response = client.messages.create(
                        model="claude-sonnet-4-20250514",
                        max_tokens=500,
                        system=system_prompt,
                        messages=[{"role": m["role"], "content": m["content"]} for m in st.session_state.coach_messages[-10:]]
                    )
                    robin_reply = response.content[0].text
                    st.session_state.coach_messages.append({"role": "assistant", "content": robin_reply})
                    st.session_state.coach_messages_by_idx[wt_idx] = list(st.session_state.coach_messages)
                    _log_coach_exchange(coach_input, robin_reply, current_wt_sec if wt_active else st.session_state.get("focus_section_select", ""))
                    st.rerun()
                except Exception as e:
                    st.error(f"Coach failed: {e}")
        else:
            st.warning("Type something first!")

    if coach_col2.button("🗑️ Clear", use_container_width=True, key="coach_clear"):
        st.session_state.coach_messages = []
        st.session_state.walkthrough_introduced = -1
        st.rerun()

    # ── Coach conversation log ──
    _coach_log = st.session_state.get("coach_log", [])
    if _coach_log:
        with st.expander(f"📜 Coach History ({len(_coach_log)} exchanges)", expanded=False):
            # Export buttons
            _exp_col1, _exp_col2 = st.columns(2)

            def _build_coach_docx(log):
                from docx import Document
                from docx.shared import Pt, RGBColor
                from io import BytesIO
                doc = Document()
                doc.add_heading("Robin Coach History", 0)
                for entry in log:
                    doc.add_heading(f"{entry['date']} · {entry['section']}", level=2)
                    q_para = doc.add_paragraph()
                    q_run = q_para.add_run(f"You: {entry['question']}")
                    q_run.bold = True
                    a_para = doc.add_paragraph()
                    a_run = a_para.add_run(f"Robin: {entry['answer']}")
                    a_run.font.color.rgb = RGBColor(0x1a, 0x1a, 0x2e)
                    doc.add_paragraph()
                buf = BytesIO()
                doc.save(buf)
                buf.seek(0)
                return buf.read()

            def _build_coach_pdf(log):
                from fpdf import FPDF
                from io import BytesIO
                import unicodedata

                def _safe(text):
                    """Strip/replace characters that Latin-1 fonts can't encode."""
                    if not text:
                        return ""
                    # Normalize to decomposed form, then re-compose what we can
                    text = unicodedata.normalize("NFKD", text)
                    return text.encode("latin-1", errors="replace").decode("latin-1")

                pdf = FPDF()
                pdf.set_auto_page_break(auto=True, margin=15)
                pdf.add_page()
                pdf.set_font("Helvetica", "B", 16)
                pdf.cell(0, 10, "Robin Coach History", ln=True)
                pdf.ln(4)
                for entry in log:
                    pdf.set_font("Helvetica", "B", 11)
                    header = _safe(f"{entry['date']}  |  {entry['section']}")
                    pdf.cell(0, 8, header, ln=True)
                    pdf.set_font("Helvetica", "B", 10)
                    pdf.cell(0, 6, "You:", ln=True)
                    pdf.set_font("Helvetica", "", 10)
                    pdf.multi_cell(0, 5, _safe(entry["question"]))
                    pdf.set_font("Helvetica", "B", 10)
                    pdf.cell(0, 6, "Robin:", ln=True)
                    pdf.set_font("Helvetica", "", 10)
                    pdf.multi_cell(0, 5, _safe(entry["answer"]))
                    pdf.ln(4)
                    pdf.set_draw_color(200, 200, 200)
                    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
                    pdf.ln(4)
                return bytes(pdf.output())

            with _exp_col1:
                _docx_bytes = _build_coach_docx(_coach_log)
                st.download_button(
                    "⬇️ Export Word",
                    data=_docx_bytes,
                    file_name="robin_coach_history.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True,
                    key="coach_export_docx"
                )
            with _exp_col2:
                _pdf_bytes = _build_coach_pdf(_coach_log)
                st.download_button(
                    "⬇️ Export PDF",
                    data=_pdf_bytes,
                    file_name="robin_coach_history.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                    key="coach_export_pdf"
                )

            st.divider()
            for _log_entry in reversed(_coach_log):
                st.markdown(f"**{_log_entry['date']} · {_log_entry['section']}**")
                st.markdown(
                    f'<div style="background:#1a1410;color:#f5f0e8;padding:8px 12px;'
                    f'border-radius:10px 2px 10px 10px;margin:4px 0 4px 32px;font-size:13px;">👤 {_log_entry["question"]}</div>',
                    unsafe_allow_html=True
                )
                st.markdown(
                    f'<div style="background:#fff;border:1px solid #d4c9b8;color:#1a1410;padding:8px 12px;'
                    f'border-radius:2px 10px 10px 10px;margin:4px 32px 4px 0;font-size:13px;">🐦 {_log_entry["answer"]}</div>',
                    unsafe_allow_html=True
                )
                st.divider()

# ─────────────────────────────────────────────
# 11. TABS
# ─────────────────────────────────────────────
# ─────────────────────────────────────────────
# WELCOME BANNER — Progress & Encouragement
# ─────────────────────────────────────────────
_rank_icon, _rank_title, _rank_color = get_rank(st.session_state.xp)
_last_section = st.session_state.get("last_worked_section", "")
_last_date = st.session_state.get("last_worked_date", "")
_section_timers = st.session_state.get("section_timers", {})
_total_section_mins = sum(_section_timers.values())
_task_timers = st.session_state.get("task_timers", {})
_total_task_mins = sum(_task_timers.values())
_all_mins = _total_section_mins + _total_task_mins
_rank_icon_display = get_rank(st.session_state.xp)[0]

# EKT progress for banner
_banner_cache = st.session_state.get("comps_feedback_cache", [])
_banner_completed = st.session_state.completed_tasks
_banner_ekt_total = len(_banner_cache) + len(lab_context) + len(EMILY_DRAFT_FEEDBACK)
_banner_ekt_done = (
    sum(1 for i in _banner_cache if i.get("status") != "pending")
    + sum(1 for tid in lab_context if tid in _banner_completed)
    + sum(1 for fb in EMILY_DRAFT_FEEDBACK if fb["id"] in _banner_completed)
)
_banner_ekt_pct = int(_banner_ekt_done / _banner_ekt_total * 100) if _banner_ekt_total else 0

# Build encouraging message
_msg_lines = [f"## 🦇 Welcome back, {_rank_icon_display} {_rank_title}"]
_msg_lines.append(f"**{st.session_state.xp} XP earned** • **{_all_mins // 60}h {_all_mins % 60}m** focused • **{_banner_ekt_done}/{_banner_ekt_total} feedback items resolved** ({_banner_ekt_pct}%)")

if _last_section and _last_date:
    _msg_lines.append(f"⏪ **Last worked:** {_last_section} · {_last_date}")

# Progress towards next rank
_next_xp, _next_title = get_next_rank(st.session_state.xp)
if _next_xp:
    _needed = _next_xp - st.session_state.xp
    _msg_lines.append(f"🔺 **{_needed} XP until {_next_title}**")
else:
    _msg_lines.append(f"👑 **LEGEND STATUS ACHIEVED** — Gotham's finest.")

if _banner_ekt_pct >= 75:
    _msg_lines.append("*The finish line is in sight. One more push.* 🌙")
elif _banner_ekt_pct >= 50:
    _msg_lines.append("*Past halfway. Momentum is yours.* 🌙")
else:
    _msg_lines.append("*Gotham needs you. Dive in.* 🌙")

st.markdown("\n\n".join(_msg_lines))

# ── DAILY MISSION BRIEF ──────────────────────
_today_key = datetime.now().strftime("%Y-%m-%d")
_db_brief = st.session_state.get("daily_briefing", {})
_brief_text = _db_brief.get("text", "") if _db_brief.get("date") == _today_key else ""

if _brief_text:
    st.markdown(
        f'<div style="background:#0d2b0d;border-left:4px solid #2ecc71;border-radius:8px;'
        f'padding:10px 14px;color:#d5f5e3;font-size:0.85rem;margin:8px 0;">'
        f'<b style="color:#2ecc71;">🐦 Today\'s Mission Brief</b><br>{_brief_text}</div>',
        unsafe_allow_html=True
    )
else:
    _brief_col1, _brief_col2 = st.columns([3, 1])
    with _brief_col2:
        if st.button("🐦 Get Mission Brief", use_container_width=True, key="gen_brief_btn"):
            with st.spinner("Robin is preparing today's brief..."):
                _new_brief = generate_daily_briefing()
            st.rerun()

st.divider()

t3, t4, t5, t6, t7, t8 = st.tabs([
    "🎁 Rewards & Analytics", "📜 Writing Guide", "🎓 Comps Review", "🧠 Mind Map", "🎯 Focus", "📋 Committee Feedback"
])

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

    @st.fragment
    def _rewards_list():
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

    col_l, col_r = st.columns(2)
    with col_l:
        _rewards_list()

    with col_r:
        st.subheader("📊 Focus Time Analytics")
        section_timers_data = st.session_state.get("section_timers", {})
        task_timers_data = st.session_state.task_timers

        if section_timers_data:
            st.markdown("**⏱️ Time by Section (Focus Clock)**")
            df_sec = pd.DataFrame(
                list(section_timers_data.items()), columns=['Section', 'Minutes']
            ).sort_values('Minutes', ascending=False)
            st.bar_chart(df_sec.set_index('Section'))
            sec_total = sum(section_timers_data.values())
            st.metric("Total Focus Clock Time", f"{sec_total // 60}h {sec_total % 60}m")

        if task_timers_data:
            st.markdown("**🍅 Time by Task (Pomodoro)**")
            df_task = pd.DataFrame(
                list(task_timers_data.items()), columns=['Task ID', 'Minutes']
            )
            st.bar_chart(df_task.set_index('Task ID'))
            task_total = sum(task_timers_data.values())
            st.metric("Total Pomodoro Time", f"{task_total // 60}h {task_total % 60}m")

        all_mins = sum(section_timers_data.values()) + sum(task_timers_data.values())
        if all_mins:
            st.metric("🦇 Total PhD Focus Time", f"{all_mins // 60}h {all_mins % 60}m")
        else:
            st.info("Start a Focus Clock or Pomodoro sprint to track time! 🦇")

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

                # Stable system prompt: persona + section identity + full content.
                # Lives in `system` param so prompt caching activates (requires ≥1,024 tokens;
                # section content easily clears that bar for any real draft).
                _system = [{"type": "text", "text": f"""You are an expert dissertation committee member specializing in public health, aging, health policy, geriatrics, and disaster preparedness.

Paper: {current_section['paper']}
Section: {current_section['title']}

Section content:
\"\"\"{current_section['content']}\"\"\"""", "cache_control": {"type": "ephemeral"}}]

                # User message: only what changes per request (feedback type + optional notes).
                _user = f"""{f'Student notes: {user_notes}' if user_notes else ''}

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
                    system=_system,
                    messages=[{"role": "user", "content": _user}]
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

    # Emma's feedback from session cache
    emma_feedback = [i for i in st.session_state.get("comps_feedback_cache", []) if i.get("reviewer") == "Emma Tsui"]

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

    # Load Emma's feedback from session cache
    focus_emma_items = list(st.session_state.get("comps_feedback_cache", []))

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

    # ── GOOGLE DOC LINK ──────────────────────────────────
    st.divider()
    st.subheader("📝 Google Doc Editor")
    _GDOC_URL = "https://docs.google.com/document/d/1OMk-Q-IJrsO-H1iqENxM68VHBFpmtXQcriSzjKz5dME/edit?usp=sharing"
    st.markdown(
        f'<a href="{_GDOC_URL}" target="_blank" style="display:inline-block;padding:12px 28px;'
        f'background:linear-gradient(135deg,#f1c40f,#e67e22);color:#1a1a2e;font-weight:bold;'
        f'font-size:1.05rem;border-radius:8px;text-decoration:none;'
        f'box-shadow:0 0 16px rgba(241,196,15,0.4);">🦇 Open Google Doc ↗</a>',
        unsafe_allow_html=True
    )
    st.caption("Opens in a new tab so your doc stays stable while you work in the app.")

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

# ── TAB 8: COMMITTEE FEEDBACK ────────────────────
with t8:
    st.header("📋 Committee Feedback")
    st.caption("Emily + Emma Tsui — work through items one by one, earn XP for each.")

    # Build Emily items — lab_context inline comments + structured draft feedback
    _emily_ekt_items = []
    for _etid, _ectx in lab_context.items():
        _esections = task_to_sections.get(_etid, [])
        _emily_ekt_items.append({
            "id": f"Emily-{_etid}",
            "task_id": _etid,
            "reviewer": "Emily",
            "paper": "HBMC",
            "section": _esections[0] if _esections else "General",
            "feedback": _ectx["comment"],
            "action_type": "substantive",
            "priority": "high",
            "estimated_minutes": 20,
            "status": "done" if _etid in st.session_state.completed_tasks else "pending",
        })
    _sev_to_priority = {"High": "high", "Medium": "medium", "Low": "low"}
    _sev_to_mins = {"High": 30, "Medium": 20, "Low": 15}
    for _edf in EMILY_DRAFT_FEEDBACK:
        _atype = _EMILY_COMMENT_TYPE_MAP.get(_edf["comment_type"], "clarification")
        _priority = _sev_to_priority.get(_edf["severity"], "medium")
        _emily_ekt_items.append({
            "id": _edf["id"],
            "task_id": _edf["id"],
            "reviewer": "Emily",
            "paper": "HBMC",
            "section": _edf["section"],
            "feedback": _edf["feedback"],
            "action_type": _atype,
            "priority": _priority,
            "estimated_minutes": _sev_to_mins.get(_edf["severity"], 20),
            "status": "done" if _edf["id"] in st.session_state.completed_tasks else "pending",
        })

    # Combine Emma (from cache) + Emily items
    _ekt_items = sorted(
        [i for i in st.session_state.get("comps_feedback_cache", []) if i.get("reviewer") == "Emma Tsui"],
        key=lambda x: (x.get("paper_num") or 0, x.get("comment_id") or 0)
    ) + _emily_ekt_items

    if _ekt_items:
        _ekt_pending = [f for f in _ekt_items if f.get("status") == "pending"]
        _ekt_done = [f for f in _ekt_items if f.get("status") != "pending"]
        _total = len(_ekt_items)
        _done_count = len(_ekt_done)

        # Glowing overall progress bar
        _overall_pct = _done_count / _total if _total else 0
        if _overall_pct < 0.25:
            _ov_color = "#e74c3c"
            _ov_glow = "rgba(231,76,60,0.5)"
        elif _overall_pct < 0.5:
            _ov_color = "#f39c12"
            _ov_glow = "rgba(243,156,18,0.5)"
        elif _overall_pct < 0.75:
            _ov_color = "#3498db"
            _ov_glow = "rgba(52,152,219,0.5)"
        elif _overall_pct < 1.0:
            _ov_color = "#2ecc71"
            _ov_glow = "rgba(46,204,113,0.5)"
        else:
            _ov_color = "#f1c40f"
            _ov_glow = "rgba(241,196,15,0.7)"
        _ov_width = max(2, int(_overall_pct * 100))
        st.markdown(
            f'<div style="background:#111;border-radius:10px;height:32px;overflow:hidden;'
            f'border:1px solid #333;margin:8px 0;position:relative;">'
            f'<div style="height:100%;width:{_ov_width}%;background:linear-gradient(90deg,{_ov_color},{_ov_color}dd);'
            f'border-radius:10px;transition:width 0.5s ease;'
            f'box-shadow:0 0 12px {_ov_glow}, 0 0 24px {_ov_glow}, inset 0 0 8px rgba(255,255,255,0.15);'
            f'animation:overallPulse 2s ease-in-out infinite;">'
            f'</div>'
            f'<div style="position:absolute;top:0;left:0;width:100%;height:100%;display:flex;'
            f'align-items:center;justify-content:center;font-size:0.85rem;font-weight:bold;'
            f'color:#fff;text-shadow:0 0 6px rgba(0,0,0,0.8);">'
            f'🦇 {_done_count}/{_total} feedback items — {_total - _done_count} remaining</div>'
            f'</div>'
            f'<style>@keyframes overallPulse {{'
            f'0%,100%{{box-shadow:0 0 10px {_ov_glow}, 0 0 20px {_ov_glow};}}'
            f'50%{{box-shadow:0 0 18px {_ov_glow}, 0 0 36px {_ov_glow}, 0 0 50px {_ov_glow};}}'
            f'}}</style>',
            unsafe_allow_html=True
        )

        # XP info
        _xp_per_type = {"quick_fix": 10, "clarification": 15, "substantive": 25, "major": 40, "none": 0}
        _total_xp_available = sum(_xp_per_type.get(f.get("action_type", ""), 10) for f in _ekt_pending)
        st.markdown(f"**XP available from remaining items: {_total_xp_available}**")

        st.divider()

        # ── RACE THE CLOCK MODE ──────────────────────────────
        _race_active = st.session_state.get("race_active", False)
        _race_taunts = [
            ("Joker", "You wanna know how I got these scars? Procrastination, Batman. Tick tock."),
            ("Bane", "You think deadlines are your ally? I was born in them, molded by them."),
            ("Scarecrow", "What do you fear most, Dark Knight? An unfinished dissertation, perhaps?"),
            ("Ra's al Ghul", "If you make yourself more than just a student... if you devote yourself to finishing... you become something else entirely."),
            ("Mr. Freeze", "Allow me to break the ice — your comps are overdue."),
            ("Riddler", "Riddle me this: how many feedback items can you crush before time runs out?"),
            ("Catwoman", "You don't owe these committee members anything. But you're gonna give it to them anyway, aren't you?"),
            ("Two-Face", "You either finish the comps, or you live long enough to see yourself ABD."),
            ("Poison Ivy", "Every revision you skip lets the weeds grow back stronger, Dark Knight."),
            ("Penguin", "Time is money, Batman — and you're running out of both."),
            ("Deathstroke", "I've been watching you stall. Let's see if you can actually execute."),
            ("Hugo Strange", "I know your secret, Batman. You've been avoiding the substantive edits."),
            ("Darkseid", "Your procrastination is a flea biting the heel of a god. There is no 'tomorrow.' There is no 'later.' There is only the Anti-Life Equation, and right now, your unfinished Chapter Four is the only thing standing in the way of total dominion. Submit, or perish."),
            ("Reverse-Flash", "It was me, Batman. I was the one who distracted you with that YouTube rabbit hole so you'd miss your daily word count by just one minute! But even I am bored of your excuses. Finish the draft. You can't run from the deadline forever, and I'm tired of waiting for a rival who can't even format a Table of Contents."),
            ("Amanda Waller", "I don't care about your writer's block, and I certainly don't care about your sleep schedule. You have a mission. You have a deadline. If that dissertation isn't on my desk by 0800 hours, I'm pulling your funding and labeling your entire academic career a national security threat. Get. It. Done."),
            ("Ra's al Ghul", "A true master does not 'try' to write. A true master shapes the world through sheer force of intellect. You have spent years in the League of Graduate Students; do not shame your tutors now by trembling before a mere defense. Burn the midnight oil until the work is complete, or let your legacy be reduced to ash."),
            ("Brainiac", "Your collection of knowledge is... incomplete. It irritates me. I have digitized entire civilizations in less time than it has taken you to write a Literature Review. The universe has no room for unfinished thoughts. Upload the file, or be deleted as an inefficient variable."),
            ("Sinestro", "I see the yellow glow of fear in your eyes every time you look at the 'Appendices' folder. Harness it! Do not let the committee intimidate you — make them afraid of the sheer brilliance of your findings. Success is not given; it is imposed upon the weak by the strong. Write with fire."),
        ]
        _villain_name, _villain_quote = random.choice(_race_taunts)

        @st.fragment(run_every="1s")
        def race_hud():
            _race_end = st.session_state.get("race_end_time", datetime.now())
            _race_remaining = _race_end - datetime.now()
            _race_secs = max(0, int(_race_remaining.total_seconds()))
            _race_mins, _race_s = divmod(_race_secs, 60)
            _race_completed = st.session_state.get("race_completed", 0)
            _race_target_count = st.session_state.get("race_target", 5)
            _race_streak = st.session_state.get("race_streak", 0)
            _race_best = st.session_state.get("race_best_streak", 0)
            _race_pct = _race_completed / _race_target_count if _race_target_count else 0

            # Determine urgency color + villain taunt
            if _race_secs <= 0:
                _clock_color = "#e74c3c"
                _clock_emoji = "💀"
                _live_taunt = "Joker: HA HA HA! Time's up, Bats!"
            elif _race_secs < 60:
                _clock_color = "#e74c3c"
                _clock_emoji = "🔥"
                _live_taunt = "Bane: Now you have my permission to panic."
            elif _race_secs < 120:
                _clock_color = "#e74c3c"
                _clock_emoji = "🔥"
                _live_taunt = "Scarecrow: I can smell the fear. Two minutes left..."
            elif _race_secs < 300:
                _clock_color = "#f39c12"
                _clock_emoji = "⚡"
                _live_taunt = "Riddler: Can you solve the remaining items in time? I doubt it."
            else:
                _clock_color = "#2ecc71"
                _clock_emoji = "🏎️"
                _live_taunt = "Alfred: Steady pace, sir. You've got this."

            # Streak display
            _streak_text = ""
            if _race_streak >= 3:
                _streak_text = f' · <span style="color:#f1c40f;">🔥 {_race_streak}x STREAK!</span>'

            st.markdown(
                f'<div style="background:linear-gradient(135deg,#1a0a0a,#2a0a0a);'
                f'border:2px solid {_clock_color};border-radius:12px;padding:16px;'
                f'color:#f0e6c8;margin-bottom:12px;">'
                f'<div style="display:flex;justify-content:space-between;align-items:center;">'
                f'<div>'
                f'<span style="font-size:1.8rem;font-weight:bold;color:{_clock_color};">'
                f'{_clock_emoji} {_race_mins:02d}:{_race_s:02d}</span>'
                f'<span style="margin-left:16px;font-size:1rem;">Items: <b>{_race_completed}/{_race_target_count}</b>'
                f'{_streak_text}</span>'
                f'</div>'
                f'<div style="font-size:0.85rem;color:#aaa;">Best streak: {_race_best}</div>'
                f'</div>'
                f'<div style="margin-top:10px;font-style:italic;font-size:0.9rem;color:{_clock_color};">'
                f'🦹 {_live_taunt}</div>'
                f'</div>',
                unsafe_allow_html=True
            )
            # Glowing progress bar
            if _race_pct < 0.25:
                _bar_color = "#e74c3c"
                _glow_color = "rgba(231,76,60,0.6)"
            elif _race_pct < 0.5:
                _bar_color = "#f39c12"
                _glow_color = "rgba(243,156,18,0.6)"
            elif _race_pct < 0.75:
                _bar_color = "#3498db"
                _glow_color = "rgba(52,152,219,0.6)"
            elif _race_pct < 1.0:
                _bar_color = "#2ecc71"
                _glow_color = "rgba(46,204,113,0.6)"
            else:
                _bar_color = "#f1c40f"
                _glow_color = "rgba(241,196,15,0.8)"
            _bar_width = max(2, int(_race_pct * 100))
            st.markdown(
                f'<div style="background:#111;border-radius:10px;height:28px;overflow:hidden;'
                f'border:1px solid #333;margin:8px 0 16px 0;position:relative;">'
                f'<div style="height:100%;width:{_bar_width}%;background:linear-gradient(90deg,{_bar_color},{_bar_color}dd);'
                f'border-radius:10px;transition:width 0.5s ease;'
                f'box-shadow:0 0 12px {_glow_color}, 0 0 24px {_glow_color}, inset 0 0 8px rgba(255,255,255,0.15);'
                f'animation:barPulse 1.5s ease-in-out infinite;">'
                f'</div>'
                f'<div style="position:absolute;top:0;left:0;width:100%;height:100%;display:flex;'
                f'align-items:center;justify-content:center;font-size:0.8rem;font-weight:bold;'
                f'color:#fff;text-shadow:0 0 6px rgba(0,0,0,0.8);">'
                f'{_race_completed}/{_race_target_count} — {int(_race_pct * 100)}%</div>'
                f'</div>'
                f'<style>@keyframes barPulse {{'
                f'0%,100%{{box-shadow:0 0 12px {_glow_color}, 0 0 24px {_glow_color};}}'
                f'50%{{box-shadow:0 0 20px {_glow_color}, 0 0 40px {_glow_color}, 0 0 60px {_glow_color};}}'
                f'}}</style>',
                unsafe_allow_html=True
            )

            # Check win/lose conditions
            if _race_completed >= _race_target_count:
                _bonus = st.session_state.get("race_bonus", 0)
                _time_bonus = (_race_secs // 60) * 5  # 5 XP per minute remaining
                _streak_bonus = _race_best * 5  # 5 XP per best streak
                _total_bonus = _bonus + _time_bonus + _streak_bonus
                _win_quotes = [
                    ("Alfred", "Well done, sir. I took the liberty of preparing a celebration."),
                    ("Commissioner Gordon", "You did it. Gotham — and your committee — thank you."),
                    ("Lucius Fox", "I don't think even I could have engineered that kind of efficiency."),
                    ("Batman", "I'm whatever Gotham needs me to be. Tonight, that was fast."),
                    ("Catwoman", "Not bad, Dark Knight. Not bad at all."),
                ]
                _win_name, _win_quote = random.choice(_win_quotes)
                st.markdown(
                    f'<div style="background:linear-gradient(135deg,#0a2a0a,#0a3a0a);'
                    f'border:2px solid #2ecc71;border-radius:12px;padding:20px;'
                    f'color:#d5f5e3;text-align:center;">'
                    f'<div style="font-size:2rem;">🏆 RACE WON!</div>'
                    f'<div style="font-size:1.2rem;margin-top:8px;">'
                    f'Clock bonus: +{_bonus} XP · Time left bonus: +{_time_bonus} XP · Streak bonus: +{_streak_bonus} XP</div>'
                    f'<div style="font-size:1.5rem;color:#f1c40f;margin-top:8px;font-weight:bold;">'
                    f'Total bonus: +{_total_bonus} XP</div>'
                    f'<div style="margin-top:12px;font-style:italic;font-size:0.95rem;color:#a0d8b0;">'
                    f'🦇 {_win_name}: "{_win_quote}"</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )
                if st.button("🎉 Claim Bonus & End Race", type="primary", use_container_width=True, key="race_claim"):
                    st.session_state.xp += _total_bonus
                    st.session_state.celebration_xp = _total_bonus
                    st.session_state.race_active = False
                    save_all_progress()
                    st.balloons()
                    st.rerun(scope="app")
            elif _race_secs <= 0:
                _partial = _race_completed * 5  # consolation XP
                _lose_quotes = [
                    ("Bane", "And when your edits are ashes, you have my permission to cry."),
                    ("Joker", "See, I'm not a monster. I'm just ahead of the curve. Unlike you."),
                    ("Ra's al Ghul", "But you are not done yet. Get up. Why do we fall, Bruce?"),
                    ("Scarecrow", "Your greatest fear has been realized. But fear can be a teacher."),
                    ("Alfred", "Why do we fall, sir? So that we can learn to pick ourselves up."),
                    ("Batman", "It's not who I am underneath, but what I do that defines me."),
                ]
                _lose_name, _lose_quote = random.choice(_lose_quotes)
                st.markdown(
                    f'<div style="background:linear-gradient(135deg,#2a0a0a,#3a0a0a);'
                    f'border:2px solid #e74c3c;border-radius:12px;padding:20px;'
                    f'color:#f5d5d5;text-align:center;">'
                    f'<div style="font-size:2rem;">⏰ TIME\'S UP!</div>'
                    f'<div style="font-size:1rem;margin-top:8px;">'
                    f'You completed {_race_completed}/{_race_target_count}. '
                    f'Consolation: +{_partial} XP</div>'
                    f'<div style="margin-top:12px;font-style:italic;font-size:0.95rem;color:#d4a0a0;">'
                    f'🦹 {_lose_name}: "{_lose_quote}"</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )
                if st.button("💪 Collect & Try Again", use_container_width=True, key="race_retry"):
                    st.session_state.xp += _partial
                    st.session_state.celebration_xp = _partial
                    st.session_state.race_active = False
                    save_all_progress()
                    st.rerun(scope="app")

            # Abort button — still get partial XP
            _abort_completed = st.session_state.get("race_completed", 0)
            _abort_xp = _abort_completed * 5
            _abort_label = f"🛑 Abort Race (+{_abort_xp} XP for {_abort_completed} done)" if _abort_completed > 0 else "🛑 Abort Race"
            if st.button(_abort_label, key="race_abort"):
                if _abort_xp > 0:
                    st.session_state.xp += _abort_xp
                    st.session_state.celebration_xp = _abort_xp
                    save_all_progress()
                    st.toast(f"🦇 +{_abort_xp} XP for {_abort_completed} items completed!", icon="🦇")
                st.session_state.race_active = False
                st.rerun(scope="app")

        if not _race_active:
            with st.expander("🏎️ **RACE THE CLOCK** — Blitz through feedback for bonus XP", expanded=False):
                st.markdown(
                    '<div style="background:#1a1a2e;border-left:4px solid #e74c3c;border-radius:8px;'
                    'padding:14px;color:#f0e6c8;margin-bottom:12px;">'
                    f'<b style="color:#e74c3c;">🦹 {_villain_name}:</b> <i>"{_villain_quote}"</i>'
                    '</div>',
                    unsafe_allow_html=True
                )
                st.markdown("**Set your challenge:**")
                _race_col1, _race_col2 = st.columns(2)
                _race_target = _race_col1.number_input(
                    "Items to complete:", min_value=1, max_value=len(_ekt_pending),
                    value=min(5, len(_ekt_pending)), key="race_target_input"
                )
                _race_presets = {"Quick Blitz (15m)": 15, "Sprint (30m)": 30, "Marathon (60m)": 60, "Custom": 0}
                _race_preset = _race_col2.selectbox("Time limit:", list(_race_presets.keys()), key="race_preset")
                if _race_preset == "Custom":
                    _race_minutes = _race_col2.number_input("Minutes:", min_value=5, max_value=120, value=20, key="race_custom_mins")
                else:
                    _race_minutes = _race_presets[_race_preset]

                _race_bonus = _race_target * 10  # bonus XP for beating the clock
                st.markdown(
                    f"**Challenge:** Complete **{_race_target} items** in **{_race_minutes} minutes**  \n"
                    f"**Bonus if you beat the clock:** +{_race_bonus} XP  \n"
                    f"**Bonus per item with time left:** +5 XP each"
                )

                if st.button("🏁 START RACE", type="primary", use_container_width=True, key="race_start"):
                    st.session_state.race_active = True
                    st.session_state.race_target = _race_target
                    st.session_state.race_completed = 0
                    st.session_state.race_end_time = datetime.now() + timedelta(minutes=_race_minutes)
                    st.session_state.race_bonus = _race_bonus
                    st.session_state.race_streak = 0
                    st.session_state.race_best_streak = 0
                    save_all_progress()
                    st.rerun()
        else:
            race_hud()

        st.divider()

        # Filter controls
        _ekt_col1, _ekt_col2, _ekt_col3, _ekt_col4 = st.columns(4)
        _ekt_paper_filter = _ekt_col1.selectbox(
            "Paper:", ["All", "HBMC", "Climate", "Delphi", "SCPA", "General"],
            key="ekt_paper_filter"
        )
        _ekt_type_filter = _ekt_col2.selectbox(
            "Triage:", ["All", "quick_fix", "clarification", "substantive", "major"],
            key="ekt_type_filter"
        )
        _ekt_status_filter = _ekt_col3.selectbox(
            "Status:", ["Pending", "Done", "All"],
            key="ekt_status_filter"
        )
        _ekt_reviewer_filter = _ekt_col4.selectbox(
            "Reviewer:", ["All", "Emma Tsui", "Emily"],
            key="ekt_reviewer_filter"
        )

        # Apply filters
        _filtered = _ekt_items
        if _ekt_paper_filter != "All":
            _filtered = [f for f in _filtered if f.get("paper") == _ekt_paper_filter]
        if _ekt_type_filter != "All":
            _filtered = [f for f in _filtered if f.get("action_type") == _ekt_type_filter]
        if _ekt_status_filter == "Pending":
            _filtered = [f for f in _filtered if f.get("status") == "pending"]
        elif _ekt_status_filter == "Done":
            _filtered = [f for f in _filtered if f.get("status") != "pending"]
        if _ekt_reviewer_filter != "All":
            _filtered = [f for f in _filtered if f.get("reviewer") == _ekt_reviewer_filter]

        # Bulk complete
        _bulk_pending = [f for f in _filtered if f.get("status") == "pending"]
        if _bulk_pending:
            with st.expander(f"⚡ Quick Complete — mark multiple done at once ({len(_bulk_pending)} pending)"):
                _bulk_options = {f"{f['id']} — {f.get('section','')} ({f.get('action_type','')})": f for f in _bulk_pending}
                _bulk_selected = st.multiselect("Select items to mark done:", list(_bulk_options.keys()), key="ekt_bulk_select")
                if _bulk_selected and st.button("✅ Mark Selected Done", type="primary", key="ekt_bulk_submit"):
                    _bulk_xp = 0
                    try:
                        for _label in _bulk_selected:
                            _bitem = _bulk_options[_label]
                            _bxp = _xp_per_type.get(_bitem.get("action_type", ""), 10)
                            if _bitem.get("reviewer") == "Emily":
                                _btid = _bitem.get("task_id")
                                if _btid:
                                    st.session_state.completed_tasks.add(_btid)
                            else:
                                get_mongo_db()["comps_feedback"].update_one(
                                    {"id": _bitem["id"]},
                                    {"$set": {"status": "done", "completed_at": datetime.now()}}
                                )
                                for _cached in st.session_state.get("comps_feedback_cache", []):
                                    if _cached.get("id") == _bitem["id"]:
                                        _cached["status"] = "done"
                                        _cached["completed_at"] = datetime.now()
                                        break
                            _bulk_xp += _bxp
                        st.session_state.xp += _bulk_xp
                        st.session_state.celebration_xp = _bulk_xp
                        _last_bitem = _bulk_options[_bulk_selected[-1]]
                        st.session_state.last_worked_section = _last_bitem.get("section", "")
                        st.session_state.last_worked_date = datetime.now().strftime("%b %d, %Y at %I:%M %p")
                        save_all_progress()
                        st.toast(f"+{_bulk_xp} XP — {len(_bulk_selected)} items crushed!", icon="🦇")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Bulk update failed: {e}")

        # Current item index
        if "ekt_current_idx" not in st.session_state:
            st.session_state.ekt_current_idx = 0

        if not _filtered:
            st.success("No items match your filters — nice work!")
        else:
            # Clamp index
            _idx = st.session_state.ekt_current_idx % len(_filtered)
            _item = _filtered[_idx]

            # Navigation
            def _sync_coach_to_ekt_item(item):
                """Sync sidebar walkthrough index and active item to the given EKT item."""
                sec = item.get("section", "")
                st.session_state.ekt_active_item = item  # store full item for coach prompt
                if not sec:
                    return
                _all_secs = list(SECTION_TASKS.keys())
                _extra = list({i.get("section") for i in st.session_state.get("comps_feedback_cache", []) if i.get("section")})
                for _s in _extra:
                    if _s not in _all_secs:
                        _all_secs.append(_s)
                if sec in _all_secs:
                    st.session_state.walkthrough_idx = _all_secs.index(sec)
                    st.session_state.walkthrough_introduced = -1
                    st.session_state.coach_messages = []

            # Always keep ekt_active_item pointing at the currently displayed item
            # and sync the sidebar Robin mission + active_mission to match
            if st.session_state.get("ekt_active_item", {}).get("id") != _item.get("id"):
                st.session_state.ekt_active_item = _item
                _atype = _item.get("action_type", "")
                if _atype in EKT_MISSION_MAP:
                    st.session_state.robin_active_mission = EKT_MISSION_MAP[_atype]
                # Drive sidebar "Current Focus Task" label via active_mission
                if not st.session_state.get("timer_running"):
                    _mid = _item.get("id", "")
                    _msec = _item.get("section", "General")
                    st.session_state.active_mission = f"{_mid}: {_msec}"

            _nav_col1, _nav_col2, _nav_col3 = st.columns([1, 4, 1])
            if _nav_col1.button("⬅️ Prev", key="ekt_prev", use_container_width=True):
                new_idx = (_idx - 1) % len(_filtered)
                st.session_state.ekt_current_idx = new_idx
                _sync_coach_to_ekt_item(_filtered[new_idx])
                st.rerun()
            _nav_col2.markdown(f"<div style='text-align:center;font-size:1.1rem;padding:6px;'><b>{_idx + 1} / {len(_filtered)}</b></div>", unsafe_allow_html=True)
            if _nav_col3.button("➡️ Next", key="ekt_next", use_container_width=True):
                new_idx = (_idx + 1) % len(_filtered)
                st.session_state.ekt_current_idx = new_idx
                _sync_coach_to_ekt_item(_filtered[new_idx])
                st.rerun()

            st.divider()

            # Item card
            _priority_color = {"high": "#e74c3c", "medium": "#f39c12", "low": "#27ae60", "none": "#888"}
            _type_icon = {"quick_fix": "⚡", "clarification": "💬", "substantive": "📝", "major": "🏗️", "none": "✅"}
            _p_color = _priority_color.get(_item.get("priority", "medium"), "#888")
            _t_icon = _type_icon.get(_item.get("action_type", ""), "📋")
            _xp_reward = _xp_per_type.get(_item.get("action_type", ""), 10)
            _is_done = _item.get("status") != "pending"

            _done_badge = '<div style="margin-top:12px;padding:8px 14px;background:#27ae6033;border-radius:8px;color:#2ecc71;font-weight:bold;">✅ COMPLETED</div>' if _is_done else ''
            st.markdown(
                f'<div style="background:linear-gradient(135deg,#1a1a2e,#0f3460);'
                f'border-left:4px solid {_p_color};border-radius:12px;padding:20px;'
                f'color:#f0e6c8;margin:8px 0;">'
                f'<div style="display:flex;justify-content:space-between;align-items:center;">'
                f'<span style="font-size:1.2rem;font-weight:bold;color:#f1c40f;">'
                f'{_t_icon} {_item.get("id", "")} — {_item.get("section", "")}</span>'
                f'<span style="background:{_p_color}22;color:{_p_color};padding:4px 12px;'
                f'border-radius:20px;font-size:0.8rem;font-weight:600;">'
                f'{_item.get("priority", "").upper()}</span></div>'
                f'<div style="margin-top:4px;font-size:0.85rem;color:#aaa;">'
                f'Paper: {_item.get("paper", "")} · {_item.get("action_type", "")} · ~{_item.get("estimated_minutes", "?")}min'
                f' · <span style="color:#f1c40f;font-weight:bold;">+{_xp_reward} XP</span></div>'
                f'<hr style="border-color:#333;margin:12px 0;">'
                f'<div style="font-size:1.05rem;line-height:1.8;">{_item.get("feedback", "")}</div>'
                f'{_done_badge}'
                f'</div>',
                unsafe_allow_html=True
            )

            # Action buttons
            if not _is_done:
                st.write("")
                _act_col1, _act_col2, _act_col3 = st.columns(3)

                if _act_col1.button("✅ Mark Done — Earn XP!", key=f"ekt_done_{_item['id']}",
                                     type="primary", use_container_width=True):
                    try:
                        if _item.get("reviewer") == "Emily":
                            # Emily items tracked via completed_tasks
                            _tid = _item.get("task_id")
                            if _tid:
                                st.session_state.completed_tasks.add(_tid)
                        else:
                            # Emma items tracked in MongoDB + cache
                            get_mongo_db()["comps_feedback"].update_one(
                                {"id": _item["id"]},
                                {"$set": {"status": "done", "completed_at": datetime.now()}}
                            )
                            for _cached in st.session_state.get("comps_feedback_cache", []):
                                if _cached.get("id") == _item["id"]:
                                    _cached["status"] = "done"
                                    _cached["completed_at"] = datetime.now()
                                    break
                        st.session_state.xp += _xp_reward
                        st.session_state.celebration_xp = _xp_reward
                        st.session_state.last_worked_section = _item.get("section", "")
                        st.session_state.last_worked_date = datetime.now().strftime("%b %d, %Y at %I:%M %p")
                        # Race the clock tracking
                        if st.session_state.get("race_active"):
                            st.session_state.race_completed = st.session_state.get("race_completed", 0) + 1
                            st.session_state.race_streak = st.session_state.get("race_streak", 0) + 1
                            if st.session_state.race_streak > st.session_state.get("race_best_streak", 0):
                                st.session_state.race_best_streak = st.session_state.race_streak
                        save_all_progress()
                        # Contextual toast: show section + how many of this paper are left
                        _done_after = sum(
                            1 for i in _ekt_items
                            if i.get("paper") == _item.get("paper") and (
                                i.get("status") != "pending" if i.get("reviewer") != "Emily"
                                else i.get("task_id") in st.session_state.completed_tasks
                            )
                        )
                        _paper_total = sum(1 for i in _ekt_items if i.get("paper") == _item.get("paper"))
                        _type_labels = {"quick_fix": "quick fix", "clarification": "clarification", "substantive": "revision", "major": "major revision"}
                        _tlabel = _type_labels.get(_item.get("action_type", ""), "item")
                        _sec_short = (_item.get("section", "")[:28] + "…") if len(_item.get("section", "")) > 28 else _item.get("section", "")
                        st.toast(f"+{_xp_reward} XP — {_tlabel} done · {_sec_short} · {_item.get('paper','')} {_done_after}/{_paper_total}", icon="🦇")
                        st.balloons()
                        # Auto-advance to next
                        st.session_state.ekt_current_idx = (_idx + 1) % len(_filtered)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to update: {e}")

                # Focus timer button
                _ekt_mission = f"{_item['id']}: {_item.get('section', '')} ({_item.get('paper', '')})"
                _timer_active = st.session_state.get('timer_running', False)
                _on_this = st.session_state.get('active_mission', '') == _ekt_mission
                if _timer_active and _on_this:
                    if _act_col2.button("🔄 Reset Timer", key=f"ekt_reset_{_item['id']}",
                                         use_container_width=True):
                        st.session_state.timer_running = False
                        st.session_state.timer_paused = False
                        st.session_state.target_time = None
                        st.session_state.active_mission = ""
                        save_all_progress()
                        st.rerun()
                elif not _timer_active:
                    _est = _item.get("estimated_minutes", 25)
                    _timer_mins = max(_est, 10)  # minimum 10min sprint
                    if _act_col2.button(f"🚀 {_timer_mins}m Sprint", key=f"ekt_timer_{_item['id']}",
                                         use_container_width=True):
                        st.session_state.active_mission = _ekt_mission
                        st.session_state.target_time = datetime.now() + timedelta(minutes=_timer_mins)
                        st.session_state.timer_running = True
                        st.session_state.timer_paused = False
                        save_all_progress()
                        st.toast(f"🚀 {_timer_mins}m sprint started for {_item['id']}!", icon="🦇")
                        st.rerun()
                else:
                    if _act_col2.button("🔄 Reset Timer", key=f"ekt_reset_other_{_item['id']}",
                                         use_container_width=True):
                        st.session_state.timer_running = False
                        st.session_state.timer_paused = False
                        st.session_state.target_time = None
                        st.session_state.active_mission = ""
                        save_all_progress()
                        st.rerun()

                if _act_col3.button("⏭️ Skip", key=f"ekt_skip_{_item['id']}",
                                     use_container_width=True):
                    # Break streak on skip during race
                    if st.session_state.get("race_active"):
                        st.session_state.race_streak = 0
                    st.session_state.ekt_current_idx = (_idx + 1) % len(_filtered)
                    st.rerun()
            else:
                if st.button("⏭️ Next Item", key=f"ekt_next_done_{_item['id']}",
                              use_container_width=True):
                    st.session_state.ekt_current_idx = (_idx + 1) % len(_filtered)
                    st.rerun()

        # Stats section
        st.divider()
        st.subheader("📊 Breakdown")
        _stats_col1, _stats_col2, _stats_col3 = st.columns(3)

        with _stats_col1:
            st.markdown("**By Reviewer:**")
            for _rev, _rev_icon in [("Emma Tsui", "🦇"), ("Emily", "📋")]:
                _rev_items = [f for f in _ekt_items if f.get("reviewer") == _rev]
                _rev_done = [f for f in _rev_items if f.get("status") != "pending"]
                if _rev_items:
                    st.progress(len(_rev_done) / len(_rev_items),
                                text=f"{_rev_icon} {_rev}: {len(_rev_done)}/{len(_rev_items)}")

        with _stats_col2:
            st.markdown("**By Paper:**")
            for _paper in ["HBMC", "Climate", "Delphi", "SCPA", "General"]:
                _paper_items = [f for f in _ekt_items if f.get("paper") == _paper]
                _paper_done = [f for f in _paper_items if f.get("status") != "pending"]
                if _paper_items:
                    st.progress(len(_paper_done) / len(_paper_items),
                                text=f"{_paper}: {len(_paper_done)}/{len(_paper_items)}")

        with _stats_col3:
            st.markdown("**By Triage:**")
            for _atype, _icon in [("quick_fix", "⚡"), ("clarification", "💬"), ("substantive", "📝"), ("major", "🏗️")]:
                _type_items = [f for f in _ekt_items if f.get("action_type") == _atype]
                _type_done = [f for f in _type_items if f.get("status") != "pending"]
                if _type_items:
                    st.progress(len(_type_done) / len(_type_items),
                                text=f"{_icon} {_atype}: {len(_type_done)}/{len(_type_items)}")
    else:
        st.info("No feedback items found.")

# ── COMPS COACH FLOATING BUTTON ──────────────────────────────────────────────
import anthropic as _anthropic
_comps_client = _anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])
_context_data = {
    "xp": st.session_state.xp,
    "section_timers": st.session_state.get("section_timers", {}),
    "saved_responses": st.session_state.saved_responses,
    "last_worked_section": st.session_state.get("last_worked_section", ""),
    "last_worked_date": st.session_state.get("last_worked_date", ""),
}
render_floating_button()
render_comps_modal(_comps_client, _context_data)

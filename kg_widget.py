"""
kg_widget.py — Shared "Knowledge Graph" visualization (sci-fi terminal style)
ใช้ร่วมกันทั้งหน้าแรก (ai_team.py) และหน้า งานบริษัทอาควาไลน์ (pages/1_...py)
และทุกหน้าที่แสดง Knowledge Graph (Live Chat / Brief ด่วน / Workflow Builder / คุยกับ AI Agent)

สไตล์/กลไกอ้างอิงจากไฟล์ตัวอย่างที่ผู้ใช้ให้มา (knowledge_graph.py):
- Force-directed physics (spring + repulsion + recenter + random jitter) ทำให้ node เคลื่อนไหวตลอดเวลาแบบสุ่ม/ยุ่งเหยิง
- ลาก node ได้ / pan-zoom ผืนผ้าใบได้
- Node เรืองแสง/กระพริบ (pulse) เมื่อ "active"
- Knowledge particles ("ความคิด" ของ agent) ลอยขึ้นพร้อมป้ายคำที่กำลัง "คิด/ทำงาน" อยู่ — มีเส้นเชื่อมกับ agent เจ้าของ (บางกว่าเส้น agent-agent) พร้อมแสงวิ่งไปตามเส้น และอยู่นานขึ้น
- Communication particles (แสงวิ่งส่งข้อมูล) วิ่งไปตามเส้นเชื่อม agent-agent จริง ๆ (ไม่ใช่เส้นสุ่มลอย ๆ)
- Log bar หมุนข้อความสถานะ, Node Inspector แสดงรายละเอียด node ที่ชี้
- รองรับ "theme" ปรับแต่งได้ (สีเส้น/ความหนาเส้น/ความเร็ว/สี-ชื่อ agent) ดูจาก DEFAULT_THEME ด้านล่าง
"""

import json
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from agent_default_personas import AGENT_META

AGENT_IDS = list(AGENT_META.keys())

# พื้นที่ chrome (topbar/banner/controls/inspector/logbar) ที่ต้องเผื่อความสูงเพิ่มจาก canvas
# (ลดจาก 250 เพราะของเดิมเผื่อพื้นที่เกินจริงมาก ทำให้เกิดช่องว่างเปล่าๆด้านล่างกราฟก่อนเนื้อหาถัดไป)
FULL_EXTRA_PX = 200
MINI_EXTRA_PX = 34

# ════════════════════════════════════════════════════════════════════
# THEME — ค่าปรับแต่งเริ่มต้น (ผู้ใช้แก้ไขได้จากหน้า Design UX/UI ผ่าน ui_settings.py)
# ════════════════════════════════════════════════════════════════════
DEFAULT_THEME = {
    "line_color_agent": "#00ccff",     # สีเส้นเชื่อม agent-agent
    "line_color_thought": "#7dd3fc",   # สีเส้นเชื่อม agent-ความคิด (บางกว่า)
    "line_width_agent": 2,             # ความหนาเส้น agent-agent
    "line_width_thought": 1.4,         # ความหนาเส้น agent-ความคิด (ควรเล็กกว่า line_width_agent)
    "speed_multiplier": 1.0,           # ความเร็วการเคลื่อนไหว/อนิเมชันโดยรวม
    "agent_colors": {},                # aid -> "#hex" (ทับสีเริ่มต้นของ agent)
    "agent_names": {},                 # aid -> ชื่อที่ต้องการแสดงใน graph (ทับชื่อเริ่มต้น)
}


def _merged_theme(theme=None):
    t = dict(DEFAULT_THEME)
    if theme:
        for k, v in theme.items():
            if k in ("agent_colors", "agent_names"):
                continue
            if v is not None:
                t[k] = v
        if theme.get("agent_colors"):
            t["agent_colors"] = theme["agent_colors"]
        if theme.get("agent_names"):
            t["agent_names"] = theme["agent_names"]
    return t


def _hub_node():
    return {
        "id": "HUB", "name": "AQUALINE", "icon": "🏢",
        "color": "#0ea5e9", "glow": "#7dd3fc",
        "x": 0.5, "y": 0.5, "r": 26,
        "info": "ศูนย์กลางข้อมูลบริษัท AQUALINE — เชื่อมต่อ AI Agent ทั้งหมด 26 ตัว",
    }


def _agent_nodes(theme=None):
    """วาง agent เริ่มต้นแบบกระจายสุ่ม (ไม่ใช่วงกลมเรียบ ๆ) เพื่อให้การเคลื่อนไหวดูยุ่งเหยิง/เป็นธรรมชาติ
    มากกว่าการลู่เข้าหากันจากวงใหญ่ที่เป็นระเบียบ"""
    theme = theme or {}
    color_overrides = theme.get("agent_colors", {}) or {}
    name_overrides = theme.get("agent_names", {}) or {}
    n = len(AGENT_IDS)
    nodes = []
    for i, aid in enumerate(AGENT_IDS):
        meta = AGENT_META[aid]
        base_ang = (2 * math.pi * i / n) - math.pi / 2
        ang = base_ang + random.uniform(-0.65, 0.65)
        rad = random.uniform(0.20, 0.42)
        color = color_overrides.get(aid) or meta.get("color", "#3b82f6")
        name = name_overrides.get(aid) or meta["name"]
        nodes.append({
            "id": aid,
            "name": name,
            "icon": meta.get("icon", "🤖"),
            "color": color,
            "glow": color,
            "x": round(0.5 + rad * math.cos(ang), 4),
            "y": round(0.5 + rad * math.sin(ang) * 0.82, 4),
            "r": 14,
            "info": f"{meta.get('icon','')} {name} ({aid}) · {meta.get('p','')}",
        })
    return nodes


def build_nodes(theme=None):
    return [_hub_node()] + _agent_nodes(theme)


EDGES = [["HUB", aid] for aid in AGENT_IDS] + [
    ["A1", "A11"], ["A1", "A10"], ["A1", "A17"], ["A1", "A26"], ["A1", "A25"],
    ["A11", "A4"], ["A11", "A6"], ["A11", "A12"], ["A11", "A13"],
    ["A3", "A4"], ["A3", "A24"], ["A3", "A21"],
    ["A7", "A8"], ["A7", "A22"], ["A8", "A21"],
    ["A9", "A23"], ["A9", "A19"],
    ["A10", "A22"], ["A14", "A15"],
    ["A17", "A26"], ["A17", "A25"], ["A17", "A1"],
    ["A19", "A22"], ["A20", "A18"], ["A2", "A15"],
    ["A5", "A4"], ["A6", "A12"], ["A16", "A4"], ["A25", "A19"],
]
EDGES = [[a, b] for a, b in EDGES if a in AGENT_IDS + ["HUB"] and b in AGENT_IDS + ["HUB"]]


def _knowledge_tags():
    tags = []
    for aid in AGENT_IDS:
        meta = AGENT_META[aid]
        label = (meta.get("p") or meta["name"])[:18]
        tags.append({"l": label, "c": meta.get("color", "#38bdf8"), "p": aid})
    return tags


def _logs(name_overrides=None):
    name_overrides = name_overrides or {}
    logs = ["[ SYS ] AQUALINE Knowledge Graph initialized · All systems nominal"]
    for aid in AGENT_IDS:
        meta = AGENT_META[aid]
        name = name_overrides.get(aid) or meta["name"]
        logs.append(f"[ {aid} ] {meta.get('icon','')} {name}: กำลัง{meta.get('p','ทำงาน')}")
    return logs


# ════════════════════════════════════════════════════════════════════
# FULL GRAPH — sci-fi terminal เต็มรูปแบบ (physics + drag + zoom/pan + controls)
# ════════════════════════════════════════════════════════════════════
FULL_GRAPH_TEMPLATE = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Orbitron:wght@400;700&display=swap');
*{margin:0;padding:0;box-sizing:border-box}
#kg-root{background:#020a12;border-radius:10px;font-family:'Share Tech Mono',monospace;width:100%;display:flex;flex-direction:column;border:1px solid #0a2535}
#topbar{display:flex;align-items:center;justify-content:space-between;padding:8px 16px;background:#030d18;border-bottom:1px solid #0a2a3a;flex-wrap:wrap;gap:6px}
.sys-label{font-size:11px;color:#0ff;letter-spacing:.18em;font-family:'Orbitron',monospace;text-shadow:0 0 8px #0ff8}
.stats{display:flex;gap:16px}
.stat{font-size:10px;color:#0a8;letter-spacing:.1em;display:flex;align-items:center;gap:5px}
.dot{width:7px;height:7px;border-radius:50%;display:inline-block}
.dot.g{background:#0f9;box-shadow:0 0 6px #0f9}
.dot.a{background:#fa0;box-shadow:0 0 6px #fa0}
.dot.b{background:#0ff;box-shadow:0 0 6px #0ff}
canvas#kg{display:block;width:100%;cursor:grab}
canvas#kg:active{cursor:grabbing}
#controls{display:flex;gap:8px;padding:8px 16px;background:#030d18;border-top:1px solid #0a2030;border-bottom:1px solid #0a2030;flex-wrap:wrap;align-items:center}
.ctrl-btn{background:#041020;border:1px solid #0a3a5a;border-radius:4px;color:#0cf;font-size:10px;font-family:'Share Tech Mono',monospace;padding:4px 10px;cursor:pointer;letter-spacing:.08em;transition:all .15s}
.ctrl-btn:hover{border-color:#0cf;background:#062030;box-shadow:0 0 8px #0cf4}
.ctrl-label{font-size:10px;color:#0a6;letter-spacing:.1em;margin-right:4px}
#a26-banner{display:none;background:#031a1c;border-top:1px solid #0c4;border-bottom:1px solid #0c4;padding:6px 16px;font-size:11px;color:#22d3ee;letter-spacing:.05em;align-items:center;gap:8px}
#a26-banner.show{display:flex}
#meet-banner{display:none;background:#1a0f2e;border-top:1px solid #a78bfa;border-bottom:1px solid #a78bfa;padding:6px 16px;font-size:11px;color:#c4b5fd;letter-spacing:.05em;align-items:center;gap:8px}
#meet-banner.show{display:flex}
#inspector{background:#030d18;border-top:1px solid #0a2030;padding:8px 16px;min-height:46px}
.ins-label{font-size:9px;color:#0cf;letter-spacing:.15em;margin-bottom:4px;font-family:'Orbitron',monospace}
.ins-body{font-size:11px;color:#0a9;line-height:1.5;font-family:'Share Tech Mono',monospace}
#logbar{background:#010810;border-top:1px solid #061828;padding:5px 16px;font-size:10px;color:#0a5;font-family:'Share Tech Mono',monospace;letter-spacing:.05em;white-space:nowrap;overflow:hidden}
</style>

<div id="kg-root">
<div id="topbar">
  <div class="sys-label">◈ __TITLE__ — LIVE</div>
  <div class="stats">
    <div class="stat"><span class="dot g"></span><span>SYS:ONLINE</span></div>
    <div class="stat"><span class="dot a"></span><span>ACTIVE:<span id="ac">0</span></span></div>
    <div class="stat"><span class="dot b"></span><span>NODES:<span id="nc">0</span></span></div>
  </div>
</div>

<div id="a26-banner"><span>🕵️</span><span id="a26-banner-text"></span></div>
<div id="meet-banner"><span>🗣️</span><span id="meet-banner-text"></span></div>

<canvas id="kg" height="__HEIGHT__"></canvas>

<div id="controls">
  <span class="ctrl-label">CONTROL:</span>
  <button class="ctrl-btn" onclick="resetView()">⟳ RESET</button>
  <button class="ctrl-btn" onclick="zoomIn()">＋ ZOOM</button>
  <button class="ctrl-btn" onclick="zoomOut()">－ ZOOM</button>
  <button class="ctrl-btn" onclick="togglePhysics()">⚡ PHYSICS: <span id="phys-label">ON</span></button>
</div>

<div id="inspector">
  <div class="ins-label">▸ NODE INSPECTOR</div>
  <div class="ins-body" id="ins-body">ลาก node เพื่อย้าย · scroll เพื่อ zoom · ลากพื้นหลังเพื่อ pan · ชี้ที่ agent เพื่อดูรายละเอียด</div>
</div>

<div id="logbar"><span id="lt">[ SYS ] AQUALINE Knowledge Graph initialized</span></div>
</div>

<script>
const C=document.getElementById('kg'),ctx=C.getContext('2d');
let W,H=__HEIGHT__,scale=1,panX=0,panY=0,dragging=null,panning=false,lastMX=0,lastMY=0,physicsOn=true;
function resize(){W=C.parentElement.offsetWidth;C.width=W;C.height=H;}
resize();window.addEventListener('resize',resize);

const AGENTS=__NODES_JSON__;
const EDGES=__EDGES_JSON__;
const KT=__KT_JSON__;
const LOGS=__LOGS_JSON__;
const A26_PHASE="__A26_PHASE__";
const A26_STATUS_TEXT="__A26_STATUS__";
const ACTIVE_IDS=__ACTIVE_IDS_JSON__;
const ACTIVE_LABEL="__ACTIVE_LABEL__";
const LINE_COLOR_AGENT="__LINE_COLOR_AGENT__";
const LINE_COLOR_THOUGHT="__LINE_COLOR_THOUGHT__";
const LINE_WIDTH_AGENT=__LINE_WIDTH_AGENT__;
const LINE_WIDTH_THOUGHT=__LINE_WIDTH_THOUGHT__;
const SPEED_MULT=__SPEED_MULT__;

let kn=[],pts=[],fr=0,hov=null,logIdx=0;
const STARS=Array.from({length:160},()=>{
  const r=.4+Math.random()*1.6;
  return {x:Math.random(),y:Math.random(),r,ph:Math.random()*Math.PI*2,sp:.01+Math.random()*.02,dx:(Math.random()-.5)*.00014*r,dy:(Math.random()-.5)*.00014*r};
});
const active = ACTIVE_IDS.length ? new Set(['HUB',...ACTIVE_IDS]) : new Set(AGENTS.map(a=>a.id));
const ACTIVE_SET = new Set(ACTIVE_IDS);
const biasEdges = EDGES.filter(([a,b])=>ACTIVE_SET.has(a)||ACTIVE_SET.has(b));
const CLUSTERS = AGENTS.filter(a=>a.id!=='HUB').map(a=>{
  const n=16+Math.floor(Math.random()*9);
  const spread=(22+Math.random()*10)*2;
  const dots=Array.from({length:n},(_,di)=>{
    const ang=Math.random()*Math.PI*2,rad=spread*Math.sqrt(Math.random());
    return {ox:Math.cos(ang)*rad,oy:Math.sin(ang)*rad,dph:Math.random()*Math.PI*2,dfx:.02+Math.random()*.03,dfy:.02+Math.random()*.03,damp:1+Math.random()*1.6,core:di<3};
  });
  const edges=[],seen=new Set();
  dots.forEach((d,i)=>{
    const order=dots.map((d2,j)=>({j,dist:i===j?Infinity:Math.hypot(d.ox-d2.ox,d.oy-d2.oy)})).sort((p,q)=>p.dist-q.dist);
    for(let k=0;k<2;k++){
      const j=order[k].j,key=i<j?i+'_'+j:j+'_'+i;
      if(!seen.has(key)){seen.add(key);edges.push([i,j]);}
    }
  });
  for(let c=0;c<3;c++){
    const i=Math.floor(Math.random()*n),j=Math.floor(Math.random()*n);
    if(i!==j){const key=i<j?i+'_'+j:j+'_'+i;if(!seen.has(key)){seen.add(key);edges.push([i,j]);}}
  }
  return {aid:a.id,dots,edges,spread};
});
function hitR(a){
  if(a.id==='HUB')return a.r+10;
  const cl=CLUSTERS.find(c=>c.aid===a.id);
  return cl?cl.spread+26:a.r+24;
}

if(A26_PHASE==='running'){
  const b=document.getElementById('a26-banner');
  b.classList.add('show');
  document.getElementById('a26-banner-text').textContent=A26_STATUS_TEXT;
}

if(ACTIVE_IDS.length){
  const mb=document.getElementById('meet-banner');
  mb.classList.add('show');
  document.getElementById('meet-banner-text').textContent=ACTIVE_LABEL;
  ACTIVE_IDS.forEach(pid=>{spK(pid);});
}

function spK(pid){
  const a=AGENTS.find(x=>x.id===pid);if(!a)return;
  const ts=KT.filter(t=>t.p===pid);
  const t=(ts.length?ts:KT)[Math.floor(Math.random()*(ts.length?ts.length:KT.length))];
  if(!t)return;
  const ang=Math.random()*Math.PI*2,d=(70+Math.random()*90)/W;
  kn.push({l:t.l,c:t.c,pid,x:a.x+Math.cos(ang)*d,y:a.y+Math.sin(ang)*d*W/H,r:5+Math.random()*3.5,al:0,age:0,max:420+Math.random()*260,vx:(Math.random()-.5)*.0006,vy:(Math.random()-.5)*.0006,pT:Math.random(),pSp:.014+Math.random()*.01});
}
function spP(a1,a2){
  const s=AGENTS.find(a=>a.id===a1),e=AGENTS.find(a=>a.id===a2);if(!s||!e)return;
  const x1=s.x*W,y1=s.y*H,x2=e.x*W,y2=e.y*H;
  const mx=(x1+x2)/2,my=(y1+y2)/2,dx=x2-x1,dy=y2-y1,dist=Math.hypot(dx,dy)||1;
  const wob=(Math.random()<.5?-1:1)*Math.min(26,dist*.14)*(.5+Math.random()*.5);
  const cx=mx-dy/dist*wob,cy=my+dx/dist*wob;
  pts.push({x1,y1,cx,cy,x2,y2,c:LINE_COLOR_AGENT,t:0,sp:.032+Math.random()*.026});
}

function drawScene(){
  ctx.clearRect(0,0,W,H);ctx.fillStyle='#020a12';ctx.fillRect(0,0,W,H);
  ctx.save();
  const step=40,ox=((panX%step)+step)%step,oy=((panY%step)+step)%step;
  ctx.strokeStyle='#071828';ctx.lineWidth=.4;
  for(let x=ox;x<W;x+=step){ctx.beginPath();ctx.moveTo(x,0);ctx.lineTo(x,H);ctx.stroke();}
  for(let y=oy;y<H;y+=step){ctx.beginPath();ctx.moveTo(0,y);ctx.lineTo(W,y);ctx.stroke();}
  ctx.restore();
  ctx.save();ctx.translate(panX,panY);ctx.scale(scale,scale);

  ctx.save();ctx.fillStyle='#bfe8ff';
  STARS.forEach(s=>{
    const tw=.35+.45*Math.sin(fr*s.sp+s.ph);
    ctx.globalAlpha=Math.max(.08,tw*.5);
    ctx.beginPath();ctx.arc(s.x*W,s.y*H,s.r,0,Math.PI*2);ctx.fill();
  });
  ctx.restore();

  EDGES.forEach(([a,b],_ei)=>{
    const pa=AGENTS.find(x=>x.id===a),pb=AGENTS.find(x=>x.id===b);if(!pa||!pb)return;
    const on=active.has(a)&&active.has(b);
    const isA26=(a==='A26'||b==='A26')&&A26_PHASE==='running';
    const x1=pa.x*W,y1=pa.y*H,x2=pb.x*W,y2=pb.y*H;
    const dx=x2-x1,dy=y2-y1;
    ctx.save();
    ctx.globalAlpha=isA26?1:on?.85:.2;
    ctx.strokeStyle=isA26?'#22d3ee':on?LINE_COLOR_AGENT:'#1a3a5a';
    ctx.lineWidth=(isA26?LINE_WIDTH_AGENT+1:on?LINE_WIDTH_AGENT:0.8)/scale;
    ctx.shadowBlur=isA26?14:on?7:0;ctx.shadowColor=isA26?'#22d3ee':LINE_COLOR_AGENT;
    ctx.setLineDash([7/scale,5/scale]);
    ctx.beginPath();ctx.moveTo(x1,y1);ctx.lineTo(x2,y2);ctx.stroke();
    ctx.setLineDash([]);ctx.shadowBlur=0;ctx.restore();
    const spT=.0028+(_ei%5)*.0006,rawT=(fr*spT+_ei*.173)%1,travelT=_ei%2===0?rawT:1-rawT;
    const tx=x1+dx*travelT,ty=y1+dy*travelT;
    ctx.save();
    ctx.globalAlpha=on?.3:.08;
    ctx.beginPath();ctx.arc(tx,ty,5.5/scale,0,Math.PI*2);ctx.fillStyle=isA26?'#22d3ee':LINE_COLOR_AGENT;ctx.fill();
    ctx.globalAlpha=on?1:.3;ctx.shadowBlur=isA26?16:10;ctx.shadowColor=isA26?'#22d3ee':LINE_COLOR_AGENT;
    ctx.beginPath();ctx.arc(tx,ty,2.6/scale,0,Math.PI*2);ctx.fillStyle='#eaffff';ctx.fill();
    ctx.shadowBlur=0;ctx.restore();
  });

  pts.forEach(p=>{
    const it=1-p.t;
    const x=it*it*p.x1+2*it*p.t*p.cx+p.t*p.t*p.x2;
    const y=it*it*p.y1+2*it*p.t*p.cy+p.t*p.t*p.y2;
    ctx.save();ctx.globalAlpha=(1-p.t)*.95;ctx.shadowBlur=14;ctx.shadowColor=p.c;
    ctx.beginPath();ctx.arc(x,y,3.2/scale,0,Math.PI*2);ctx.fillStyle=p.c;ctx.fill();
    ctx.globalAlpha=(1-p.t)*.35;ctx.beginPath();ctx.arc(x,y,6/scale,0,Math.PI*2);ctx.fill();
    ctx.restore();
  });

  AGENTS.forEach(a=>{
    const ax=a.x*W,ay=a.y*H,on=active.has(a.id),hv=hov&&hov.id===a.id;
    const isA26Run=(a.id==='A26'&&A26_PHASE==='running');
    const isHub=a.id==='HUB';
    const pu=on?(.85+.15*Math.sin(fr*.07+a.x*8)):1,rr=a.r*pu*(isA26Run?1.18:1);
    const cl=isHub?null:CLUSTERS.find(c=>c.aid===a.id);
    let labelR=rr;
    ctx.save();
    if(isHub){
      const slowPulse=.5+.5*Math.sin(fr*.018);
      const fastPulse=.5+.5*Math.sin(fr*.07);
      const corePulse=slowPulse*.7+fastPulse*.3;
      for(let ring=7;ring>=1;ring--){
        ctx.globalAlpha=(.075+.055*corePulse)/ring;
        ctx.shadowBlur=34+ring*12;ctx.shadowColor=a.glow;
        ctx.beginPath();ctx.arc(ax,ay,rr+ring*17+slowPulse*8,0,Math.PI*2);ctx.fillStyle=a.glow;ctx.fill();
      }
      ctx.shadowBlur=0;
      ctx.save();
      ctx.translate(ax,ay);ctx.rotate(fr*.012);
      ctx.globalAlpha=.65+.3*slowPulse;ctx.strokeStyle=a.glow;ctx.lineWidth=1.6/scale;
      ctx.beginPath();ctx.ellipse(0,0,rr+10+slowPulse*3,(rr+10+slowPulse*3)*.42,0,0,Math.PI*2);ctx.stroke();
      ctx.restore();
      const grad=ctx.createRadialGradient(ax-rr*.32,ay-rr*.32,rr*.08,ax,ay,rr+corePulse*3);
      grad.addColorStop(0,'#f3fbff');grad.addColorStop(.32,'#bdeeff');grad.addColorStop(.62,a.color);grad.addColorStop(1,'#03101a');
      ctx.globalAlpha=1;ctx.beginPath();ctx.arc(ax,ay,rr+corePulse*3,0,Math.PI*2);ctx.fillStyle=grad;ctx.fill();
      ctx.strokeStyle=a.glow;ctx.lineWidth=1.5/scale;ctx.stroke();
      ctx.globalAlpha=.55+.35*fastPulse;ctx.shadowBlur=14;ctx.shadowColor='#fff';
      ctx.beginPath();ctx.arc(ax-rr*.18,ay-rr*.18,rr*.16,0,Math.PI*2);ctx.fillStyle='#ffffff';ctx.fill();ctx.shadowBlur=0;
    }else if(cl){
      const cSc=pu*(isA26Run?1.18:1);
      const tint=isA26Run?'#22d3ee':a.glow;
      labelR=cl.spread*cSc;
      const haloR=labelR*1.9;
      ctx.globalAlpha=on?(isA26Run?.22:.14):.05;ctx.shadowBlur=0;
      const hg=ctx.createRadialGradient(ax,ay,0,ax,ay,haloR);
      hg.addColorStop(0,tint);hg.addColorStop(1,'rgba(0,0,0,0)');
      ctx.beginPath();ctx.arc(ax,ay,haloR,0,Math.PI*2);ctx.fillStyle=hg;ctx.fill();
      const live=cl.dots.map(d=>({
        x:ax+d.ox*cSc+Math.sin(fr*d.dfx+d.dph)*d.damp,
        y:ay+d.oy*cSc+Math.cos(fr*d.dfy+d.dph)*d.damp,
        core:d.core
      }));
      ctx.strokeStyle=tint;ctx.lineWidth=.7/scale;ctx.globalAlpha=on?.5:.15;
      cl.edges.forEach(([i,j])=>{ctx.beginPath();ctx.moveTo(live[i].x,live[i].y);ctx.lineTo(live[j].x,live[j].y);ctx.stroke();});
      live.forEach(p=>{
        ctx.globalAlpha=on?1:.3;ctx.shadowBlur=p.core?(hv?12:7):0;ctx.shadowColor=tint;
        ctx.beginPath();ctx.arc(p.x,p.y,(p.core?2.6:1.3)*(hv?1.2:1),0,Math.PI*2);
        ctx.fillStyle=p.core?'#ffffff':a.color;ctx.fill();ctx.shadowBlur=0;
      });
      if(hv){
        ctx.globalAlpha=.5;ctx.strokeStyle='#fff';ctx.lineWidth=1/scale;ctx.setLineDash([3/scale,3/scale]);
        ctx.beginPath();ctx.arc(ax,ay,labelR+6,0,Math.PI*2);ctx.stroke();ctx.setLineDash([]);
      }
    }
    ctx.globalAlpha=on?1:.3;ctx.fillStyle=on?a.glow:'#1a3040';ctx.font=`700 ${9/scale}px 'Orbitron'`;ctx.textAlign='center';ctx.textBaseline='middle';
    ctx.fillText(isHub?a.name:a.id,ax,ay+labelR+11/scale);
    ctx.restore();
  });

  // กลุ่มความคิด (thought) วาดทับบนสุดเสมอ กันไม่ให้ก้อนจุด agent (ที่ขยายใหญ่ขึ้น) บังเส้น/จุดความคิด
  kn.forEach(k=>{
    const pa=AGENTS.find(a=>a.id===k.pid);if(!pa)return;
    const lx=pa.x*W,ly=pa.y*H,kx=k.x*W,ky=k.y*H;
    ctx.save();
    // เส้นเชื่อม agent -> ความคิด (บางกว่าเส้น agent-agent เสมอ และมองเห็นชัดขึ้น)
    ctx.globalAlpha=Math.min(1,.3+k.al*.65);
    ctx.strokeStyle=LINE_COLOR_THOUGHT;ctx.lineWidth=LINE_WIDTH_THOUGHT/scale;ctx.setLineDash([2/scale,4/scale]);
    ctx.beginPath();ctx.moveTo(lx,ly);ctx.lineTo(kx,ky);ctx.stroke();ctx.setLineDash([]);
    // แสงวิ่งเล็กๆ ไปตามเส้นความคิด
    const gx=lx+(kx-lx)*k.pT,gy=ly+(ky-ly)*k.pT;
    ctx.globalAlpha=k.al*.95;ctx.shadowBlur=7;ctx.shadowColor=LINE_COLOR_THOUGHT;
    ctx.beginPath();ctx.arc(gx,gy,1.7/scale,0,Math.PI*2);ctx.fillStyle=LINE_COLOR_THOUGHT;ctx.fill();ctx.shadowBlur=0;
    // ตัวความคิด (จุดเรืองแสง + halo + label)
    ctx.globalAlpha=k.al*.14;ctx.beginPath();ctx.arc(kx,ky,k.r+9,0,Math.PI*2);ctx.fillStyle=k.c;ctx.fill();
    ctx.globalAlpha=k.al;ctx.shadowBlur=8;ctx.shadowColor=k.c;
    ctx.beginPath();ctx.arc(kx,ky,k.r,0,Math.PI*2);ctx.fillStyle=k.c;ctx.fill();ctx.shadowBlur=0;
    if(k.al>.4){ctx.fillStyle='#c0e8c0';ctx.font=`${9/scale}px 'Share Tech Mono'`;ctx.fillText(k.l,kx+k.r+4,ky+3);}
    ctx.restore();
  });

  ctx.restore();
  document.getElementById('ac').textContent=active.size;
  document.getElementById('nc').textContent=AGENTS.length;
}

function applyPhysics(){
  if(!physicsOn)return;
  AGENTS.forEach(a=>{
    if(a.id==='HUB')return;
    if(dragging===a){a.vx=0;a.vy=0;return;}
    let fx=0,fy=0;
    EDGES.forEach(([i,j])=>{
      const oid=i===a.id?j:j===a.id?i:null;if(!oid)return;
      const o=AGENTS.find(x=>x.id===oid);if(!o)return;
      const dx=(o.x-a.x)*W,dy=(o.y-a.y)*H,dist=Math.hypot(dx,dy)||1;
      const rest=o.id==='HUB'?170:110;
      const f=(dist-rest)*.000016;
      fx+=dx/dist*f;fy+=dy/dist*f;
    });
    AGENTS.forEach(b=>{
      if(b===a)return;
      const dx=(a.x-b.x)*W,dy=(a.y-b.y)*H,dist=Math.hypot(dx,dy)||1;
      if(dist<140){const f=.000010*W*W/(dist*dist);fx+=dx/dist*f;fy+=dy/dist*f;}
    });
    // ดึงเข้ากึ่งกลางแบบอ่อนๆ (ลดลงจากเดิมมาก เพื่อไม่ให้ดูเหมือนลู่เข้าหากันเป็นระเบียบ)
    fx+=(0.5-a.x)*.000015*W;fy+=(0.5-a.y)*.000015*H;
    // แรงผลักกลับเมื่อเข้าใกล้ขอบจอ (กันไม่ให้ agent ไปเกาะติดขอบจนเรียงตัวเป็นรูปสี่เหลี่ยมแบนๆ)
    const _edgeM=.16;
    let _ex=0,_ey=0;
    if(a.x<_edgeM)_ex=_edgeM-a.x;else if(a.x>1-_edgeM)_ex=-(a.x-(1-_edgeM));
    if(a.y<_edgeM)_ey=_edgeM-a.y;else if(a.y>1-_edgeM)_ey=-(a.y-(1-_edgeM));
    fx+=_ex*.015*W;fy+=_ey*.015*H;
    // แรงล่องลอยแบบนุ่มนวล (smooth wander) — ใช้คลื่นไซน์ต่อเนื่องแทนค่าสุ่มรายเฟรม ให้ agent เคลื่อนไหวลื่นไหลเป็นธรรมชาติ ไม่กระตุก ไม่หยุดนิ่ง/ไม่ลู่เข้าเป็นวงเรียบ
    if(a.wPhase===undefined){a.wPhase=Math.random()*Math.PI*2;a.wPhase2=Math.random()*Math.PI*2;a.wFreqX=.0045+Math.random()*.003;a.wFreqY=.0045+Math.random()*.003;}
    fx+=Math.sin(fr*a.wFreqX+a.wPhase)*.0020*W;fy+=Math.cos(fr*a.wFreqY+a.wPhase2)*.0020*H;
    a.vx=(a.vx===undefined?0:a.vx);a.vy=(a.vy===undefined?0:a.vy);
    a.vx=(a.vx+fx/W)*.87;a.vy=(a.vy+fy/H)*.87;
    a.x=Math.max(.04,Math.min(.96,a.x+a.vx*SPEED_MULT));a.y=Math.max(.04,Math.min(.96,a.y+a.vy*SPEED_MULT));
  });
  kn.forEach(k=>{
    k.x+=k.vx*SPEED_MULT;k.y+=k.vy*SPEED_MULT;
    k.pT+=k.pSp*SPEED_MULT;if(k.pT>1)k.pT-=1;
  });
}

function tick(){
  fr++;applyPhysics();
  STARS.forEach(s=>{s.x=(s.x+s.dx*SPEED_MULT+1)%1;s.y=(s.y+s.dy*SPEED_MULT+1)%1;});
  kn.forEach(k=>{k.age++;const h=k.max/2;k.al=k.age<h?k.age/h:1-(k.age-h)/h;});
  kn=kn.filter(k=>k.age<k.max);
  pts.forEach(p=>{p.t+=p.sp*SPEED_MULT;});pts=pts.filter(p=>p.t<1);
  const knInterval=Math.max(7,Math.round(36/SPEED_MULT));
  if(fr%knInterval===0){
    const aa=[...active].filter(id=>!kn.some(k=>k.pid===id));
    const pool=aa.length?aa:[...active];
    if(pool.length)spK(pool[Math.floor(Math.random()*pool.length)]);
  }
  if(EDGES.length){
    const baseChance=.014*SPEED_MULT;
    EDGES.forEach(e=>{
      const isBias=ACTIVE_IDS.length&&(ACTIVE_SET.has(e[0])||ACTIVE_SET.has(e[1]));
      if(Math.random()<(isBias?baseChance*1.8:baseChance))spP(e[0],e[1]);
    });
  }
  if(fr%170===0){document.getElementById('lt').textContent=LOGS[logIdx%LOGS.length];logIdx++;}
  drawScene();requestAnimationFrame(tick);
}

C.addEventListener('mousedown',e=>{
  const r=C.getBoundingClientRect(),cx=(e.clientX-r.left-panX)/scale,cy=(e.clientY-r.top-panY)/scale;
  dragging=null;
  for(const a of AGENTS){if(Math.hypot(cx-a.x*W,cy-a.y*H)<hitR(a)){dragging=a;break;}}
  if(!dragging){panning=true;lastMX=e.clientX;lastMY=e.clientY;}
});
C.addEventListener('mousemove',e=>{
  const r=C.getBoundingClientRect(),cx=(e.clientX-r.left-panX)/scale,cy=(e.clientY-r.top-panY)/scale;
  if(dragging){
    dragging.x=Math.max(.02,Math.min(.98,cx/W));dragging.y=Math.max(.02,Math.min(.98,cy/H));dragging.vx=0;dragging.vy=0;
  }else if(panning){
    panX+=e.clientX-lastMX;panY+=e.clientY-lastMY;lastMX=e.clientX;lastMY=e.clientY;
  }
  hov=null;
  AGENTS.forEach(a=>{if(Math.hypot(cx-a.x*W,cy-a.y*H)<hitR(a)){hov=a;document.getElementById('ins-body').textContent=`[ ${a.id} ] ${a.name} — ${a.info}`;}});
});
C.addEventListener('mouseup',()=>{dragging=null;panning=false;});
C.addEventListener('mouseleave',()=>{dragging=null;panning=false;});
C.addEventListener('wheel',e=>{
  e.preventDefault();
  const r=C.getBoundingClientRect(),mx=e.clientX-r.left,my=e.clientY-r.top,d=e.deltaY>0?.88:1.14;
  panX=mx-(mx-panX)*d;panY=my-(my-panY)*d;scale=Math.max(.25,Math.min(5,scale*d));
},{passive:false});

function resetView(){scale=1;panX=0;panY=0;}
function zoomIn(){scale=Math.min(5,scale*1.3);}
function zoomOut(){scale=Math.max(.25,scale*.77);}
function togglePhysics(){physicsOn=!physicsOn;document.getElementById('phys-label').textContent=physicsOn?'ON':'OFF';}
tick();
</script>
"""


def render_full_graph(height=560, a26_phase="idle", a26_status="", title="AQUALINE NEURAL NETWORK", theme=None,
                       active_agents=None, active_label=""):
    """คืน HTML string ของ Knowledge Graph แบบเต็ม (physics + drag/zoom/pan + controls)
    theme: dict ปรับแต่งได้ (ดู DEFAULT_THEME) — ถ้าไม่ส่งจะใช้ค่าเริ่มต้น
    active_agents: list ของ agent id (เช่น ["A3","A8"]) ที่ "กำลังทำงานอยู่จริง" ตอนนี้ — ถ้าไม่ส่ง/ส่ง None/[]
        จะ fallback เป็นพฤติกรรมเดิมทุกอย่าง (ทุก agent ถือว่า active หมด) ไม่กระทบหน้าเดิมที่เรียกใช้อยู่
    active_label: ข้อความแบนเนอร์สีม่วงด้านบน graph (เช่น "🗣️ กำลังประชุม: แผนกครีเอทีฟ — เหลือ 3 คน")
        แสดงเฉพาะตอน active_agents ไม่ว่าง"""
    t = _merged_theme(theme)
    nodes = build_nodes(t)
    active_ids = list(active_agents) if active_agents else []
    html = (FULL_GRAPH_TEMPLATE
            .replace("__HEIGHT__", str(height))
            .replace("__NODES_JSON__", json.dumps(nodes, ensure_ascii=False))
            .replace("__EDGES_JSON__", json.dumps(EDGES, ensure_ascii=False))
            .replace("__KT_JSON__", json.dumps(_knowledge_tags(), ensure_ascii=False))
            .replace("__LOGS_JSON__", json.dumps(_logs(t.get("agent_names")), ensure_ascii=False))
            .replace("__A26_PHASE__", a26_phase)
            .replace("__A26_STATUS__", a26_status.replace('"', "'"))
            .replace("__ACTIVE_IDS_JSON__", json.dumps(active_ids, ensure_ascii=False))
            .replace("__ACTIVE_LABEL__", active_label.replace('"', "'"))
            .replace("__TITLE__", title)
            .replace("__LINE_COLOR_AGENT__", str(t["line_color_agent"]))
            .replace("__LINE_COLOR_THOUGHT__", str(t["line_color_thought"]))
            .replace("__LINE_WIDTH_AGENT__", str(t["line_width_agent"]))
            .replace("__LINE_WIDTH_THOUGHT__", str(t["line_width_thought"]))
            .replace("__SPEED_MULT__", str(t["speed_multiplier"])))
    return html


# ════════════════════════════════════════════════════════════════════
# MINI GRAPH — เวอร์ชันย่อ (เก็บไว้ใช้งานในอนาคต — ปัจจุบันทุกหน้าใช้ full graph แล้ว)
# ════════════════════════════════════════════════════════════════════
MINI_GRAPH_TEMPLATE = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Orbitron:wght@400;700&display=swap');
*{margin:0;padding:0;box-sizing:border-box}
#mini-wrap{background:#020a12;border-radius:8px;overflow:hidden;font-family:'Share Tech Mono',monospace;border:1px solid #0a2535;display:flex;flex-direction:column}
#mini-top{display:flex;align-items:stretch;gap:0}
#mini-canvas-col{flex:1;min-width:0;position:relative}
canvas#mini-kg{display:block;width:100%;height:__MHEIGHT__px}
#mini-right{width:230px;flex-shrink:0;background:#030d18;border-left:1px solid #0a2535;display:flex;flex-direction:column;padding:8px 10px;gap:4px}
.mini-title{font-size:9px;color:#0cf;letter-spacing:.15em;font-family:'Orbitron',monospace;margin-bottom:4px;flex-shrink:0}
#agent-status-list{overflow-y:auto;max-height:__MHEIGHT__px}
.agent-row{display:flex;align-items:center;gap:6px;padding:3px 0;border-bottom:1px solid #0a1828}
.agent-dot{width:7px;height:7px;border-radius:50%;flex-shrink:0}
.agent-info{flex:1;min-width:0}
.agent-id-mini{font-size:8px;font-family:'Orbitron',monospace;font-weight:700;color:#0cf}
.agent-task{font-size:8px;color:#0a7;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font-family:'Share Tech Mono',monospace}
.agent-badge{font-size:7px;padding:1px 5px;border-radius:3px;letter-spacing:.06em;flex-shrink:0;background:#031a10;color:#0f9;border:1px solid #0f9}
#mini-logbar{background:#010810;border-top:1px solid #061828;padding:4px 12px;font-size:9px;color:#0a5;font-family:'Share Tech Mono',monospace;letter-spacing:.04em;white-space:nowrap;overflow:hidden;display:flex;align-items:center;gap:8px}
.log-blink{color:#0cf;animation:blink .8s step-end infinite}
@keyframes blink{50%{opacity:0}}
</style>

<div id="mini-wrap">
  <div id="mini-top">
    <div id="mini-canvas-col"><canvas id="mini-kg"></canvas></div>
    <div id="mini-right">
      <div class="mini-title">▸ __TITLE__</div>
      <div id="agent-status-list"></div>
    </div>
  </div>
  <div id="mini-logbar">
    <span class="log-blink">▶</span>
    <span id="mini-log">[ SYS ] All systems nominal</span>
  </div>
</div>

<script>
const C=document.getElementById('mini-kg'),ctx=C.getContext('2d');
let W,H=__MHEIGHT__;
function rsz(){W=C.parentElement.offsetWidth;C.width=W;C.height=H;}
rsz();window.addEventListener('resize',rsz);

const NODES=__NODES_JSON__;
const EDGES=__EDGES_JSON__;
const LOGS=__LOGS_JSON__;

let fr=0,kn=[],pts=[],logIdx=0;

function spK(){
  const a=NODES[Math.floor(Math.random()*NODES.length)];
  const ang=Math.random()*Math.PI*2,d=.05+Math.random()*.08;
  kn.push({x:a.x+Math.cos(ang)*d,y:a.y+Math.sin(ang)*d*W/H,c:a.glow,r:2+Math.random()*1.8,al:0,age:0,max:110+Math.random()*70});
}
function spP(){
  const a=NODES[Math.floor(Math.random()*NODES.length)],b=NODES[Math.floor(Math.random()*NODES.length)];
  if(a!==b)pts.push({x:a.x,y:a.y,tx:b.x,ty:b.y,c:a.glow,t:0,sp:.03+Math.random()*.02});
}

function draw(){
  ctx.clearRect(0,0,W,H);ctx.fillStyle='#020a12';ctx.fillRect(0,0,W,H);
  ctx.strokeStyle='#071828';ctx.lineWidth=.3;
  for(let x=0;x<W;x+=26){ctx.beginPath();ctx.moveTo(x,0);ctx.lineTo(x,H);ctx.stroke();}
  for(let y=0;y<H;y+=26){ctx.beginPath();ctx.moveTo(0,y);ctx.lineTo(W,y);ctx.stroke();}

  EDGES.forEach(([a,b])=>{
    const na=NODES.find(n=>n.id===a),nb=NODES.find(n=>n.id===b);if(!na||!nb)return;
    ctx.save();ctx.globalAlpha=.18;ctx.strokeStyle='#0a3a6a';ctx.lineWidth=.6;ctx.setLineDash([3,5]);
    ctx.beginPath();ctx.moveTo(na.x*W,na.y*H);ctx.lineTo(nb.x*W,nb.y*H);ctx.stroke();ctx.setLineDash([]);ctx.restore();
  });

  kn.forEach(k=>{ctx.save();ctx.globalAlpha=k.al;ctx.shadowBlur=5;ctx.shadowColor=k.c;ctx.beginPath();ctx.arc(k.x*W,k.y*H,k.r,0,Math.PI*2);ctx.fillStyle=k.c;ctx.fill();ctx.restore();});
  pts.forEach(p=>{
    const x=p.x*W+(p.tx-p.x)*W*p.t,y=p.y*H+(p.ty-p.y)*H*p.t;
    ctx.save();ctx.globalAlpha=(1-p.t)*.8;ctx.shadowBlur=8;ctx.shadowColor=p.c;
    ctx.beginPath();ctx.arc(x,y,1.8,0,Math.PI*2);ctx.fillStyle=p.c;ctx.fill();ctx.restore();
  });

  NODES.forEach(a=>{
    const pu=.88+.12*Math.sin(fr*.08+a.x*6),rr=a.r*pu;
    ctx.save();
    ctx.globalAlpha=.07+.04*Math.sin(fr*.06);ctx.shadowBlur=14;ctx.shadowColor=a.glow;
    ctx.beginPath();ctx.arc(a.x*W,a.y*H,rr+10,0,Math.PI*2);ctx.fillStyle=a.glow;ctx.fill();ctx.shadowBlur=0;
    ctx.globalAlpha=1;ctx.shadowBlur=5;ctx.shadowColor=a.glow;
    ctx.beginPath();ctx.arc(a.x*W,a.y*H,rr,0,Math.PI*2);ctx.fillStyle=a.color;ctx.fill();
    ctx.strokeStyle=a.glow;ctx.lineWidth=.8;ctx.stroke();ctx.shadowBlur=0;
    ctx.fillStyle='#fff';ctx.font=`${Math.round(rr*1.05)}px sans-serif`;ctx.textAlign='center';ctx.textBaseline='middle';
    ctx.fillText(a.icon||a.id,a.x*W,a.y*H);
    ctx.restore();
  });
}

function buildStatusList(){
  const el=document.getElementById('agent-status-list');
  el.innerHTML=NODES.filter(n=>n.id!=='HUB').map(a=>{
    return `<div class="agent-row"><div class="agent-dot" style="background:${a.glow};box-shadow:0 0 5px ${a.glow}"></div><div class="agent-info"><div class="agent-id-mini">${a.icon} ${a.id}</div><div class="agent-task">${a.info}</div></div><span class="agent-badge">ACTIVE</span></div>`;
  }).join('');
}

function tick(){
  fr++;
  kn.forEach(k=>{k.age++;const h=k.max/2;k.al=k.age<h?k.age/h:1-(k.age-h)/h;});
  kn=kn.filter(k=>k.age<k.max);
  pts.forEach(p=>{p.t+=p.sp;});pts=pts.filter(p=>p.t<1);
  if(fr%35===0)spK();
  if(fr%55===0)spP();
  if(fr%160===0){document.getElementById('mini-log').textContent=LOGS[logIdx%LOGS.length];logIdx++;}
  draw();requestAnimationFrame(tick);
}
buildStatusList();tick();
</script>
"""


def render_mini_graph(height=150, title="AGENT STATUS — LIVE", theme=None):
    """คืน HTML string ของ Knowledge Graph แบบย่อ (เก็บไว้ใช้งานในอนาคต)"""
    t = _merged_theme(theme)
    nodes = build_nodes(t)
    html = (MINI_GRAPH_TEMPLATE
            .replace("__MHEIGHT__", str(height))
            .replace("__NODES_JSON__", json.dumps(nodes, ensure_ascii=False))
            .replace("__EDGES_JSON__", json.dumps(EDGES, ensure_ascii=False))
            .replace("__LOGS_JSON__", json.dumps(_logs(t.get("agent_names")), ensure_ascii=False))
            .replace("__TITLE__", title))
    return html

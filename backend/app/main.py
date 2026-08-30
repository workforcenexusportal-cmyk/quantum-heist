"""Quantum Heist API — FastAPI entrypoint."""

from __future__ import annotations

import json
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from .engine.models import Action, PredictionResult, TimelineSummary
from .engine.replays import ReplayMetadata, ReplayStore
from .engine.sessions import Session

app = FastAPI(title="Quantum Heist API", version="0.1.0")
SESSIONS: Dict[str, Session] = {}
REPLAYS = ReplayStore()


class CreateSessionRequest(BaseModel):
    map: str = Field(default="tunnel")


class ActionRequest(BaseModel):
    operator: str
    kind: str
    dir: Optional[str] = None


class PredictRequest(BaseModel):
    actions: List[Action] = Field(default_factory=list)
    ticks: int = Field(default=10, ge=1, le=60)


class CollapseRequest(BaseModel):
    target: str
    promote: bool = False


class ForkRequest(BaseModel):
    from_timeline: Optional[str] = None


@app.get("/play", response_class=HTMLResponse, include_in_schema=False)
def play():
    """Serve a zero-build playable client for local development."""
    return HTMLResponse(PLAY_HTML)


@app.post("/sessions")
def create_session(req: CreateSessionRequest):
    try:
        session = Session(req.map)
    except (ValueError, KeyError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    SESSIONS[session.id] = session
    return {"session_id": session.id, "map": session.map_name, "primary_timeline_id": session.tree.primary_id, "state": session.tree.primary().state}


def _get_session(session_id: str) -> Session:
    session = SESSIONS.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="session not found")
    return session


@app.get("/sessions/{session_id}")
def get_session(session_id: str):
    session = _get_session(session_id)
    node = session.tree.primary()
    return {"session_id": session.id, "primary_timeline_id": session.tree.primary_id, "state": node.state}


@app.post("/sessions/{session_id}/action")
def queue_action(session_id: str, req: ActionRequest):
    session = _get_session(session_id)
    if req.kind not in ("move", "hack", "emp"):
        raise HTTPException(status_code=400, detail="kind must be 'move', 'hack' or 'emp'")
    if req.kind == "move" and req.dir not in ("N", "S", "E", "W"):
        raise HTTPException(status_code=400, detail="move requires dir N/S/E/W")
    session.queue_action(Action(operator=req.operator, kind=req.kind, dir=req.dir))  # type: ignore[arg-type]
    return {"queued": True, "operator": req.operator}


@app.post("/sessions/{session_id}/tick")
def tick(session_id: str):
    session = _get_session(session_id)
    state = session.tick()
    if session.completed_replay is not None:
        REPLAYS.save(session.completed_replay)
    return {"session_id": session.id, "primary_timeline_id": session.tree.primary_id, "state": state}


@app.post("/sessions/{session_id}/predict", response_model=PredictionResult)
def predict_route(session_id: str, req: PredictRequest):
    session = _get_session(session_id)
    by_tick: Dict[int, List[Action]] = {}
    for i, action in enumerate(req.actions):
        by_tick.setdefault(i, []).append(action)
    return session.predict(by_tick, req.ticks)


@app.post("/sessions/{session_id}/fork")
def fork(session_id: str, req: ForkRequest):
    session = _get_session(session_id)
    new_id = session.fork(req.from_timeline)
    if new_id is None:
        raise HTTPException(status_code=409, detail="cannot fork this timeline")
    return {"forked": True, "timeline_id": new_id, "parent_id": req.from_timeline or session.tree.primary_id}


@app.post("/sessions/{session_id}/collapse")
def collapse(session_id: str, req: CollapseRequest):
    session = _get_session(session_id)
    if not session.collapse(req.target, promote=req.promote):
        raise HTTPException(status_code=409, detail="cannot collapse/promote this timeline")
    return {"collapsed": True, "target": req.target, "promoted": req.promote, "primary": session.tree.primary_id}


@app.get("/sessions/{session_id}/timelines", response_model=List[TimelineSummary])
def timelines(session_id: str):
    return _get_session(session_id).summaries()


@app.get("/sessions/{session_id}/outcome", response_model=Optional[ReplayMetadata])
def mission_outcome(session_id: str):
    session = _get_session(session_id)
    replay = session.completed_replay or (REPLAYS.by_session(session_id)[-1] if REPLAYS.by_session(session_id) else None)
    return replay


@app.get("/replays/{replay_id}", response_model=ReplayMetadata)
def replay(replay_id: str):
    item = REPLAYS.get(replay_id)
    if item is None:
        raise HTTPException(status_code=404, detail="replay not found")
    return item


@app.get("/maps")
def maps():
    from .engine.maps import MAPS
    return {"maps": sorted(MAPS.keys())}


PLAY_HTML = r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Quantum Heist // Play</title>
<style>
:root{--bg:#090d14;--panel:#111927;--line:#26344a;--text:#e8eef7;--muted:#8290a6;--cyan:#5eead4;--red:#fb7185;--gold:#fbbf24;--green:#4ade80;--purple:#c084fc}*{box-sizing:border-box}body{margin:0;background:radial-gradient(circle at 50% 0,#15243a 0,#090d14 48%);color:var(--text);font:14px ui-monospace,SFMono-Regular,Consolas,monospace;min-height:100vh}main{max-width:1050px;margin:auto;padding:28px 16px}header{display:flex;justify-content:space-between;align-items:end;gap:20px;border-bottom:1px solid var(--line);padding-bottom:18px;margin-bottom:18px}h1{font-size:30px;margin:5px 0}h2{font-size:13px;letter-spacing:.15em;color:var(--muted)}.eyebrow{color:var(--cyan);font-size:11px;letter-spacing:.28em}.layout{display:grid;grid-template-columns:1fr 330px;gap:16px}.panel{background:rgba(17,25,39,.92);border:1px solid var(--line);border-radius:8px;padding:16px}.bar{display:flex;justify-content:space-between;gap:10px;align-items:center;margin-bottom:14px}.grid{display:grid;gap:3px;width:min(100%,650px);margin:auto}.cell{aspect-ratio:1;border-radius:3px;display:grid;place-items:center;font-weight:bold;font-size:clamp(10px,2.5vw,17px);position:relative}.wall{background:#273348}.floor{background:#0d1522}.vault{background:#5b4312;border:1px solid #d99a18}.hacked{background:#166534!important;border-color:var(--green)!important}.crew{width:72%;height:72%;border-radius:5px;background:var(--cyan);color:#071014;display:grid;place-items:center;z-index:2}.guard{width:72%;height:72%;border-radius:50%;background:var(--red);color:#19070b;display:grid;place-items:center;z-index:2}.stunned{box-shadow:0 0 0 2px var(--purple),0 0 12px var(--purple)}.status{padding:8px 10px;border-radius:4px;background:#0b1320;color:var(--muted);font-size:12px}.success{color:var(--green);background:#0b241b}.danger{color:var(--red);background:#2b1018}button,select{font:inherit;color:var(--text);background:#182338;border:1px solid var(--line);border-radius:4px;padding:9px 12px;cursor:pointer}button:hover:not(:disabled){border-color:var(--cyan);background:#20324d}button:disabled{opacity:.45;cursor:not-allowed}.primary{background:var(--cyan);color:#071014;border-color:var(--cyan);font-weight:bold}.controls{display:grid;grid-template-columns:repeat(3,1fr);gap:6px;max-width:320px;margin-top:14px}.wide{grid-column:span 3}.actions{display:grid;grid-template-columns:repeat(2,1fr);gap:6px;margin-top:14px}.timeline{border-top:1px solid var(--line);padding:10px 0;font-size:12px;display:flex;justify-content:space-between;gap:6px}.timeline:first-of-type{border-top:0}.accent{color:var(--cyan)}.muted{color:var(--muted)}.legend{display:grid;grid-template-columns:1fr 1fr;gap:8px;color:var(--muted);font-size:12px;margin-top:14px}.log{max-height:150px;overflow:auto;color:var(--muted);font-size:11px;line-height:1.6;margin-top:12px;white-space:pre-wrap}@media(max-width:760px){.layout{grid-template-columns:1fr}header{align-items:start;flex-direction:column}.cell{font-size:12px}}
</style></head><body><main>
<header><div><div class="eyebrow">KESTREL COLLECTIVE // LIVE SIMULATION</div><h1>QUANTUM HEIST</h1><div class="muted">Plan. Predict. Fork. Collapse.</div></div><div><label class="muted">FACILITY </label><select id="map"><option value="tunnel">Tunnel Run</option><option value="office">Meridian Office</option></select> <button class="primary" id="new">NEW HEIST</button></div></header>
<div class="layout"><section class="panel"><div class="bar"><div>SESSION <span class="accent" id="session">—</span> · TICK <span class="accent" id="tick">—</span></div><div id="status" class="status">CONNECTING</div></div><div id="grid" class="grid"></div><div class="controls"><span></span><button data-dir="N">▲ NORTH</button><span></span><button data-dir="W">◀ WEST</button><button id="wait">WAIT</button><button data-dir="E">EAST ▶</button><span></span><button data-dir="S">▼ SOUTH</button><span></span></div><div class="actions"><button id="tickBtn">TICK / COMMIT</button><button id="hack">HACK VAULT</button><button id="emp">EMP PULSE</button><button id="predict">PREDICT 8 TICKS</button><button id="fork">FORK TIMELINE</button></div><div class="log" id="log"></div></section><aside><section class="panel"><h2>TIMELINE TREE</h2><div id="timelines" class="muted">No branches yet.</div></section><section class="panel" style="margin-top:16px"><h2>FIELD NOTES</h2><div class="legend"><span>◼ OPERATOR</span><span>● GUARD</span><span>▣ VAULT</span><span>◌ ECHO</span></div><p class="muted">Move one cell, then commit with TICK. HACK works only adjacent to the vault. EMP stuns the nearest guard in range for three ticks.</p><div id="echo"></div></section></aside></div></main>
<script>
const $=id=>document.getElementById(id);let sid=null,state=null,busy=false;const api=async(path,opts={})=>{const r=await fetch(path,{headers:{'Content-Type':'application/json'},...opts});if(!r.ok)throw Error(await r.text());return r.json()};
function log(s){$('log').textContent=(s+'\n'+$('log').textContent).slice(0,2000)}function setBusy(v){busy=v;document.querySelectorAll('button').forEach(b=>b.disabled=v)}function actor(id){return state.actors.find(a=>a.id===id)}
function draw(){if(!state)return;const g=$('grid');g.style.gridTemplateColumns=`repeat(${state.cols},1fr)`;g.innerHTML='';const by={};state.actors.forEach(a=>(by[a.pos.row+','+a.pos.col]??=[]).push(a));for(let r=0;r<state.rows;r++)for(let c=0;c<state.cols;c++){const e=document.createElement('div'),k=r+','+c;e.className='cell '+state.grid[r][c]+(state.vault_hacked&&state.grid[r][c]=='vault'?' hacked':'');(by[k]??[]).forEach(a=>{const x=document.createElement('div');x.className=a.kind+(a.stunned_until>state.tick?' stunned':'');x.textContent=a.kind=='guard'?'●':'◆';x.title=a.id;e.append(x)});g.append(e)}$('session').textContent=sid||'—';$('tick').textContent=state.tick;const st=$('status');st.textContent=state.vault_hacked?'VAULT HACKED':state.compromised?'COMPROMISED':'UNDETECTED';st.className='status '+(state.vault_hacked?'success':state.compromised?'danger':'')}
async function refresh(){const ts=await api(`/sessions/${sid}/timelines`);$('timelines').innerHTML=ts.map(t=>`<div class="timeline"><span>${t.is_primary?'★':'·'} ${t.id} <span class="muted">t=${t.tick}</span></span><span class="${t.compromised?'danger accent':t.status=='promoted'?'accent':''}">${t.status}</span></div>`).join('')}
async function run(f){if(!sid||busy)return;setBusy(true);try{await f();draw();await refresh()}catch(e){log('ERROR: '+e.message)}finally{setBusy(false)}}
async function fresh(){setBusy(true);try{const x=await api('/sessions',{method:'POST',body:JSON.stringify({map:$('map').value})});sid=x.session_id;state=x.state;$('echo').innerHTML='';$('log').textContent='';log('Insertion complete. Operator crew-1 ready.');draw();await refresh()}catch(e){log('ERROR: '+e.message)}finally{setBusy(false)}}
async function move(d){await run(async()=>{await api(`/sessions/${sid}/action`,{method:'POST',body:JSON.stringify({operator:'crew-1',kind:'move',dir:d})});log('Queued move '+d+' — commit with TICK')})}async function commit(){await run(async()=>{const x=await api(`/sessions/${sid}/tick`,{method:'POST',body:'{}'});state=x.state;log('Committed tick '+state.tick)})}async function gadget(k){await run(async()=>{await api(`/sessions/${sid}/action`,{method:'POST',body:JSON.stringify({operator:'crew-1',kind:k})});log(k.toUpperCase()+' queued — commit with TICK')})}async function predict(){await run(async()=>{const x=await api(`/sessions/${sid}/predict`,{method:'POST',body:JSON.stringify({actions:[],ticks:8})});$('echo').innerHTML=`<div class="status ${x.compromised?'danger':'success'}" style="margin-top:12px">ECHO: ${x.compromised?'COMPROMISE AT TICK '+x.compromised_at:'CLEAN FOR 8 TICKS'}<br>${x.vault_hacked?'Vault hacked':'Vault remains locked'}</div>`;log('Echo calculated through tick '+x.final_state.tick)})}async function fork(){await run(async()=>{const x=await api(`/sessions/${sid}/fork`,{method:'POST',body:'{}'});log('Forked timeline '+x.timeline_id)})}document.querySelectorAll('[data-dir]').forEach(b=>b.onclick=()=>move(b.dataset.dir));$('wait').onclick=commit;$('tickBtn').onclick=commit;$('hack').onclick=()=>gadget('hack');$('emp').onclick=()=>gadget('emp');$('predict').onclick=predict;$('fork').onclick=fork;$('new').onclick=fresh;$('map').onchange=fresh;fresh();
</script></body></html>'''

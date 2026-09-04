"""Small standard-library dashboard for live Prompt A runs."""

import argparse
import json
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


ROOT = Path(__file__).parent
STATE = {"running": False, "events": [], "exit_code": None}
LOCK = threading.Lock()

PAGE = r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Prompt A · Decision Lab</title>
<style>
:root{--paper:#f4efe5;--ink:#25231f;--muted:#756e62;--line:#d8cdbb;--amber:#b66d25;--green:#477353;--red:#a24f42;--white:#fffaf1}
*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--ink);font:15px/1.45 ui-sans-serif,system-ui,sans-serif}
main{max-width:1180px;margin:auto;padding:42px clamp(20px,5vw,70px) 70px}.eyebrow{text-transform:uppercase;letter-spacing:.16em;font-size:11px;color:var(--amber);font-weight:750}
h1{font:600 clamp(34px,5vw,58px)/.98 Georgia,serif;letter-spacing:-.04em;margin:12px 0 10px;max-width:650px}p{color:var(--muted);margin:0}.top{display:flex;justify-content:space-between;gap:30px;align-items:end;margin-bottom:36px}.actions{display:flex;gap:10px;align-items:center}
button{border:0;background:var(--ink);color:var(--white);padding:11px 17px;font-weight:700;cursor:pointer}button.secondary{background:transparent;color:var(--ink);border:1px solid var(--line)}button:disabled{opacity:.5;cursor:wait}.status{font-size:12px;color:var(--muted)}
.layout{display:grid;grid-template-columns:minmax(280px,390px) 1fr;gap:26px;align-items:start}.panel{border-top:2px solid var(--ink);padding-top:14px}.panel h2{font-size:13px;text-transform:uppercase;letter-spacing:.1em;margin:0 0 14px}.board-wrap{background:var(--white);padding:22px;border:1px solid var(--line)}.board{display:grid;grid-template-columns:repeat(5,1fr);gap:5px;aspect-ratio:1}.cell{background:#e8dfd1;position:relative;display:grid;place-items:center;color:var(--muted);font:12px Georgia,serif}.cell.path{background:#d8c6a7}.cell.current{background:var(--ink);color:var(--white)}.cell.goal{box-shadow:inset 0 0 0 3px var(--amber)}.cell.current.goal{background:var(--green)}.cell small{position:absolute;bottom:4px;right:5px;font:10px ui-sans-serif;color:inherit;opacity:.65}.legend{display:flex;gap:14px;margin-top:14px;font-size:12px;color:var(--muted)}.dot{display:inline-block;width:9px;height:9px;margin-right:5px;background:var(--ink)}.dot.goal{background:var(--amber)}.dot.path{background:#d8c6a7}
.feed{height:440px;overflow:auto;border-bottom:1px solid var(--line)}.event{display:grid;grid-template-columns:54px 1fr auto;gap:12px;border-bottom:1px solid var(--line);padding:12px 0;animation:in .35s ease-out}.event time{font:12px ui-monospace,monospace;color:var(--muted)}.event strong{font-size:14px}.event code{font:12px ui-monospace,monospace;color:var(--amber)}.event .ok{color:var(--green)}.event .bad{color:var(--red)}.empty{padding:50px 0;color:var(--muted)}
.ledger{margin-top:28px;display:grid;grid-template-columns:repeat(4,1fr);gap:10px}.run{background:var(--white);border:1px solid var(--line);padding:12px}.run b{display:block;font-size:12px}.run span{font:22px Georgia,serif}.run small{display:block;color:var(--muted);font-size:11px;margin-top:5px}.run.active{border-color:var(--amber)}
@keyframes in{from{opacity:0;transform:translateY(4px)}to{opacity:1;transform:none}}@media(max-width:800px){.top{display:block}.actions{margin-top:20px}.layout{grid-template-columns:1fr}.feed{height:320px}.ledger{grid-template-columns:repeat(2,1fr)}}@media(prefers-reduced-motion:reduce){.event{animation:none}}
</style></head><body><main>
<style>.event{animation:none}.feed pre{white-space:pre-wrap;overflow-wrap:anywhere}.actions{flex-wrap:wrap}button{white-space:nowrap}</style>
<header class="top"><div><div class="eyebrow">COS 579C · Prompt A</div><h1>Does memory help?</h1><p>A live look at the next move, the tool result, and the cost of getting there.</p></div><div class="actions"><label class="status">Provider <select id="provider"><option value="codex">Codex</option><option value="claude">Claude</option></select></label><label class="status">Condition <select id="condition"><option value="baseline">baseline</option><option value="memory">memory</option></select></label><span id="status" class="status">Ready · memory resets per run</span><button id="reset" class="secondary">Clear</button><button id="start">Start run</button></div></header>
<section class="layout"><div class="panel"><h2>Live board <span id="board-label"></span></h2><div class="board-wrap"><div id="board" class="board"></div><div class="legend"><span><i class="dot"></i>current</span><span><i class="dot path"></i>visited</span><span><i class="dot goal"></i>goal</span></div></div></div>
<div class="panel"><h2>Decision feed</h2><div id="feed" class="feed"><div class="empty">Start a run to watch the agent search.</div></div></div></section>
<section class="panel ledger"><div class="run" data-key="codex-baseline"><b>Codex · baseline</b><span>—</span><small>waiting</small></div><div class="run" data-key="codex-memory"><b>Codex · memory</b><span>—</span><small>waiting</small></div><div class="run" data-key="claude-baseline"><b>Claude · baseline</b><span>—</span><small>waiting</small></div><div class="run" data-key="claude-memory"><b>Claude · memory</b><span>—</span><small>waiting</small></div></section>
</main><script>
const $=s=>document.querySelector(s);
let snapshot='';
function render(state){
  const events=state.events;
  const latest=events[events.length-1];
  const start=events.filter(e=>e.type==='episode_start').slice(-1)[0];
  const decisions=events.filter(e=>e.type==='decision');
  const current=decisions.filter(e=>start&&e.provider===start.provider&&e.condition===start.condition&&e.episode===start.episode);
  const position=current.length?current[current.length-1].coordinate:[0,0];
  const goal=start?start.goal:null;
  $("#status").textContent=state.running?'Running · '+(latest?latest.provider+' '+latest.condition:'waiting for agent'):state.error?'Run failed':state.exit_code===0?'Complete':'Ready';
  $("#board-label").textContent=start?'· episode '+start.episode+' · goal ('+goal.join(', ')+')':'';
  const visited=new Set(['0,0',...current.map(e=>e.coordinate.join(','))]);
  document.querySelectorAll('.cell').forEach(cell=>{
    const key=cell.dataset.cell;
    cell.className='cell';
    if(visited.has(key))cell.classList.add('path');
    if(key===position.join(','))cell.classList.add('current');
    if(goal&&key===goal.join(','))cell.classList.add('goal');
    cell.firstChild.textContent=key===position.join(',')?'Agent':goal&&key===goal.join(',')?'Goal':'';
  });
  const feed=$("#feed"), scroll=feed.scrollTop;
  feed.replaceChildren();
  if(state.error){const error=document.createElement('pre');error.textContent=state.error;feed.append(error);}
  if(!decisions.length){const empty=document.createElement('p');empty.className='empty';empty.textContent=state.running?'Waiting for the first decision…':'Choose a provider and start a run.';feed.append(empty);}
  decisions.slice(-80).reverse().forEach(e=>{
    const row=document.createElement('div');row.className='event';
    const step=document.createElement('time');step.textContent='#'+e.call;
    const detail=document.createElement('div');
    const title=document.createElement('strong');title.textContent='Episode '+e.episode+' · Move '+e.tool;
    const result=document.createElement('div');result.textContent='('+e.from.join(', ')+') → ('+e.coordinate.join(', ')+')';
    const protocol=document.createElement('code');protocol.textContent=JSON.stringify({tool:e.tool})+' → goal: '+e.goal;
    detail.append(title,result,protocol);
    const outcome=document.createElement('span');outcome.className=e.goal?'ok':'';outcome.textContent=e.goal?'Goal found':'Not goal';
    row.append(step,detail,outcome);feed.append(row);
  });
  feed.scrollTop=scroll;
  document.querySelectorAll('.run').forEach(box=>{
    const episodes=events.filter(e=>e.type==='episode'&&e.provider+'-'+e.condition===box.dataset.key);
    box.querySelector('span').textContent=episodes.length?episodes.reduce((sum,e)=>sum+e.calls,0)+' moves':'—';
    box.querySelector('small').textContent=episodes.length?episodes.filter(e=>e.success).length+'/'+episodes.length+' episodes solved':'waiting';
  });
  for(const id of ['start','reset','provider','condition'])$('#'+id).disabled=state.running;
}
for(let r=0;r<5;r++)for(let c=0;c<5;c++){
  const cell=document.createElement('div');cell.className='cell';cell.dataset.cell=r+','+c;
  const label=document.createElement('span'),coordinate=document.createElement('small');
  coordinate.textContent=r+','+c;cell.append(label,coordinate);$("#board").append(cell);
}
async function poll(){
  try{
    const response=await fetch('/state');
    if(!response.ok)throw new Error('Dashboard disconnected');
    const incoming=await response.text();
    if(incoming!==snapshot){render(JSON.parse(incoming));snapshot=incoming;}
  }catch(error){$("#status").textContent='Disconnected · check dashboard terminal';}
  setTimeout(poll,400);
}
$("#start").onclick=()=>fetch('/start',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({provider:$("#provider").value,memory:$("#condition").value==='memory'})});
$("#reset").onclick=()=>fetch('/reset',{method:'POST'});
poll();
</script></body></html>'''


class Handler(BaseHTTPRequestHandler):
    def _send(self, status: int, content_type: str, body: bytes) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if self.path == "/":
            self._send(200, "text/html; charset=utf-8", PAGE.encode())
        elif self.path == "/state":
            with LOCK:
                body = json.dumps(STATE).encode()
            self._send(200, "application/json", body)
        else:
            self._send(404, "text/plain", b"not found")

    def do_POST(self) -> None:
        if self.path == "/event":
            length = int(self.headers.get("Content-Length", 0))
            event = json.loads(self.rfile.read(length))
            with LOCK:
                STATE["events"].append(event)
                STATE["running"] = True
            self._send(204, "text/plain", b"")
        elif self.path == "/start":
            length = int(self.headers.get("Content-Length", 0))
            options = json.loads(self.rfile.read(length) or b"{}")
            provider = options.get("provider", "codex")
            memory = bool(options.get("memory", False))
            if provider not in {"codex", "claude"}:
                self._send(400, "text/plain", b"unknown provider")
                return
            with LOCK:
                if STATE["running"]:
                    self._send(409, "text/plain", b"already running")
                    return
                STATE.update({"running": True, "events": [], "exit_code": None, "error": None})
            port = self.server.server_address[1]
            thread = threading.Thread(target=run_one, args=(port, provider, memory), daemon=True)
            thread.start()
            self._send(202, "text/plain", b"started")
        elif self.path == "/reset":
            with LOCK:
                if STATE["running"]:
                    self._send(409, "text/plain", b"already running")
                    return
                STATE.update({"running": False, "events": [], "exit_code": None, "error": None})
            self._send(204, "text/plain", b"")
        else:
            self._send(404, "text/plain", b"not found")

    def log_message(self, *_args: object) -> None:
        pass


def run_one(port: int, provider: str, memory: bool) -> None:
    condition = "memory" if memory else "baseline"
    command = [
        sys.executable, str(ROOT / "run_experiment.py"), provider,
        "--dashboard-url", f"http://127.0.0.1:{port}",
        "--output", str(ROOT / "results" / f"{provider}-{condition}.json"),
    ]
    if memory:
        command.append("--memory")
    result = subprocess.run(
        command,
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    with LOCK:
        STATE["running"] = False
        STATE["exit_code"] = result.returncode
        STATE["provider"] = provider
        STATE["condition"] = condition
        STATE["error"] = result.stderr.strip() or result.stdout.strip() if result.returncode else None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    print(f"Dashboard: http://{args.host}:{args.port}", flush=True)
    ThreadingHTTPServer((args.host, args.port), Handler).serve_forever()


if __name__ == "__main__":
    main()

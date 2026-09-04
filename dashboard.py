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
<header class="top"><div><div class="eyebrow">COS 579C · Prompt A</div><h1>Does memory help?</h1><p>A live look at the next move, the tool result, and the cost of getting there.</p></div><div class="actions"><span id="status" class="status">Ready · memory resets per run</span><button id="reset" class="secondary">Clear</button><button id="start">Start run</button></div></header>
<section class="layout"><div class="panel"><h2>Live board <span id="board-label"></span></h2><div class="board-wrap"><div id="board" class="board"></div><div class="legend"><span><i class="dot"></i>current</span><span><i class="dot path"></i>visited</span><span><i class="dot goal"></i>goal</span></div></div></div>
<div class="panel"><h2>Decision feed</h2><div id="feed" class="feed"><div class="empty">Start a run to watch the agent search.</div></div></div></section>
<section class="panel ledger"><div class="run" data-key="codex-baseline"><b>Codex · baseline</b><span>—</span><small>waiting</small></div><div class="run" data-key="codex-memory"><b>Codex · memory</b><span>—</span><small>waiting</small></div><div class="run" data-key="claude-baseline"><b>Claude · baseline</b><span>—</span><small>waiting</small></div><div class="run" data-key="claude-memory"><b>Claude · memory</b><span>—</span><small>waiting</small></div></section>
</main><script>
const $=s=>document.querySelector(s), state={events:[]};
function cell(r,c){return $("[data-cell='"+r+"-"+c+"']")}
function draw(e){const b=$("#board");b.innerHTML="";for(let r=0;r<5;r++)for(let c=0;c<5;c++){const x=document.createElement("div");x.className="cell";x.dataset.cell=r+"-"+c;x.innerHTML=`<small>${r},${c}</small>`;b.append(x)};const paths=e.filter(x=>x.type==='decision'&&x.provider===state.provider&&x.condition===state.condition&&x.episode===state.episode);paths.forEach(x=>cell(...x.coordinate).classList.add('path'));if(state.goal){cell(...state.goal).classList.add('goal')}if(state.position)cell(...state.position).classList.add('current');$("#board-label").textContent=state.episode?`· ${state.provider} ${state.condition} · episode ${state.episode}`:""}
function render(){const e=state.events;$("#status").textContent=state.running?`Running · ${state.provider||''} ${state.condition||''}`:(state.exit_code===0?"Complete · memory reset next run":"Ready · memory resets per run");const feed=$("#feed");feed.innerHTML="";const decisions=e.filter(x=>x.type==='decision').slice(-80).reverse();if(!decisions.length)feed.innerHTML='<div class="empty">Start a run to watch the agent search.</div>';decisions.forEach(x=>{const row=document.createElement('div');row.className='event';row.innerHTML=`<time>#${x.call}</time><div><strong>${x.provider} · ${x.condition}</strong><br><span>episode ${x.episode} · <code>${x.tool}</code> → (${x.coordinate.join(', ')})</span></div><span class="${x.goal?'ok':''}">${x.goal?'goal':'—'}</span>`;feed.append(row)});const last=decisions[0];if(last){Object.assign(state,{provider:last.provider,condition:last.condition,episode:last.episode,position:last.coordinate,goal:last.goal?last.coordinate:null});draw(e)};e.filter(x=>x.type==='episode').forEach(x=>{const box=$(`[data-key='${x.provider}-${x.condition}']`);if(box){box.className='run';box.querySelector('span').textContent=x.calls;box.querySelector('small').textContent=x.success?'goal found':'not found'}});$("#start").disabled=state.running;$("#reset").disabled=state.running}
async function poll(){const incoming=await fetch('/state').then(r=>r.json());Object.assign(state,incoming);render();setTimeout(poll,400)}$("#start").onclick=()=>fetch('/start',{method:'POST'});$("#reset").onclick=()=>fetch('/reset',{method:'POST'});poll();
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
            with LOCK:
                if STATE["running"]:
                    self._send(409, "text/plain", b"already running")
                    return
                STATE.update({"running": True, "events": [], "exit_code": None})
            port = self.server.server_address[1]
            thread = threading.Thread(target=run_all, args=(port,), daemon=True)
            thread.start()
            self._send(202, "text/plain", b"started")
        elif self.path == "/reset":
            with LOCK:
                if STATE["running"]:
                    self._send(409, "text/plain", b"already running")
                    return
                STATE.update({"running": False, "events": [], "exit_code": None})
            self._send(204, "text/plain", b"")
        else:
            self._send(404, "text/plain", b"not found")

    def log_message(self, *_args: object) -> None:
        pass


def run_all(port: int) -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "run_all.py"), "--dashboard-url", f"http://127.0.0.1:{port}"],
        cwd=ROOT,
    )
    with LOCK:
        STATE["running"] = False
        STATE["exit_code"] = result.returncode


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    print(f"Dashboard: http://{args.host}:{args.port}", flush=True)
    ThreadingHTTPServer((args.host, args.port), Handler).serve_forever()


if __name__ == "__main__":
    main()

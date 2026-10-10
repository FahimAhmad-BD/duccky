"""
DucckyBridge: a Fusion add-in that lets Claude Code drive Fusion through a folder.

A job is a Python file dropped into <bridge>/inbox. The add-in runs it on Fusion's
main thread and writes <bridge>/outbox/<job>.json with the printed output, the
error traceback if any, and the paths of any viewport images the job saved.
Finished jobs move to <bridge>/done so every run is kept for review.

Names available inside a job:
    adsk, app, ui      the Fusion API modules and the application objects
    design()           the active Fusion design (adsk.fusion.Design)
    snapshot(name)     fit the view and save a PNG of the viewport, returns its path
    state              a dict that persists between jobs until Fusion restarts

The bridge folder is %USERPROFILE%/Documents/ClaudeFusion/bridge. No network port
is opened; only processes on this computer can reach the inbox.
"""

import adsk.core
import adsk.fusion
import contextlib
import glob
import io
import json
import os
import threading
import time
import traceback

BRIDGE = os.path.join(os.path.expanduser("~"), "Documents", "ClaudeFusion", "bridge")
INBOX = os.path.join(BRIDGE, "inbox")
OUTBOX = os.path.join(BRIDGE, "outbox")
DONE = os.path.join(BRIDGE, "done")
STATUS = os.path.join(BRIDGE, "status.json")
EVENT_ID = "DucckyBridgeJob"
POLL_S = 0.5
HEARTBEAT_S = 5.0

app = None
ui = None
_event = None
_handlers = []
_stop = threading.Event()
_pending = set()
_state = {}


def _write_json(path, data):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    os.replace(tmp, path)


def _design():
    return adsk.fusion.Design.cast(app.activeProduct)


def _run_job(path):
    job = os.path.splitext(os.path.basename(path))[0]
    result = {"job": job, "ok": False, "stdout": "", "error": None, "images": [],
              "started": time.strftime("%Y-%m-%d %H:%M:%S"), "seconds": 0.0}

    def snapshot(name="view", width=1600, height=1000, fit=True):
        vp = app.activeViewport
        if fit:
            vp.fit()
        img = os.path.join(OUTBOX, f"{job}_{name}.png")
        vp.saveAsImageFile(img, width, height)
        result["images"].append(img)
        return img

    buf = io.StringIO()
    t0 = time.time()
    try:
        with open(path, encoding="utf-8") as f:
            code = f.read()
        namespace = {"__name__": "__bridge_job__", "adsk": adsk, "app": app, "ui": ui,
                     "design": _design, "snapshot": snapshot, "state": _state}
        with contextlib.redirect_stdout(buf):
            exec(compile(code, path, "exec"), namespace)
        result["ok"] = True
    except Exception:
        result["error"] = traceback.format_exc()
    finally:
        result["stdout"] = buf.getvalue()
        result["seconds"] = round(time.time() - t0, 3)
        try:
            os.replace(path, os.path.join(DONE, os.path.basename(path)))
        except OSError:
            pass
        _write_json(os.path.join(OUTBOX, job + ".json"), result)
        _pending.discard(path)


class _JobHandler(adsk.core.CustomEventHandler):
    def notify(self, args):
        _run_job(args.additionalInfo)


def _poll():
    last_beat = 0.0
    while not _stop.wait(POLL_S):
        now = time.time()
        if now - last_beat >= HEARTBEAT_S:
            last_beat = now
            try:
                _write_json(STATUS, {"alive": True, "time": now,
                                     "local": time.strftime("%Y-%m-%d %H:%M:%S")})
            except OSError:
                pass
        for path in sorted(glob.glob(os.path.join(INBOX, "*.py"))):
            if path not in _pending:
                _pending.add(path)
                app.fireCustomEvent(EVENT_ID, path)


def run(context):
    global app, ui, _event
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        for d in (INBOX, OUTBOX, DONE):
            os.makedirs(d, exist_ok=True)
        _event = app.registerCustomEvent(EVENT_ID)
        handler = _JobHandler()
        _event.add(handler)
        _handlers.append(handler)
        _stop.clear()
        threading.Thread(target=_poll, daemon=True).start()
    except Exception:
        if ui:
            ui.messageBox("DucckyBridge failed to start:\n" + traceback.format_exc())


def stop(context):
    _stop.set()
    try:
        if _event:
            for h in _handlers:
                _event.remove(h)
        app.unregisterCustomEvent(EVENT_ID)
        _write_json(STATUS, {"alive": False, "time": time.time(),
                             "local": time.strftime("%Y-%m-%d %H:%M:%S")})
    except Exception:
        pass
    _handlers.clear()

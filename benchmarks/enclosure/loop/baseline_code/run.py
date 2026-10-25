"""Resumable benchmark runner for cad_agent.py.

Runs every (request, seed) of one condition, ONE AT A TIME: there is a single
local model server, and two agents sharing it would slow each other down and
make the timings meaningless. A machine-wide lock file enforces this across
processes too.

Layout of the output directory:

    DIR/results.jsonl                    one JSON line per finished run
    DIR/<condition>/<id>/seed<k>/        the agent's --out (it adds a timestamp folder)
    DIR/<condition>/<id>/seed<k>/run.log the agent's stdout and stderr

A run that is already in results.jsonl is skipped, so an interrupted benchmark
is resumed by running the same command again. A run that was interrupted before
it was recorded is started over from an empty folder, so a folder never mixes
two attempts.

Statuses: "verified" (exported, every component passed its checks),
"unsatisfied" (exported, but some component's checks still fail - NOT a pass),
"failed", "crashed", "timeout", "aborted", "interrupted", "usage_error" (the agent rejected its
command line, exit code 2), or "rc<N>" for anything else.

Example:

    venv/bin/python benchmarks/run.py --requests benchmarks/dev.json --condition baseline \\
        --seeds 0 1 2 --with-l1 --out runs/dev
"""

import argparse
import contextlib
import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, Iterator, List, Optional, Sequence, Set, Tuple

REPO = Path(__file__).resolve().parent.parent
AGENT = REPO / "cad_agent.py"
TIMEOUT = 200 * 60           # seconds per run
LOCK = Path(tempfile.gettempdir()) / "cad_agent_benchmark.lock"
# cad_agent's exit codes (cad_agent.EXIT_*). 2 is argparse's usage error (bad --l1,
# --mode cascade without --l1, ...), raised before any design exists: an invocation
# error, never a design that failed its requirements.
STATUS_BY_RC = {0: "verified", 1: "failed", 2: "usage_error", 3: "unsatisfied", 130: "interrupted"}


@dataclass
class RunSpec:
    """One agent run: which request, which seed, under which condition, and where it writes."""
    condition: str
    id: str
    seed: int
    request: str
    l1: Optional[List[dict]]
    mode: str
    workdir: Path
    agent_args: Tuple[str, ...] = ()   # extra cad_agent.py options (e.g. --judges ...)

    def key(self) -> Tuple[str, str, int]:
        return (self.condition, self.id, self.seed)


@dataclass
class RunResult:
    rc: Optional[int]        # None when the run timed out
    secs: float


# A runner executes one RunSpec and returns its exit code and duration. The real
# one starts cad_agent.py; tests pass a fake.
Runner = Callable[[RunSpec], RunResult]


def load_requests(path: Path) -> List[dict]:
    """The "requests" list of a benchmark file (dev.json / heldout.json shape), or a bare list."""
    data = json.loads(Path(path).read_text())
    requests = data["requests"] if isinstance(data, dict) else data
    ids = [r["id"] for r in requests]
    if len(ids) != len(set(ids)):
        raise ValueError(f"{path}: duplicate request ids")
    return requests


def recorded_runs(results: Path) -> Set[Tuple[str, str, int]]:
    """(condition, id, seed) of every run already in results.jsonl; a torn last line is ignored."""
    done: Set[Tuple[str, str, int]] = set()
    if not results.exists():
        return done
    for line in results.read_text().splitlines():
        try:
            r = json.loads(line)
            done.add((r["condition"], r["id"], int(r["seed"])))
        except (json.JSONDecodeError, KeyError, TypeError, ValueError):
            continue
    return done


def plan_runs(requests: Sequence[dict], condition: str, seeds: Sequence[int], out: Path,
              ids: Optional[Sequence[str]] = None, with_l1: bool = True,
              mode: str = "default", agent_args: Sequence[str] = ()) -> List[RunSpec]:
    """Every run of the condition, request-major (all seeds of one request, then the next)."""
    by_id = {r["id"]: r for r in requests}
    unknown = [i for i in (ids or []) if i not in by_id]
    if unknown:
        raise ValueError(f"unknown request ids: {', '.join(unknown)}")
    chosen = [by_id[i] for i in ids] if ids else list(requests)
    if mode == "cascade":  # the cascade controls to the L1s; without them every run is a usage error
        if not with_l1:
            raise ValueError("mode 'cascade' needs the L1 requirements (do not pass --no-l1)")
        missing = [r["id"] for r in chosen if not r.get("l1")]
        if missing:
            raise ValueError(f"mode 'cascade' needs L1 requirements; none for: {', '.join(missing)}")
    return [RunSpec(condition, r["id"], seed, r["request"], r.get("l1") if with_l1 else None, mode,
                    out / condition / r["id"] / f"seed{seed}", tuple(agent_args))
            for r in chosen for seed in seeds]


def agent_command(spec: RunSpec, python: str = sys.executable, agent: Path = AGENT) -> List[str]:
    """The cad_agent.py command line for one run (always --auto: nobody is there to answer)."""
    cmd = [python, str(agent), "--auto", "--out", str(spec.workdir), "--seed", str(spec.seed)]
    if spec.l1:
        cmd += ["--l1", json.dumps(spec.l1)]
    if spec.mode != "default":  # passed through only when asked, so the default CLI stays untouched
        cmd += ["--mode", spec.mode]
    return cmd + list(spec.agent_args) + [spec.request]


def subprocess_runner(timeout: float = TIMEOUT, python: str = sys.executable) -> Runner:
    """The real runner: cad_agent.py in a subprocess, output to run.log, killed after `timeout`."""
    def run(spec: RunSpec) -> RunResult:
        start = time.monotonic()
        with open(spec.workdir / "run.log", "w") as log:
            try:
                proc = subprocess.run(agent_command(spec, python), stdout=log, stderr=subprocess.STDOUT,
                                      cwd=REPO, timeout=timeout,
                                      env=dict(os.environ, PYTHONUNBUFFERED="1"))  # run.log fills live
                rc: Optional[int] = proc.returncode
            except subprocess.TimeoutExpired:
                log.write(f"\n[run.py] killed after {timeout:.0f} s\n")
                rc = None
        return RunResult(rc, time.monotonic() - start)
    return run


def design_record(workdir: Path) -> Optional[dict]:
    """The newest design.json the agent wrote under its --out folder, if any."""
    found = sorted(workdir.glob("*/design.json"))
    if not found:
        return None
    try:
        return json.loads(found[-1].read_text())
    except (json.JSONDecodeError, OSError):
        return None


def run_status(result: RunResult, record: Optional[dict]) -> str:
    """One word per run. The agent's own outcome wins over the exit code when it wrote one."""
    if result.rc is None:
        return "timeout"
    if record and record.get("outcome"):
        return record["outcome"]
    return STATUS_BY_RC.get(result.rc, f"rc{result.rc}")


@contextlib.contextmanager
def exclusive(lock_path: Optional[Path]) -> Iterator[None]:
    """Refuse to start while another benchmark holds the lock (one model server, one run)."""
    if lock_path is None:
        yield
        return
    import fcntl
    with open(lock_path, "w") as f:
        try:
            fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise SystemExit(f"another benchmark is running (lock {lock_path}); runs must be serial")
        f.write(str(os.getpid()))
        f.flush()
        yield


def run_benchmark(specs: Sequence[RunSpec], results: Path, runner: Runner,
                  log: Callable[[str], None] = print) -> List[dict]:
    """Run every spec not yet recorded, serially, appending one line per run. Returns the new lines."""
    done = recorded_runs(results)
    todo = [s for s in specs if s.key() not in done]
    log(f"{len(specs) - len(todo)} of {len(specs)} runs already recorded; {len(todo)} to go")
    new: List[dict] = []
    for n, spec in enumerate(todo, 1):
        if spec.workdir.exists():
            shutil.rmtree(spec.workdir)  # an unrecorded attempt: start clean
        spec.workdir.mkdir(parents=True)
        log(f"[{n}/{len(todo)}] {spec.condition} {spec.id} seed {spec.seed} ...")
        result = runner(spec)
        record = design_record(spec.workdir)
        line = {"condition": spec.condition, "id": spec.id, "seed": spec.seed, "rc": result.rc,
                "secs": round(result.secs, 1), "workdir": str(spec.workdir),
                "status": run_status(result, record), "mode": spec.mode, "with_l1": bool(spec.l1),
                "agent_args": list(spec.agent_args)}
        if record:
            line["verification"] = record.get("verification")
        results.parent.mkdir(parents=True, exist_ok=True)
        torn = results.exists() and results.stat().st_size > 0 and not results.read_bytes().endswith(b"\n")
        with open(results, "a") as f:
            # A run killed mid-write leaves a torn last line; never glue a new record onto it.
            f.write(("\n" if torn else "") + json.dumps(line) + "\n")
            f.flush()
            os.fsync(f.fileno())
        new.append(line)
        log(f"    -> {line['status']} (rc={result.rc}, {line['secs']} s)")
    return new


def summarize(lines: Sequence[dict]) -> Dict[str, int]:
    out: Dict[str, int] = {}
    for line in lines:
        out[line["status"]] = out.get(line["status"], 0) + 1
    return out


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run cad_agent.py over a benchmark file, serially and resumably.")
    parser.add_argument("--requests", type=Path, required=True, help="benchmark JSON (e.g. benchmarks/dev.json)")
    parser.add_argument("--ids", nargs="*", default=None, help="only these request ids")
    parser.add_argument("--condition", required=True, help="name of this experimental condition")
    parser.add_argument("--seeds", type=int, nargs="+", default=[0])
    # BooleanOptionalAction would spell the negation --no-with-l1; the documented flag is --no-l1.
    parser.add_argument("--with-l1", dest="with_l1", action="store_true", default=True,
                        help="pass the request's L1 requirements to the agent (the default)")
    parser.add_argument("--no-l1", dest="with_l1", action="store_false",
                        help="withhold the L1 requirements from the agent")
    parser.add_argument("--mode", default="default", choices=["default", "cascade"],
                        help="agent mode, passed through as --mode when not 'default'")
    parser.add_argument("--agent-args", default="",
                        help='extra cad_agent.py options for every run, e.g. "--judges qwen3.5:9b,gemma4:latest"')
    parser.add_argument("--out", type=Path, required=True, help="output directory")
    parser.add_argument("--timeout", type=float, default=TIMEOUT, help="seconds per run (default 200 min)")
    args = parser.parse_args(argv)

    try:
        specs = plan_runs(load_requests(args.requests), args.condition, args.seeds, args.out.resolve(),
                          ids=args.ids, with_l1=args.with_l1, mode=args.mode,
                          agent_args=shlex.split(args.agent_args))
    except ValueError as e:
        parser.error(str(e))
    results = args.out.resolve() / "results.jsonl"
    with exclusive(LOCK):
        new = run_benchmark(specs, results, subprocess_runner(args.timeout))
    print(f"done: {summarize(new)}; results in {results}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

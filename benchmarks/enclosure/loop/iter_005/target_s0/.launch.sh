cd /Users/robinonsay/python/llm-bt
start=$(date +%s)
/Users/robinonsay/python/llm-bt/venv/bin/python -c '
import os, signal, subprocess, sys
p = subprocess.Popen(sys.argv[2:], start_new_session=True)
try:
    sys.exit(p.wait(timeout=float(sys.argv[1])))
except subprocess.TimeoutExpired:
    os.killpg(p.pid, signal.SIGTERM)
    try: p.wait(timeout=30)
    except subprocess.TimeoutExpired: os.killpg(p.pid, signal.SIGKILL)
    print("[RUN.md] killed after", sys.argv[1], "s", flush=True)
    sys.exit(124)
' 5400 /Users/robinonsay/python/llm-bt/venv/bin/python /Users/robinonsay/python/llm-bt/cad_agent.py --mode assembly --auto --seed 0 --num-ctx 8192 --parts /Users/robinonsay/python/llm-bt/benchmarks/enclosure/parts --rules /Users/robinonsay/python/llm-bt/design_rules.json --l1 /Users/robinonsay/python/llm-bt/benchmarks/enclosure/loop/iter_005/inputs/E1-01.l1.json --out /Users/robinonsay/python/llm-bt/benchmarks/enclosure/loop/iter_005/target_s0 "$(cat /Users/robinonsay/python/llm-bt/benchmarks/enclosure/loop/iter_005/inputs/E1-01.request.txt)"
rc=$?
echo "$rc $(( $(date +%s) - start ))" > /Users/robinonsay/python/llm-bt/benchmarks/enclosure/loop/iter_005/target_s0/.rc

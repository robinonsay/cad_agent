#!/bin/bash
# Dev pilot 2: cascade with ornith alone (C) vs cascade with a 3-model judge panel (P).
# Seeds alternate between conditions so a partial run is still balanced.
cd /Users/robinonsay/python/llm-bt
OUT=/private/tmp/claude-501/-Users-robinonsay-python-llm-bt/7d706733-5c1d-44fb-a74b-bc29203e1df6/scratchpad/pilot2
JUDGES="ornith-1.5:9b,qwen3.5:9b,gemma4:latest"
for s in 0 1 2 3 4; do
  venv/bin/python benchmarks/run.py --requests benchmarks/dev.json --mode cascade --condition C_cascade \
      --seeds $s --out $OUT --agent-args "--num-ctx 8192"
  venv/bin/python benchmarks/run.py --requests benchmarks/dev.json --mode cascade --condition P_panel \
      --seeds $s --out $OUT --agent-args "--num-ctx 8192 --judges $JUDGES"
done
echo PILOTDONE

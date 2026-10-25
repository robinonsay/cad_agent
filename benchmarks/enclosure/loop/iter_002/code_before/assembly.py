"""--mode assembly: the enclosure-designing agent (ARCHITECTURE.md sections 2-4).

The target tree (ARCHITECTURE.md section 4) is built one milestone at a time.
Iteration 001 (milestone M0) wires the CLI and the blackboard and loads the
data the later stages need:

    cad_assembly (Sequence)
    ├── LoadCatalog          parts.Catalog.load + validation gate; a failing part is dropped and noted
    ├── LoadRules            design_rules.json (generic FDM / fastener rules, each with a source)
    └── NotImplementedStage  "not implemented: parse_spec" -> FAILURE (design.json records the stage)

The local LLM is the controller for discrete choices and Python is the plant
model and the sensor; nothing here holds a number, part or face that is
specific to one request (test_no_hardcoding.py scans this module).
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import py_trees
from py_trees.common import Status

import cad_checks as cc
import feature_graph as fg
import parts as pt

ca = cc._ca()  # cad_agent (the running script's module when cad_agent.py is __main__)


@dataclass
class AssemblyState:
    """The blackboard of assembly mode (ARCHITECTURE.md section 3). Stages fill it in order."""
    spec: Dict[str, Any] = field(default_factory=dict)        # request numbers with provenance + rules defaults
    contents: List[dict] = field(default_factory=list)        # what goes inside, resolved against the catalogue
    frame: Dict[str, Any] = field(default_factory=dict)       # enclosure frame (section 3.4)
    layout: Dict[str, Any] = field(default_factory=dict)      # declared pose of every reference part
    graph: Optional[fg.FeatureGraph] = None                   # reference / body / add / cut / envelope nodes
    choices: Dict[str, str] = field(default_factory=dict)     # discrete decisions + who made them
    checks: List[Any] = field(default_factory=list)           # frozen check set
    results: List[Any] = field(default_factory=list)          # latest measurement
    reports: List[Any] = field(default_factory=list)          # loop endings
    assumptions: List[str] = field(default_factory=list)      # estimates and rules defaults used
    history: List[dict] = field(default_factory=list)         # accepted moves with error keys
    catalog: Optional[pt.Catalog] = None
    rules: Optional[pt.Rules] = None
    stage: str = ""                                           # the stage reached (or the one not implemented)
    notes: List[str] = field(default_factory=list)
    parts_dir: Optional[str] = None
    rules_path: Optional[str] = None
    with_models: bool = False

    def summary(self) -> dict:
        return {
            "stage": self.stage,
            "notes": list(self.notes),
            "parts_dir": self.parts_dir,
            "rules_path": self.rules_path,
            "with_models": self.with_models,
            "catalog": self.catalog.ids() if self.catalog else [],
            "catalog_errors": list(self.catalog.errors) if self.catalog else [],
            "rules": dict(self.rules.values) if self.rules else {},
            "spec": dict(self.spec),
            "contents": list(self.contents),
            "layout": dict(self.layout),
            "choices": dict(self.choices),
            "assumptions": list(self.assumptions),
            "deferred_gate_rules": dict(pt.DEFERRED_RULES),
            "feature_graph": self.graph.to_json() if self.graph is not None else None,
        }


class AssemblyStep(ca.Step):
    def __init__(self, name: str, design):
        super().__init__(name, design)

    @property
    def state(self) -> AssemblyState:
        return self.design.assy


class LoadCatalog(AssemblyStep):
    """Load the parts catalogue and run the import gate on every part; drop and note any failure."""

    def __init__(self, design):
        super().__init__("LoadCatalog", design)

    def update(self) -> Status:
        st = self.state
        st.stage = "load_catalog"
        cat = pt.Catalog.load(st.parts_dir)
        for err in cat.errors:
            st.notes.append(f"catalogue: {err}")
        for pid in cat.ids():
            part = cat.get(pid)
            try:
                fails = pt.validate(pt.instantiate(part, part.gate_params()))
            except (pt.PartError, fg.ExprError, fg.MissingRefError, KeyError, ValueError) as e:
                fails = [pt.GateFailure(pid, "load", str(e))]
            if fails:
                cat.drop(pid, "; ".join(f"{f.rule}: {f.detail}" for f in fails))
                st.notes.append(f"catalogue: {pid} failed the import gate and is not used: "
                                + "; ".join(str(f) for f in fails))
        for problem in cat.cross_references():
            st.notes.append(f"catalogue: {problem}")
        st.catalog = cat
        if not cat.parts:
            st.notes.append(f"catalogue: no usable parts in {st.parts_dir}")
            self.feedback_message = "no usable parts"
            return Status.FAILURE
        self.logger.info(f"catalogue: {len(cat.parts)} parts ({', '.join(cat.ids())})")
        return Status.SUCCESS


class LoadRules(AssemblyStep):
    """Load design_rules.json (generic FDM / fastener values, each with a source)."""

    def __init__(self, design):
        super().__init__("LoadRules", design)

    def update(self) -> Status:
        st = self.state
        st.stage = "load_rules"
        try:
            st.rules = pt.load_rules(st.rules_path)
        except (OSError, ValueError) as e:
            st.notes.append(f"rules: cannot load {st.rules_path}: {e}")
            return Status.FAILURE
        self.logger.info(f"rules: {len(st.rules.values)} values from {st.rules_path}")
        return Status.SUCCESS


class NotImplementedStage(AssemblyStep):
    """A stage of the target tree that does not exist yet: a typed, visible FAILURE (never a fake pass)."""

    def __init__(self, design, stage: str):
        super().__init__(f"NotImplemented:{stage}", design)
        self.stage = stage

    def update(self) -> Status:
        self.state.stage = self.stage
        msg = f"not implemented: {self.stage}"
        self.state.notes.append(msg)
        self.logger.info(msg)
        print(msg, flush=True)
        return Status.FAILURE


def build_assembly_tree(design, llm, parts_dir, rules_path, with_models: bool = False,
                        auto_approve: bool = False) -> py_trees.behaviour.Behaviour:
    """The assembly-mode tree. `llm` is the controller for later stages (unused by M0's stages)."""
    if design.assy is None:
        design.assy = AssemblyState(parts_dir=str(parts_dir), rules_path=str(rules_path),
                                    with_models=bool(with_models))
    return py_trees.composites.Sequence("cad_assembly", memory=True, children=[
        LoadCatalog(design), LoadRules(design), NotImplementedStage(design, "parse_spec")])


def finalize(design, llm) -> dict:
    """Outcome record of a finished assembly run (milestone M13). Unreachable until then."""
    raise NotImplementedError("assembly finalize arrives with milestone M13")

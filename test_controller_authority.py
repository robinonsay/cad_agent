"""The controller's authority (owner decision D1, migration delta R01): every rule:* decision in the agent code is
registered in controller_rules.json with its class, and no semantic rule (one that reads the text and picks a meaning)
is active unless it is pending migration with a delta id from loop/ARCHITECTURE.md section 10.8.

The scan reads the agent modules' AST: string literals and f-strings (a formatted module-level string constant is
resolved, any other formatted value is a placeholder), never docstrings or comments. A name is "rule:" + identifier +
an optional literal [qualifier]; it ends at the first other character, the same canonical form controller.py uses at
run time for the authority audit.
"""

import ast
import json
import re
import unittest
from pathlib import Path
from typing import Dict, List, Set, Tuple

REPO = Path(__file__).parent
REGISTRY = REPO / "controller_rules.json"
ARCHITECTURE = REPO / "benchmarks" / "generalize" / "loop" / "ARCHITECTURE.md"
MODULES = ("assembly.py", "assembly_checks.py", "feature_graph.py", "layout.py", "parts.py", "controller.py",
           "cad_agent.py", "menus.py",     # changed in migration delta R02: menus.py (the shared menu plumbing) is scanned
           "building_blocks.py")   # changed in migration delta R11 (building blocks): building_blocks.py is agent code
RULE_RE = re.compile(r"rule:([A-Za-z_][A-Za-z0-9_]*)(\[[A-Za-z0-9_]+\])?")
CLASSES = {"sensor", "actuator", "controller-information", "guardrail", "plant", "semantic-rule"}
STATUSES = {"active", "pending_migration", "retired"}
DELTA_RE = re.compile(r"^R\d{2}$")


def _docstring_nodes(tree: ast.AST) -> Set[int]:
    out = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            for st in node.body:
                if isinstance(st, ast.Expr) and isinstance(st.value, ast.Constant) and isinstance(st.value.value, str):
                    out.add(id(st.value))
    return out


def _module_constants(tree: ast.Module) -> Dict[str, str]:
    out = {}
    for st in tree.body:
        if isinstance(st, ast.Assign) and isinstance(st.value, ast.Constant) and isinstance(st.value.value, str):
            for t in st.targets:
                if isinstance(t, ast.Name):
                    out[t.id] = st.value.value
    return out


def scan_rules(source: str, filename: str = "<source>") -> List[Tuple[str, str, str, int]]:
    """Every rule decision name in a module: (name, file, enclosing function or class, line)."""
    tree = ast.parse(source, filename)
    skip = _docstring_nodes(tree)
    for node in ast.walk(tree):
        if isinstance(node, ast.JoinedStr):              # an f-string's parts are read through the f-string itself
            skip |= {id(v) for v in node.values}
    consts = _module_constants(tree)
    owner: Dict[int, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            for sub in ast.walk(node):
                owner.setdefault(id(sub), node.name)
    found = []
    for node in ast.walk(tree):
        text = None
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in skip:
            text = node.value
        elif isinstance(node, ast.JoinedStr):
            parts = []
            for v in node.values:
                if isinstance(v, ast.Constant):
                    parts.append(str(v.value))
                elif isinstance(v, ast.FormattedValue) and isinstance(v.value, ast.Name) and v.value.id in consts:
                    parts.append(consts[v.value.id])
                else:
                    parts.append("{}")
            text = "".join(parts)
        if not text or "rule:" not in text:
            continue
        for m in RULE_RE.finditer(text):
            found.append((f"rule:{m.group(1)}{m.group(2) or ''}", filename, owner.get(id(node), "<module>"),
                          node.lineno))
    return found


def code_rules() -> Dict[str, List[str]]:
    """name -> ["module:function", ...] over every agent module."""
    out: Dict[str, List[str]] = {}
    for name in MODULES:
        for rule, mod, fn, _ in scan_rules((REPO / name).read_text(), name):
            site = f"{mod}:{fn}"
            if site not in out.setdefault(rule, []):
                out[rule].append(site)
    return out


def registry() -> Dict[str, dict]:
    return json.loads(REGISTRY.read_text())["rules"]


def migration_plan_ids() -> Set[str]:
    """The delta ids of ARCHITECTURE.md section 10.8 (its table's first column)."""
    text = ARCHITECTURE.read_text()
    start = text.index("### 10.8 Migration plan")
    end = text.find("\n### ", start + 1)
    section = text[start:end if end >= 0 else len(text)]
    return set(re.findall(r"^\| \*\*(R\d{2})\*\*", section, re.M))


class TestScanner(unittest.TestCase):
    def test_scanner_is_not_vacuous(self):
        src = '''
"""module docstring: rule:docstring_only is not a decision"""
ROLE = "board"
def f(x):
    """rule:in_a_docstring is not either"""
    # rule:in_a_comment is invisible to the AST
    a = "rule:plain_name"
    b = f"rule:qualified[{ROLE}]"
    c = f"rule:with_args({x.id})"
    d = f"rule:family.{x}"
    e = "made by rule: nothing (a space after the colon is no name)"
    return a, b, c, d, e
'''
        names = sorted(n for n, *_ in scan_rules(src))
        self.assertEqual(names, ["rule:family", "rule:plain_name", "rule:qualified[board]", "rule:with_args"])
        self.assertEqual({fn for _, _, fn, _ in scan_rules(src)}, {"f"})

    def test_runtime_canonical_names_agree(self):
        import controller
        for raw, want in (("rule:connector_to_cut(module_1.usb)", "rule:connector_to_cut"),
                          ("rule:closure.rebate.plate", "rule:closure"),
                          ("rule:text_evidence[board]", "rule:text_evidence[board]"),
                          ("prescore+llm:vote+rank", None), ("llm", None)):
            self.assertEqual(controller.canonical_rule(raw), want, raw)
        for name in registry():
            self.assertEqual(controller.canonical_rule(name), name, name)


class TestRegistry(unittest.TestCase):
    def test_every_rule_in_the_code_is_registered(self):
        reg = registry()
        missing = {n: sites for n, sites in code_rules().items() if n not in reg}
        self.assertEqual(missing, {}, "register every rule:* decision in controller_rules.json with its class "
                                      "and justification (owner decision D1)")

    def test_entries_are_classified_and_justified(self):
        for name, e in registry().items():
            with self.subTest(name=name):
                self.assertIn(e.get("class"), CLASSES)
                self.assertIn(e.get("status"), STATUSES)
                self.assertTrue(str(e.get("justification", "")).strip())

    def test_no_semantic_rule_is_active(self):
        reg, code = registry(), code_rules()
        plan = migration_plan_ids()
        self.assertTrue({"R01", "R02", "R03"} <= plan, plan)          # the plan table is read, not empty
        for name, e in reg.items():
            with self.subTest(name=name):
                if e["class"] == "semantic-rule" and name in code:
                    self.assertEqual(e["status"], "pending_migration", f"{name} is a semantic rule in the code")
                    self.assertRegex(e.get("migration", ""), DELTA_RE)
                    self.assertIn(e["migration"], plan, f"{name}: migration {e.get('migration')} is not in 10.8")
                if e["status"] == "pending_migration":
                    self.assertEqual(e["class"], "semantic-rule", f"{name}: only a semantic rule can be pending")

    def test_registry_matches_the_code(self):
        reg, code = registry(), code_rules()
        for name, e in reg.items():
            with self.subTest(name=name):
                if e["status"] == "retired":
                    self.assertNotIn(name, code, f"{name} is retired (migrated in {e.get('migrated_in')}) but is back "
                                                 f"in {code.get(name)}")
                    self.assertRegex(e.get("migrated_in", ""), DELTA_RE)
                else:
                    self.assertIn(name, code, f"{name} is registered {e['status']} but no agent module uses it")

    def test_r01_conversions_are_retired(self):
        reg = registry()
        for name in ("rule:text_coverage", "rule:coverage_infeasible", "rule:text_evidence[closure]"):
            self.assertEqual((reg[name]["class"], reg[name]["status"], reg[name]["migrated_in"]),
                             ("semantic-rule", "retired", "R01"), name)
        self.assertNotIn("rule:text_coverage", code_rules())

    def test_the_agent_reads_the_registry(self):
        import controller
        reg = controller.load_registry()
        self.assertEqual(set(reg), set(registry()))
        self.assertEqual(controller.decision_class("rule:text_evidence[stack]", reg), "semantic-rule")
        self.assertEqual(controller.decision_class("rule:connector_to_cut(module_1.usb)", reg), "plant")
        self.assertEqual(controller.decision_class("llm:controller", reg), "llm")
        self.assertEqual(controller.decision_class("prescore+llm:vote+rank", reg), "llm")
        self.assertEqual(controller.decision_class("prescore:derive", reg), "guardrail")
        self.assertEqual(controller.decision_class("rule:never_registered", reg), "unregistered")

    def test_every_decision_tag_the_controller_records_is_registered(self):
        # R02/R11 review fix 1b: the `by` tags controller.py records (not rule names) are listed in decision_tags
        import controller
        tags = json.loads(REGISTRY.read_text())["decision_tags"]
        for tag in (controller.CONTROLLER_BY, controller.SEARCH_BY):
            self.assertIn(tag, tags, tag)
        self.assertEqual(controller.decision_class(controller.SEARCH_BY, controller.load_registry()), "guardrail")
        self.assertIn("guardrail", tags[controller.SEARCH_BY])


if __name__ == "__main__":
    unittest.main()

"""Hard-coding guard (milestone M0): assembly-mode logic holds no target-specific number or part.

Numbers specific to the enclosure target or its variants (board sizes, Pico 2
sizes, port positions) may live only in benchmarks/enclosure/parts/*/part.json
and in the request / L1 text. This test scans the assembly-mode modules' AST for
those numbers as numeric literals and for catalogue part ids and aliases as
string literals. The id/alias list is read from both catalogues (enclosure and
generalize, generalize delta 001 T14) at test time, so it grows with them.
"""

import ast
import json
import unittest
from pathlib import Path
from typing import Iterable, List, Set

REPO = Path(__file__).parent
PARTS = REPO / "benchmarks" / "enclosure" / "parts"
CATALOGUES = (PARTS, REPO / "benchmarks" / "generalize" / "parts")
MODULES = ("assembly.py", "parts.py", "feature_graph.py", "assembly_checks.py", "layout.py",
           "controller.py")   # changed in migration delta R01: the closed-loop controller is agent logic too
BANNED_NUMBERS = (70, 50, 51, 21, 4.9, 17.5, 32.5, 65, 45, 80, 60, 90, 40, 47, 11.4, 1.3, 1.6, 2.54, 12,
                  35, 8.5, 10.9, 6.9, 1.85)


def geometry_vocabulary() -> Set[str]:
    """The feature graph's own primitive names (feature_graph.PRIMITIVES: box, cylinder, tube, ...). They are the agent's
    closed geometry vocabulary, not design data, so a catalogue alias that happens to equal one (generic_tube's "tube")
    does not make the primitive name a hard-coded part. Nothing else is exempt."""
    import feature_graph
    return {str(p).lower() for p in feature_graph.PRIMITIVES}


def catalogue_strings() -> Set[str]:
    out: Set[str] = set()
    for path in sorted(p for root in CATALOGUES for p in root.glob("*/part.json")):
        data = json.loads(path.read_text())
        out.add(str(data["id"]).lower())
        out.update(str(n).lower() for n in data.get("names", []))
    return out - geometry_vocabulary()


def scan(source: str, banned_strings: Iterable[str], filename: str = "<source>") -> List[str]:
    """Every banned numeric literal and every string literal equal to a part id or alias."""
    strings = {s.lower() for s in banned_strings}
    found = []
    for node in ast.walk(ast.parse(source, filename)):
        if not isinstance(node, ast.Constant):
            continue
        v = node.value
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            if any(abs(v - b) < 1e-9 for b in BANNED_NUMBERS):
                found.append(f"{filename}:{node.lineno}: numeric literal {v!r}")
        elif isinstance(v, str) and v.strip().lower() in strings:
            found.append(f"{filename}:{node.lineno}: catalogue id/alias {v!r}")
    return found


class TestNoHardcoding(unittest.TestCase):
    def test_guard_is_not_vacuous(self):
        found = scan("x = 70\ny = 'rpi_pico2'", {"rpi_pico2"})
        self.assertEqual(len(found), 2, found)
        self.assertTrue(any("70" in f for f in found) and any("rpi_pico2" in f for f in found))
        self.assertEqual(len(scan("z = -2.54 + 1.6000000000001", set())), 2)

    def test_catalogue_strings_are_read_from_part_files(self):
        strings = catalogue_strings()
        self.assertIn("rpi_pico2", strings)
        self.assertGreater(len(strings), 11)
        # the only exemption (changed in generalize delta 003: the prism primitive, C4)
        self.assertEqual(geometry_vocabulary(), {"box", "cylinder", "tube", "shell", "part", "prism"})
        for root in CATALOGUES:              # every catalogue's ids are scanned (generalize delta 001 T14)
            ids = {json.loads(p.read_text())["id"] for p in root.glob("*/part.json")}
            self.assertTrue(ids, root)
            self.assertTrue(ids <= strings, root)

    def test_assembly_modules_hold_no_target_literals(self):
        strings = catalogue_strings()
        problems = []
        missing = [name for name in MODULES if not (REPO / name).is_file()]
        self.assertEqual(missing, [], "every assembly-mode module must exist and be scanned (a missing file fails)")
        for name in MODULES:
            problems += scan((REPO / name).read_text(), strings, name)
        self.assertEqual(problems, [])


if __name__ == "__main__":
    unittest.main()

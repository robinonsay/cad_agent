"""Structural forms (archetypes) as controller choices (migration delta R12; owner decision D1; loop/ARCHITECTURE.md
10.8, R07 partly done).

Until R12 the archetype was gated by the text: a shell was feasible only when a sentence named an enclosure word
(design_rules.json archetypes.tray_lid.evidence), and with several feasible archetypes and no valid answer the first of
Python's enumeration was taken (`rule:first_option[archetype]`). Both decided a form by reading the text. Now:

* **Plant feasibility** (`form_options`): Python enumerates every structural form the derivation rules can build for the
  chosen contents, from catalogue data only, and explains each infeasible one. The shell needs a primary the plant can
  hold (a mount_holes interface or a seat interface: standoffs or a cradle); the plate needs a content part with a
  `bolt_face` interface and a catalogue fastener chain that fits it (plate.py). With two or more candidates each is
  derived on a scratch copy, and a form whose derivation fails is infeasible with the plant's reason.
* **Controller choice**: one feasible form is recorded as plant feasibility (`rule:only_feasible`); several are one
  content-keyed, seeded-shuffled, permutation-voted menu (R02). With no valid answer the plant measures every feasible
  form (derive, manifold build, every check) and keeps the lowest controllable error (`prescore:archetype`, a guardrail
  tag), never Python's first option.
* **Sensors** (form level): `form_evidence` (a text sensor: a buildable form's vocabulary is named and the current form's
  is not; it reports the quotes, it never decides) and `content_placed` of a part another form would place (an engaged
  reference part that a shell leaves unplaced). Both offer **set_archetype** (invalidates the archetype stage) through
  R02's APPLIERS, menu, permutation vote and verifier search.
* **Spec slots by form** (`candidate_forms`, `spec_slots`): ParseSpec asks the shell slots always (unchanged) and adds a
  form's slots (design_rules.json spec_slots.forms) when a part the text names can anchor that form (catalogue data).
  Units are checked against the word after the number (design_rules.json unit_words), ranges against the slot's band.

Nothing here holds a number, part or face of one request (test_no_hardcoding.py scans this module); every rule:*
decision string is registered in controller_rules.json (test_controller_authority.py).
"""

from __future__ import annotations

import math
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence, Tuple

import assembly as A            # circular on purpose: only module attributes are read, at call time
import assembly_checks as ac
import cad_checks as cc
import menus
import parts as pt

SHELL = "shell"
PLATE = "plate"
FORM_LABEL = "assy_archetype"            # the archetype menu's label (transcripts, scripted fakes)
SET_ARCHETYPE = "set_archetype"          # the action kind
FORM_EVIDENCE = "form_evidence"          # the sensor's check type and id
PRESCORE_BY = "prescore:archetype"       # no valid vote: the feasible form with the lowest measured error (guardrail)
SUBJECTS = {SHELL: "An enclosure is being designed from this request and its requirements.",
            "any": "A printed part is being designed from this request and its requirements: an enclosure, or another "
                   "printed form ({others})."}
OTHER_FORMS = {PLATE: "a plate or platform the parts bolt to"}


# ---------------------------------------------------------------------------
# The archetype vocabulary (design_rules.json archetypes: form, closure, meaning, evidence words)
# ---------------------------------------------------------------------------


def archetype_rows(rules: pt.Rules) -> Dict[str, dict]:
    """form -> {name, key, meaning, evidence} for every archetype the rules describe (the shell's closure is the screws
    of A.SHELL, so its key stays "tray_lid+screws" and the regression records read the same)."""
    out = {}
    for name, row in (rules.archetypes or {}).items():
        form = row.get("form") or (SHELL if name == A.SHELL[0] else name)
        closure = A.SHELL[1] if form == SHELL else str(row.get("closure") or "")
        out[form] = {"name": name, "key": f"{name}+{closure}" if closure else name, "meaning": row.get("meaning", name),
                     "evidence": list(row.get("evidence") or [])}
    if SHELL not in out:
        out[SHELL] = {"name": A.SHELL[0], "key": "+".join(A.SHELL), "meaning": SHELL, "evidence": []}
    return out


def form_of(rules: pt.Rules, key: Optional[str]) -> Optional[str]:
    """The form of an archetype key ("tray_lid+screws" -> shell), or None."""
    return next((f for f, r in archetype_rows(rules).items() if r["key"] == key), None)


def current_form(st: "A.AssemblyState") -> Optional[str]:
    return form_of(st.rules, (st.choices.get("archetype") or {}).get("value")) if st.rules else None


def is_plate(st: "A.AssemblyState") -> bool:
    return current_form(st) == PLATE


# ---------------------------------------------------------------------------
# Candidate forms before Contents (ParseSpec, the Contents wording): from the parts the text names
# ---------------------------------------------------------------------------


def candidate_forms(st: "A.AssemblyState") -> List[str]:
    """The forms a part the request or an L1 names (A.named_parts, the alias reading Contents admission uses) could
    anchor, read from catalogue data: the shell always (the pipeline's original form), the plate when a named part
    offers a bolt_face interface. Only decides which spec slots are offered and how the questions name the design."""
    out = [SHELL]
    named = A.named_parts(st) if st.catalog is not None and st.texts else {}
    if any(pt.bolt_face_interface(st.catalog.get(pid)) is not None for pid in named):
        out.append(PLATE)
    return out


def subject(forms_: Sequence[str]) -> str:
    """The first sentence of ParseSpec's questions: the enclosure wording when the shell is the only candidate (the
    regression prompts stay byte-identical); with other candidates the enclosure wording is kept and the other forms are
    added (review fix N6: an enclosure request naming a bolt_face part keeps its enclosure prompt, it only gains slots
    and a mention of the other form)."""
    if list(forms_) == [SHELL]:
        return SUBJECTS[SHELL]
    return SUBJECTS["any"].format(others="; ".join(OTHER_FORMS.get(f, f) for f in forms_ if f != SHELL))


def spec_slots(rules: pt.Rules, forms_: Sequence[str]) -> List[dict]:
    """The slots ParseSpec maps: the shell slots (unchanged order) plus each other candidate form's slots."""
    out = list(rules.spec_slots)
    for f in forms_:
        if f != SHELL:
            out += list((rules.form_slots or {}).get(f, []))
    return out


def unit_of_word(rules: pt.Rules, word: Optional[str]) -> Optional[str]:
    """The unit a word states (design_rules.json unit_words), or None."""
    w = str(word or "").strip().lower()
    if not w:
        return None
    return next((u for u, words in (rules.unit_words or {}).items() if w in words), None)


def number_unit(rules: pt.Rules, n: Mapping[str, Any]) -> Optional[str]:
    """The unit a number occurrence carries in the text: its regex unit (mm, deg), else the word right after it."""
    return unit_of_word(rules, n.get("unit")) or unit_of_word(rules, n.get("after"))


def number_scale(rules: pt.Rules, n: Mapping[str, Any]) -> float:
    """Review fix N2: the factor that turns the number into its unit (design_rules.json unit_words: 2.5 kN -> 2500 N,
    0.05 GPa -> 50 MPa, 6 cm2 -> 600 mm2). A regex unit (mm, cm, deg) is already scaled by extract_numbers: factor 1."""
    if unit_of_word(rules, n.get("unit")) is not None:
        return 1.0
    w = str(n.get("after") or "").strip().lower()
    u = unit_of_word(rules, w)
    return float(((rules.unit_scales or {}).get(u) or {}).get(w, 1.0)) if u else 1.0


def slot_value(rules: pt.Rules, slot: Mapping[str, Any], n: Mapping[str, Any]) -> float:
    """The value a mapped number gives a slot: scaled by its unit word's factor when the word states the slot's own
    unit (another unit is slot_violation's to reject); a shell slot or a word of no known unit keeps the number."""
    want = str(slot.get("unit") or "")
    if want in (rules.unit_words or {}) and number_unit(rules, n) == want:
        return float(n["value"]) * number_scale(rules, n)
    return float(n["value"])


def slot_violation(rules: pt.Rules, slot: Mapping[str, Any], n: Mapping[str, Any]) -> Optional[str]:
    """A mapped number that cannot state the slot: its unit word names another unit, or its value lies outside the
    slot's plausible band. None when it may (a number with no unit word is accepted: the text does not say)."""
    got = number_unit(rules, n)
    want = str(slot.get("unit") or "")
    if got is not None and want in (rules.unit_words or {}) and got != want:
        return f"{slot['name']} is in {want}, but {n['id']} ({n['text']}) is in {got}"
    rng = slot.get("range")
    v = slot_value(rules, slot, n)
    if rng is not None and not rng[0] <= v <= rng[1]:
        return f"{slot['name']} must lie in [{rng[0]:g}, {rng[1]:g}] (got {v:g})"
    return None


def apply_exact_slots(st: "A.AssemblyState", slots: Sequence[Mapping[str, Any]]) -> None:
    """R12 review 2 (N6): a slot that `sets` a band (design_rules.json: one stated value, e.g. a thickness given as a
    single number) copies its mapped value to each end of that band the text left unmapped, with the same provenance
    (so the trace links the same L1). An end the text states itself keeps its own number. Slot semantics: the LLM
    chose the slot; Python reads no text here. The plate's setpoints of a band narrower than twice the design margin
    are its centre (plate.band_setpoints), so an exact value is the target and the checks keep the stated limits."""
    for s in slots:
        targets = s.get("sets") or []
        if not targets or s["name"] not in st.spec:
            continue
        for t in targets:
            if t in st.spec and not str(st.spec_provenance.get(t, "")).startswith("rules:"):
                continue
            st.spec[t] = st.spec[s["name"]]
            st.spec_provenance[t] = st.spec_provenance[s["name"]]
            st.notes.append(f"parse_spec: {t} = {st.spec[t]:g} from {s['name']} (one stated value sets both ends of "
                            "the band)")


def pair_violations(slots: Sequence[Mapping[str, Any]], values: Mapping[str, float]) -> List[Tuple[str, List[str]]]:
    """lo/hi slot pairs (design_rules `pair`, `side`) whose mapped lo exceeds the mapped hi."""
    out = []
    for s in slots:
        if s.get("side") != "lo" or s["name"] not in values or s.get("pair") not in values:
            continue
        lo, hi = values[s["name"]], values[s["pair"]]
        if lo > hi:
            out.append((f"{s['name']} ({lo:g}) must not exceed {s['pair']} ({hi:g})", [s["name"], s["pair"]]))
    return out


# ---------------------------------------------------------------------------
# Plant feasibility of each form for the chosen contents
# ---------------------------------------------------------------------------


def shell_feasibility(st: "A.AssemblyState") -> Tuple[bool, str]:
    """The shell holds a primary with a mount_holes interface on standoffs, or one that rests on a seat plane in a
    cradle (migration delta R11). Catalogue data only."""
    import building_blocks as bb
    prim = A.primary_item(st)
    pid = prim["part"] if prim else None
    if pid is None:
        return False, "no primary part"
    if pt.mount_interface(st.catalog.get(pid)) is None and not bb.is_cradle(st):
        return False, f"the primary {pid} has no {pt.MOUNT_HOLES} interface and no seat plane to rest on"
    return True, ""


def catalogue_options(st: "A.AssemblyState") -> List[dict]:
    """Every form the rules describe, with its catalogue feasibility and the reason when it is infeasible, in the
    vocabulary's order (the shell first: the order is the schema enum and the stub's first option, never shown)."""
    import plate as pl
    rows = archetype_rows(st.rules)
    check: Dict[str, Callable[["A.AssemblyState"], Tuple[bool, str]]] = {SHELL: shell_feasibility,
                                                                       PLATE: pl.feasibility}
    out = []
    for form, row in rows.items():
        fn = check.get(form)
        ok, why = fn(st) if fn else (False, "no derivation rules for this form yet")
        out.append({"form": form, "key": row["key"], "meaning": row["meaning"], "feasible": bool(ok),
                    "reason": "" if ok else why})
    return out


def trial(st: "A.AssemblyState", key: str) -> Optional[str]:
    """Derive the form on a scratch copy of the state (no LLM, no files): None, or the plant's failure."""
    sc = A.snapshot(st)
    A.choice(sc, "archetype", key, "rule:only_feasible")
    try:
        return A.derive(sc)
    except AssertionError:
        raise
    except Exception as e:          # noqa: BLE001 - a failed trial is an infeasible form, never a crash
        return f"{type(e).__name__}: {e}"


def form_options(st: "A.AssemblyState", trials: bool = True) -> List[dict]:
    """catalogue_options, and with two or more catalogue-feasible forms each one derived on a scratch copy: a form whose
    derivation fails is infeasible with that reason (plant feasibility, explained)."""
    opts = catalogue_options(st)
    if trials and sum(o["feasible"] for o in opts) >= 2:
        for o in opts:
            if o["feasible"]:
                err = trial(st, o["key"])
                if err is not None:
                    o.update(feasible=False, reason=f"its derivation fails here: {err}")
    return opts


def record_options(st: "A.AssemblyState", opts: Sequence[dict]) -> None:
    st.forms = [dict(o) for o in opts]
    for o in opts:
        if not o["feasible"]:
            line = f"choose_archetype: {o['form']} is not buildable: {o['reason']}"
            if line not in st.notes:
                st.notes.append(line)


def feasible_keys(st: "A.AssemblyState") -> List[str]:
    """The archetype keys of the forms recorded feasible at ChooseArchetype (st.forms), else the catalogue-feasible."""
    rows = st.forms or catalogue_options(st)
    return [o["key"] for o in rows if o["feasible"]]


def menu_prompt(request: str, opts: Sequence[dict], order: Sequence[str]) -> str:
    """The archetype question (content-keyed: the forms' ids; their meanings from design_rules.json)."""
    by = {o["form"]: o for o in opts}
    lines = "\n".join(f"- {f}: {by[f]['meaning']}" for f in order)
    return (f"Request: {request}\n\nThe parts can be built into these structural forms. Which form does the request "
            f"ask for?\n{lines}\n\n{A.ID_ANSWER}")


def prescore_form(st: "A.AssemblyState", keys: Sequence[str]) -> Tuple[Optional[str], Dict[str, Any]]:
    """No valid vote: measure every feasible form on a scratch copy (derive, manifold build, every measured check; text
    sensors such as form_evidence are left out, review fix N4) and keep the lowest controllable error (a guardrail: an
    error-based plant choice). Returns (key or None, the errors)."""
    errors: Dict[str, Any] = {}
    best = None
    for key in keys:
        sc = A.snapshot(st)
        A.choice(sc, "archetype", key, PRESCORE_BY)
        try:
            err = A.derive(sc)
            if err is None:
                _, results = A.plant_error(sc)
                # review fix N4: the form_evidence text sensor (a word list) never decides the form here: only the
                # measured checks of each form's derivation are compared
                measured = [x for x in results if x.type != FORM_EVIDENCE and (x.evidence or {}).get("basis") != "text"]
                k = cc.error_key(A.controllable(measured)[0])
                errors[key] = {"hard_failures": k.hard_failures, "violation": round(k.violation, 6)}
                if best is None or (k.hard_failures, k.violation) < best[0]:
                    best = ((k.hard_failures, k.violation), key)
            else:
                errors[key] = err
        except AssertionError:
            raise
        except Exception as e:      # noqa: BLE001
            errors[key] = f"{type(e).__name__}: {e}"
    return (best[1] if best else None), errors


def choose(st: "A.AssemblyState", llm, request: str) -> Optional[str]:
    """ChooseArchetype's decision. Returns None, or the typed failure (no feasible form, or the controller's
    set_archetype names a form that cannot be built here)."""
    opts = form_options(st)
    record_options(st, opts)
    feasible = [o for o in opts if o["feasible"]]
    if not feasible:
        return ("not implemented: archetype (" + "; ".join(f"{o['form']}: {o['reason']}" for o in opts) + ")")
    keys = [o["key"] for o in feasible]
    want = st.control.get("archetype")
    if want:                                 # the controller's set_archetype (recorded by its applier)
        if want not in keys:
            why = next((o["reason"] for o in opts if o["key"] == want), "not a known archetype")
            return f"archetype {want}: not buildable here ({why})"
        return None
    if len(keys) == 1:
        A.choice(st, "archetype", keys[0], "rule:only_feasible")
        return None
    ids = [o["form"] for o in feasible]
    vote = menus.perm_vote(llm, FORM_LABEL, lambda order: menu_prompt(request, feasible, order), ids,
                           A.menu_rules(st), A.question_seed(llm, FORM_LABEL, request, ids), key="archetype")
    if vote.pick is not None:
        key = next(o["key"] for o in feasible if o["form"] == vote.pick)
        A.choice(st, "archetype", key, "llm", votes=dict(vote.votes), consistency=vote.consistency,
                 confident=vote.confident, options=ids)
        return None
    key, errors = prescore_form(st, keys)
    if key is None:
        return "not implemented: archetype (no feasible form derived: " + "; ".join(f"{k}: {v}" for k, v in
                                                                                 errors.items()) + ")"
    A.choice(st, "archetype", key, PRESCORE_BY, errors=errors, reason="no valid controller answer")
    return None


# ---------------------------------------------------------------------------
# Sensor: form_evidence (a text sensor; it reports, the controller decides)
# ---------------------------------------------------------------------------


def evidence_by_form(st: "A.AssemblyState", forms_: Sequence[str]) -> Dict[str, List[dict]]:
    rows = archetype_rows(st.rules)
    out = {}
    for f in forms_:
        words = rows.get(f, {}).get("evidence") or []
        out[f] = A.text_evidence(st.texts, words) if words else []
    return out


def add_form_checks(st: "A.AssemblyState", plan: ac.Plan) -> None:
    """form_evidence: with two or more buildable forms, the request or an L1 names a buildable form's words
    (design_rules.json archetypes.<form>.evidence) and none of the current form's: reported with the quotes (controllable,
    actionable by set_archetype). Not added when only one form is buildable (nothing to correct)."""
    keys = feasible_keys(st)
    if len(keys) < 2:
        return
    forms_ = [form_of(st.rules, k) for k in keys]
    cur = current_form(st)
    ev = evidence_by_form(st, forms_)
    others = [f for f in forms_ if f != cur and ev.get(f)]
    passed = bool(ev.get(cur)) or not others
    quotes = [{"source": h["source"], "quote": h["quote"], "match": h["match"], "form": f}
              for f in ([cur] if ev.get(cur) else others) for h in ev.get(f, [])]
    plan.add(FORM_EVIDENCE, FORM_EVIDENCE, "the structural form is one the text asks for (when the text names a "
             "buildable form's words, the design is that form)", current=cur, expected=others if not passed else [],
             quotes=quotes[:4], sources=sorted({q["source"] for q in quotes}))


def form_evidence_check(cid: str, typ: str, a: Mapping[str, Any], bodies, plan: ac.Plan) -> cc.CheckResult:
    q = (a.get("quotes") or [{}])[0]
    if a.get("expected"):
        detail = (f"the design is a {a['current']}, but {q.get('source', 'the text')} names "
                  f"{' or '.join(a['expected'])} words (\"{q.get('match', '')}\"): \"{q.get('quote', '')}\"")
    else:
        detail = f"the design is a {a['current']}" + (f"; {q.get('source')} names it" if q.get("source") else "")
    return ac._result(cid, typ, not a.get("expected"), 1.0 if not a.get("expected") else -1.0, "count",
                      {"current": a.get("current"), "expected": list(a.get("expected") or []),
                       "quotes": list(a.get("quotes") or []), "detail": detail, "basis": "text"})


# ---------------------------------------------------------------------------
# Actuator: set_archetype
# ---------------------------------------------------------------------------


def archetype_action(st: "A.AssemblyState", form: str, r: cc.CheckResult, why: str):
    import controller as C
    row = archetype_rows(st.rules)[form]
    ev = [{"source": q.get("source"), "quote": q.get("quote")} for q in (r.evidence or {}).get("quotes") or []]
    return C.Action(kind=SET_ARCHETYPE, target="form", value=row["key"],
                    words=f"{SET_ARCHETYPE} form={form}: build the design as {form}: {row['meaning']}{why}",
                    targets=[r.check_id], invalidates="archetype", evidence=ev, ident=f"{SET_ARCHETYPE}:{form}")


def archetype_actions(st: "A.AssemblyState", r: cc.CheckResult) -> list:
    """A failing form_evidence check: one set_archetype per buildable form other than the current one (the forms the
    text names first)."""
    cur = current_form(st)
    keys = feasible_keys(st)
    forms_ = [form_of(st.rules, k) for k in keys]
    expected = list((r.evidence or {}).get("expected") or [])
    order = [f for f in expected if f in forms_] + [f for f in forms_ if f not in expected]
    return [archetype_action(st, f, r, "") for f in order if f != cur]


def placing_actions(st: "A.AssemblyState", r: cc.CheckResult) -> list:
    """A failing content_placed check of an item another buildable form would place (the plate places a reference part
    a content part engages): set_archetype to that form."""
    import plate as pl
    item = (r.evidence or {}).get("item")
    u = next((x for x in st.unplaced if x.get("id") == item), None)
    cur = current_form(st)
    if u is None or cur == PLATE or PLATE not in [form_of(st.rules, k) for k in feasible_keys(st)]:
        return []
    if not pl.places(st, u["part"]):
        return []
    return [archetype_action(st, PLATE, r, f" (it places {item}, which the {cur} leaves unplaced)")]


def apply_archetype(st: "A.AssemblyState", action, record: Mapping[str, Any], by: str = "llm:controller") -> None:
    """R02's applier signature (state, action, record, by): ChooseArchetype keeps this form when it re-runs."""
    st.control["archetype"] = action.value
    A.choice(st, "archetype", action.value, by, **dict(record))


def state_lines(st: "A.AssemblyState") -> List[str]:
    """The form line of the controller's state words, only when two or more forms are buildable (the regression's
    state words are unchanged)."""
    if len(feasible_keys(st)) < 2:
        return []
    other = [form_of(st.rules, k) for k in feasible_keys(st) if form_of(st.rules, k) != current_form(st)]
    return [f"- structural form: {current_form(st)} (also buildable: {', '.join(other)})"]


DIRECTIONS: Dict[str, Tuple[str, str]] = {FORM_EVIDENCE: ("the structural form the text names", "semantic")}
EXTRA_CHECKS: Dict[str, Callable] = {FORM_EVIDENCE: form_evidence_check}
ac.EXTRA_CHECKS.update(EXTRA_CHECKS)

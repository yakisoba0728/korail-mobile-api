"""The rule that decides what is allowed in the package's top-level ``__all__``.

``__all__`` is the public contract. After 1.0.0 a name in it cannot be removed
without breaking somebody, so the expensive mistake is not "we forgot to export
X" — that is a one-line addition later — but "we exported X and now we own it
forever". Everything here exists to make the second mistake fail in CI rather
than in a release.

The rule, stated once:

* Clients, configuration and sessions are public.
* Every type in the transitive closure of a public client method's annotations
  is public — a caller who receives a value must be able to name its type.
* Errors are public. Consent types are public.
* Domain values a caller passes in, or compares a response against, are public.

and everything else is not: transport-layer constants, internal allowlist and
route tables, the ``parse_*``/``pair_*`` functions the client already calls on
the caller's behalf, the token-generation machinery, and constants already
reachable as a default on a config field.

**"Demote" means deleting the import line AND the ``__all__`` entry**, not one
of them. ``tests/test_next_variant_reads.py`` asserts both halves for the names
it holds back (``held_back not in __all__`` *and* ``not hasattr(pkg, ...)``);
deleting only the ``__all__`` entry leaves the attribute reachable and the
holdback half-done. ``test_all_equals_the_import_block`` below makes that
symmetry a property of the whole file rather than of the names someone
remembered to check.

Nothing here holds a list of exported names. A list of names is the thing that
rots — this repository has already shipped two hand-maintained counts that went
stale. Every check derives its expectation from the source: ``__init__.py``'s
import statements via ``ast``, the client's annotations via
``typing.get_type_hints``, the module each name was defined in via the import
that brought it here. What is hand-written is *policy* — which modules may
export at all, and which non-type constants have earned a place — and policy is
what a human should be made to argue for.

This file is shared with the sibling repository. Everything below the
END-OF-PER-REPOSITORY-BLOCK marker is byte-identical in both; only the block
above it differs.
"""

# ---------------------------------------------------------------------------
# PER-REPOSITORY BLOCK. The sibling repository's copy of this file differs from
# this one in exactly the constants below and nothing else.
# ---------------------------------------------------------------------------

#: The distribution's import name.
PACKAGE_NAME = "korail_mobile_api"

#: The client class whose public methods define the reachable type closure.
CLIENT_CLASS_NAME = "KorailClient"

#: Modules whose module-level *functions* may appear in ``__all__``. These are
#: the entry points and the vocabulary a caller uses directly: constructing a
#: client, building a config, naming an error, stating consent, entering the
#: queue. A function exported from anywhere else is, by construction, a step
#: the client already performs for the caller.
FUNCTION_EXPORTING_MODULES = frozenset(
    {
        "client",
        "config",
        "consent",
        "errors",
        "live",
        "netfunnel",
    }
)

#: Modules that may export types and domain constants but never a function.
#: These hold request dataclasses, response dataclasses and the coded values
#: the app sends — all things a caller names — beside the builders, encoders
#: and table generators that produce them, which a caller does not.
DATA_EXPORTING_MODULES = frozenset(
    {
        "constants",
        "dynapath",
        "limousine_models",
        "models",
        "mutation_models",
        "read_models",
        "read_payloads",
    }
)

#: Every exported name that is neither a class nor a function, with the reason
#: it is a *domain* value rather than a transport detail. The distinction: a
#: caller either passes these to a method or compares a response field against
#: them. Anything describing how bytes reach the server — base URLs, header
#: names, timeouts, service ids, route tables, app keys — is configuration or
#: internal policy and belongs on a config field or in its own module.
DOMAIN_CONSTANTS = {
    "KORAIL_DIRECT_ITINERARY_CODE": (
        "The itinerary-type code a caller reads off a search result to tell a "
        "direct journey from a transfer one."
    ),
    "KORAIL_TRANSFER_ITINERARY_CODE": (
        "Its transfer-flavoured pair; the two are only useful together."
    ),
    "KORAIL_MAX_JOURNEY_LEGS": (
        "A caller-facing limit: build a journey with more legs than this and "
        "the request is refused before it is sent."
    ),
    "KORAIL_MAX_PASSENGERS_PER_RESERVATION": (
        "The same, for passenger rows. A caller sizing a booking needs the "
        "number the validation is written against."
    ),
    "KORAIL_MAX_DISCOUNT_CARD_SECTIONS": (
        "The same, for the sections of a discount-card purchase."
    ),
    "KORAIL_MERGE_SEAT_FLAGS_BY_CABIN": (
        "The seat flags a merge reservation must carry per cabin class. A "
        "caller assembling a merged booking selects from this table."
    ),
    "KORAIL_STANDBY_HOLD_MESSAGE_CODE": (
        "The response code that means 'you are on the standby list', which a "
        "caller compares against to branch on the outcome of a hold."
    ),
    "KORAIL_USER_AGENT": (
        "The one transport-layer string that is deliberately public. 1.0.0 "
        "changed it, and the change is what makes a bare client able to log "
        "in at all; a caller who overrides it, or who wants to check what "
        "theirs is being compared against, must be able to read the default."
    ),
    "KORAIL_MILEAGE_LEDGER_KTX": (
        "A ledger selector a caller passes to the mileage history request."
    ),
    "KORAIL_MILEAGE_LEDGER_RAIL_POINT": ("Its sibling ledger selector."),
    "KORAIL_MILEAGE_MOVEMENT_ALL": (
        "A movement filter a caller passes to the mileage history request."
    ),
    "KORAIL_MILEAGE_MOVEMENT_EARNED": ("Its earned-only sibling."),
    "KORAIL_MILEAGE_MOVEMENT_SPENT": ("Its spent-only sibling."),
    "SELF_SEAT_CHANGE_ROOM_CLASS_CODES": (
        "The room-class codes a caller chooses from when asking for a "
        "self-service seat change."
    ),
}

# ---------------------------------------------------------------------------
# END OF PER-REPOSITORY BLOCK — everything below is byte-identical across both
# repositories. A diff of the two files below this line that shows anything is
# a bug in one of them, not a local adaptation.
# ---------------------------------------------------------------------------

import ast
import dataclasses
import importlib
import inspect
import sys
import typing
from pathlib import Path

import pytest


PACKAGE = importlib.import_module(PACKAGE_NAME)
PACKAGE_DIR = Path(PACKAGE.__file__).parent
EXPORTED = list(PACKAGE.__all__)
EXPORTED_SET = set(EXPORTED)
EXPORTING_MODULES = FUNCTION_EXPORTING_MODULES | DATA_EXPORTING_MODULES


def _init_imports() -> dict[str, str]:
    """Map every name ``__init__.py`` imports to the module it came from.

    Derived from the source with ``ast`` rather than from the imported package,
    because the question this file asks is about the *import block* — a name
    that is present at runtime for some other reason (a re-export inside a
    submodule, a leftover attribute) is exactly what the first check is looking
    for.
    """
    tree = ast.parse((PACKAGE_DIR / "__init__.py").read_text(encoding="utf-8"))
    imported: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.level:
            for alias in node.names:
                imported[alias.asname or alias.name] = node.module or ""
    return imported


def _module_level_functions(module: str) -> set[str]:
    path = PACKAGE_DIR / f"{module}.py"
    if not path.exists():
        return set()
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return {
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def _resolve_hints(obj: object, module_name: str) -> dict[str, object]:
    """Resolve annotations in the namespace of the module that wrote them.

    Every module in this package uses ``from __future__ import annotations``, so
    every annotation is a string that has to be evaluated somewhere. It must be
    evaluated where it was written: a type demoted out of ``__init__.py`` is
    still perfectly resolvable in its own module, and resolving against the
    package namespace instead would turn a correct demotion into a ``NameError``
    — which is to say, it would make this check pass or fail for reasons that
    have nothing to do with the rule.
    """
    namespace = dict(vars(sys.modules[module_name]))
    return typing.get_type_hints(obj, globalns=namespace)


def _walk(annotation: object, seen: set[object], reached: set[type]) -> None:
    """Collect package-defined classes in the transitive closure of a type."""
    try:
        if annotation in seen:
            return
        seen.add(annotation)
    except TypeError:  # unhashable annotation object
        pass
    for argument in typing.get_args(annotation):
        _walk(argument, seen, reached)
    if not inspect.isclass(annotation):
        return
    module = getattr(annotation, "__module__", "")
    if module != PACKAGE_NAME and not module.startswith(PACKAGE_NAME + "."):
        return
    reached.add(annotation)
    for base in annotation.__mro__[1:]:
        _walk(base, seen, reached)
    if dataclasses.is_dataclass(annotation):
        for hint in _resolve_hints(annotation, annotation.__module__).values():
            _walk(hint, seen, reached)


def _public_methods() -> list[tuple[str, object, str]]:
    client = getattr(PACKAGE, CLIENT_CLASS_NAME)
    methods: list[tuple[str, object, str]] = []
    for klass in client.__mro__:
        module = getattr(klass, "__module__", "")
        if module != PACKAGE_NAME and not module.startswith(PACKAGE_NAME + "."):
            continue
        for name, raw in vars(klass).items():
            if name.startswith("_"):
                continue
            member = raw
            if isinstance(member, (staticmethod, classmethod)):
                member = member.__func__
            elif isinstance(member, property):
                member = member.fget
            if inspect.isfunction(member):
                methods.append((name, member, module))
    return methods


def _reachable_types() -> set[type]:
    seen: set[object] = set()
    reached: set[type] = set()
    for _, method, module in _public_methods():
        for hint in _resolve_hints(method, module).values():
            _walk(hint, seen, reached)
    return reached


def test_the_per_repository_block_is_self_consistent():
    # The block above is the only hand-written part of this file, so it is the
    # only part that can name something that does not exist. A module listed
    # here but deleted from the package would silently stop enforcing anything.
    assert not (FUNCTION_EXPORTING_MODULES & DATA_EXPORTING_MODULES), (
        "a module either may export functions or may not; listing it in both "
        "makes the narrower list decorative"
    )
    on_disk = {path.stem for path in PACKAGE_DIR.glob("*.py")} - {"__init__"}
    assert EXPORTING_MODULES <= on_disk, EXPORTING_MODULES - on_disk
    assert all(reason.strip() for reason in DOMAIN_CONSTANTS.values()), (
        "a domain constant without a stated reason is an unargued export"
    )


def test_all_equals_the_import_block():
    # Demotion has two halves -- the import line and the __all__ entry -- and
    # doing one without the other is the failure mode this repository has
    # already hit. Equality of the two sets makes half a demotion impossible:
    # a leftover import shows up as an attribute nobody declared, a leftover
    # __all__ entry as a name `from pkg import *` cannot actually bind.
    assert len(EXPORTED) == len(EXPORTED_SET), sorted(
        name for name in EXPORTED_SET if EXPORTED.count(name) > 1
    )
    imported = set(_init_imports())
    assert EXPORTED_SET == imported, {
        "in __all__ but not imported": sorted(EXPORTED_SET - imported),
        "imported but not in __all__": sorted(imported - EXPORTED_SET),
    }

    # The same equality again, asked of the imported package instead of the
    # source, because `_init_imports` only sees the ONE import form this file
    # uses (`from .module import name`). A name brought in by an absolute
    # import, a plain `import x`, or an assignment would be invisible to the
    # ast walk above and still be `hasattr`-reachable -- which is precisely the
    # half-demotion `tests/test_next_variant_reads.py` asserts against by hand
    # for the two names it holds back. Stated here it holds for every name.
    # Submodules are excluded: `from .constants import X` binds `constants` as
    # an attribute as a side effect of importing it, and that is Python's doing,
    # not an export.
    residue = sorted(
        name
        for name in dir(PACKAGE)
        if not name.startswith("_")
        and name not in EXPORTED_SET
        and not inspect.ismodule(getattr(PACKAGE, name))
    )
    assert not residue, residue


def test_only_exporting_modules_reach_all():
    # The rule is stated over MODULES, not over names. A name list would have to
    # be edited every time a response dataclass is added, and an edited list is
    # a list somebody eventually edits in the wrong direction. A module list
    # only changes when the shape of the package changes.
    origin = _init_imports()
    from_internal = sorted(
        f"{name} (from {origin[name]})"
        for name in EXPORTED_SET
        if origin.get(name) not in EXPORTING_MODULES
    )
    assert not from_internal, from_internal

    # Within the modules that legitimately export request dataclasses and coded
    # domain values, functions are still out: those are the builders, encoders
    # and table generators the client calls for the caller. Narrowed to
    # module-level `def` so that exporting a dataclass from the same file stays
    # unremarkable.
    exported_functions = sorted(
        f"{name} (def in {origin[name]})"
        for name in EXPORTED_SET
        if origin.get(name) in DATA_EXPORTING_MODULES
        and name in _module_level_functions(origin[name])
    )
    assert not exported_functions, exported_functions


def test_no_parse_or_pair_helper_is_exported():
    # The client calls these itself and hands back the parsed object. Exporting
    # one publishes the seam between "we got bytes" and "we got a dataclass",
    # which is precisely the seam that has to stay free to move.
    assert not [
        name for name in EXPORTED if name.startswith(("parse_", "pair_"))
    ]


def test_every_type_a_public_method_can_hand_back_is_exported():
    # The direction that actually costs a user something. Forgetting to export
    # a response dataclass does not break `client.get_x()`; it breaks writing
    # `def handle(r: XResponse)` around it, and the user finds out only after
    # they have already written the call. Walking the closure of every public
    # method's annotations -- return types, argument types, their dataclass
    # fields, their base classes -- makes adding a method with an unexported
    # type in its signature fail here instead of in someone's type checker.
    reached = _reachable_types()
    missing = sorted(
        klass.__name__ for klass in reached if klass.__name__ not in EXPORTED_SET
    )
    assert not missing, missing

    # A closure that reached nothing would satisfy the assertion above without
    # checking anything -- the failure mode of every derived expectation. The
    # guard is derived rather than a floor: the methods found by reflection
    # must be exactly the public `def`s `ast` finds in the client class body,
    # so a renamed class or a wrong `__mro__` filter shows up as a mismatch
    # instead of as a silently empty walk.
    by_reflection = {name for name, _, _ in _public_methods()}
    client_module = getattr(PACKAGE, CLIENT_CLASS_NAME).__module__.rsplit(".", 1)[-1]
    tree = ast.parse((PACKAGE_DIR / f"{client_module}.py").read_text(encoding="utf-8"))
    by_source = {
        item.name
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == CLIENT_CLASS_NAME
        for item in node.body
        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
        and not item.name.startswith("_")
    }
    assert by_source, f"no public methods found in the source of {CLIENT_CLASS_NAME}"
    assert by_source <= by_reflection, sorted(by_source - by_reflection)
    assert reached


def test_exported_non_types_are_exactly_the_argued_domain_constants():
    # Everything else in __all__ is a class or a function and carries its own
    # docstring. A bare module-level value carries no signature, so the only
    # thing distinguishing "a code the caller compares against" from "the base
    # URL" is an argument someone made -- which is what DOMAIN_CONSTANTS is.
    # Exact equality in both directions: a new transport constant cannot drift
    # up, and a demoted one cannot be left behind in the list as a lie.
    # `typing.get_origin` is what separates a type from a value here, not
    # `inspect.isclass`: a union alias (`A | B | C`, used where the app accepts
    # several request shapes on one route) is a type a caller annotates with,
    # but it is not a class and would otherwise be demanded an argument as if
    # it were a magic number.
    constants = {
        name
        for name in EXPORTED_SET
        if not inspect.isclass(getattr(PACKAGE, name))
        and not inspect.isroutine(getattr(PACKAGE, name))
        and typing.get_origin(getattr(PACKAGE, name)) is None
    }
    assert constants == set(DOMAIN_CONSTANTS), {
        "exported without an argument": sorted(constants - set(DOMAIN_CONSTANTS)),
        "argued for but not exported": sorted(set(DOMAIN_CONSTANTS) - constants),
    }


def test_demotion_is_a_move_and_the_submodule_is_the_permanent_home():
    # Demotion is a move, not a deletion, and the checks above only constrain
    # the top level -- they would be equally satisfied by deleting a name
    # outright. What makes narrowing cheap is that `from pkg.module import
    # name` keeps working for everything that came off the top, so the rule is
    # stated over EVERY module in the package, including the ones that now
    # export nothing upward: each module's public module-level definitions must
    # be reachable as attributes of that module.
    for path in sorted(PACKAGE_DIR.glob("*.py")):
        if path.stem == "__init__":
            continue
        module = importlib.import_module(f"{PACKAGE_NAME}.{path.stem}")
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in tree.body:
            names: list[str] = []
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                names = [node.name]
            elif isinstance(node, ast.Assign):
                names = [t.id for t in node.targets if isinstance(t, ast.Name)]
            elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                names = [node.target.id]
            for name in names:
                if name.startswith("_"):
                    continue
                assert hasattr(module, name), f"{path.stem}.{name}"

    # And the names that ARE exported must resolve to the same object through
    # either path, so the submodule route is never a stale copy of the one the
    # top level hands out.
    for name, module_name in sorted(_init_imports().items()):
        module = importlib.import_module(f"{PACKAGE_NAME}.{module_name}")
        assert getattr(module, name) is getattr(PACKAGE, name), name


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(pytest.main([__file__, "-q"]))

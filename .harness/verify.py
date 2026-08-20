#!/usr/bin/env python3
"""harness verify -- deterministic verification gate.

Runs a project's quality gates and reports the truth as an exit code. Knows
nothing about any agent harness: adapters call this, never the other way round.

    0  every gate passed
    1  at least one fatal gate failed
    2  only non-fatal gates failed
    3  configuration or usage error

See docs/adr/0003-verificacion-determinista.md for why it is built this way.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python < 3.11
    tomllib = None  # type: ignore[assignment]

MANIFEST = Path(".harness") / "verify.toml"

# Per-gate output kept for the agent. Enough to diagnose, not enough to drown
# the context window -- a 4000-line pytest failure helps nobody.
OUTPUT_LIMIT = 4000

EXIT_OK = 0
EXIT_FATAL = 1
EXIT_WARN = 2
EXIT_CONFIG = 3

# Markers that identify a project root, most specific first.
ROOT_MARKERS = (
    MANIFEST,
    Path("pyproject.toml"),
    Path("go.mod"),
    Path("package.json"),
    Path("pytest.ini"),
    Path(".git"),
)

# Directories that plausibly hold first-party source, in preference order.
SOURCE_DIR_CANDIDATES = ("app", "apps", "src", "lib")

PYTHON_EXT = (".py", ".pyi")

# Momentos en los que se invoca el verificador. Quien lo llama declara cuál es.
CONTEXTS = ("edit", "turn", "push", "ci")


# --------------------------------------------------------------------- model


@dataclass
class Gate:
    """One verification step: a command whose exit code is the verdict."""

    id: str
    cmd: str
    fatal: bool = True
    # Fast single-file variant used by post-edit hooks. `{file}` is substituted
    # with the path relative to the project root. Gates without one are skipped
    # in file scope -- running the whole suite after every edit is useless.
    file_cmd: str | None = None
    description: str = ""
    # Extensiones a las que aplica `file_cmd`. Vacío = cualquiera.
    # Sin esto, `ruff check {file}` intenta parsear un .ts o un .md como Python
    # y reporta un error de sintaxis que no tiene nada que ver con el código.
    file_ext: tuple[str, ...] = ()
    # Momentos en los que este gate corre. Vacío = todos.
    #
    # Eje distinto al de las capas: las capas dicen QUÉ gates aplican según el
    # stack; `when` dice CUÁNDO se pueden correr. Un gate que necesita Postgres
    # levantado no puede correr en cada edición, pero sí en CI, que tiene
    # `services:`. Sin esta separación, un proyecto con base de datos obliga a
    # elegir entre un gate que bloquea por razones ambientales o uno que miente
    # sobre la cobertura.
    when: tuple[str, ...] = ()


@dataclass
class GateResult:
    gate: Gate
    status: str  # passed | failed | skipped
    duration_ms: int = 0
    output: str = ""
    truncated: bool = False
    reason: str = ""

    @property
    def blocking(self) -> bool:
        return self.status == "failed" and self.gate.fatal


@dataclass
class Config:
    root: Path
    stack: str
    gates: list[Gate] = field(default_factory=list)
    source: str = "manifest"  # manifest | detected


# ---------------------------------------------------------------- discovery


def find_root(start: Path) -> Path | None:
    """Walk up from `start` looking for the outermost meaningful project root.

    Stops at the first directory holding a marker. A manifest wins outright:
    if a project declares itself, that declaration is the answer.
    """
    start = start.resolve()
    candidates = [start, *start.parents]

    for directory in candidates:
        if (directory / MANIFEST).is_file():
            return directory

    for directory in candidates:
        for marker in ROOT_MARKERS:
            target = directory / marker
            if target.exists():
                return directory
    return None


def project_env(root: Path) -> dict[str, str]:
    """Environment for gate execution, with the project's venv taking priority.

    Monolith's Makefile calls `.venv/bin/ruff`, not `ruff`. A verifier that
    resolves tools from the global PATH would either use the wrong binary or
    fail -- both amount to lying about the project's state.
    """
    env = os.environ.copy()

    bin_dirs = [
        root / ".venv" / "Scripts",  # Windows
        root / ".venv" / "bin",  # POSIX
        root / "venv" / "Scripts",
        root / "venv" / "bin",
    ]
    prefix = [str(d) for d in bin_dirs if d.is_dir()]
    if prefix:
        env["PATH"] = os.pathsep.join([*prefix, env.get("PATH", "")])

    # Both reference projects run pytest with the root importable.
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = (
        os.pathsep.join([str(root), existing]) if existing else str(root)
    )
    return env


def tool_available(name: str, env: dict[str, str]) -> bool:
    return shutil.which(name, path=env.get("PATH")) is not None


# ---------------------------------------------------------------- detection


def read_toml(path: Path) -> dict[str, Any]:
    if tomllib is None or not path.is_file():
        return {}
    try:
        with path.open("rb") as handle:
            return tomllib.load(handle)
    except (OSError, ValueError):
        return {}


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def source_targets(root: Path) -> str:
    """Space-joined source dirs to hand to linters, mirroring `ruff check app tests`."""
    found = [name for name in SOURCE_DIR_CANDIDATES if (root / name).is_dir()]
    if (root / "tests").is_dir():
        found.append("tests")
    return " ".join(found) if found else "."


def detect_python(root: Path, env: dict[str, str]) -> list[Gate]:
    pyproject = read_toml(root / "pyproject.toml")
    tools = pyproject.get("tool", {}) if isinstance(pyproject, dict) else {}
    targets = source_targets(root)
    gates: list[Gate] = []

    has_ruff = bool(tools.get("ruff")) or any(
        (root / name).is_file() for name in ("ruff.toml", ".ruff.toml")
    )
    has_black = bool(tools.get("black"))

    # Formatting is reported but never blocks: it is mechanically fixable, and
    # failing an agent's whole run over whitespace trains it to ignore gates.
    if has_black and tool_available("black", env):
        gates.append(
            Gate(
                id="format",
                cmd=f"black --check {targets}",
                fatal=False,
                file_cmd="black --check {file}",
                file_ext=PYTHON_EXT,
                description="formato (black)",
            )
        )
    elif has_ruff and tool_available("ruff", env):
        gates.append(
            Gate(
                id="format",
                cmd=f"ruff format --check {targets}",
                fatal=False,
                file_cmd="ruff format --check {file}",
                file_ext=PYTHON_EXT,
                description="formato (ruff)",
            )
        )

    if has_ruff and tool_available("ruff", env):
        gates.append(
            Gate(
                id="lint",
                cmd=f"ruff check {targets}",
                fatal=True,
                file_cmd="ruff check {file}",
                file_ext=PYTHON_EXT,
                description="lint (ruff)",
            )
        )

    mypy_configured = bool(tools.get("mypy")) or any(
        (root / name).is_file() for name in ("mypy.ini", ".mypy.ini")
    )
    if mypy_configured and tool_available("mypy", env):
        mypy_targets = (
            " ".join(name for name in SOURCE_DIR_CANDIDATES if (root / name).is_dir())
            or "."
        )
        gates.append(
            Gate(
                id="types",
                cmd=f"mypy {mypy_targets}",
                fatal=True,
                file_cmd="mypy {file}",
                file_ext=PYTHON_EXT,
                description="tipos (mypy)",
            )
        )
    elif (root / "pyrightconfig.json").is_file() and tool_available("pyright", env):
        gates.append(
            Gate(id="types", cmd="pyright", fatal=True, description="tipos (pyright)")
        )

    pytest_configured = (
        (root / "pytest.ini").is_file()
        or bool(tools.get("pytest"))
        or (root / "tests").is_dir()
    )
    if pytest_configured and tool_available("pytest", env):
        gates.append(
            Gate(id="tests", cmd="pytest -q", fatal=True, description="tests (pytest)")
        )

    return gates


def detect_node(root: Path, env: dict[str, str]) -> list[Gate]:
    package = root / "package.json"
    if not package.is_file():
        return []
    try:
        scripts = json.loads(read_text(package)).get("scripts", {})
    except ValueError:
        scripts = {}

    gates: list[Gate] = []
    if "lint" in scripts:
        gates.append(
            Gate(id="lint", cmd="npm run lint", fatal=True, description="lint (npm)")
        )
    if "typecheck" in scripts:
        gates.append(
            Gate(
                id="types",
                cmd="npm run typecheck",
                fatal=True,
                description="tipos (npm)",
            )
        )
    elif (root / "tsconfig.json").is_file():
        gates.append(
            Gate(
                id="types",
                cmd="npx tsc --noEmit",
                fatal=True,
                description="tipos (tsc)",
            )
        )
    if "test" in scripts:
        gates.append(
            Gate(id="tests", cmd="npm test", fatal=True, description="tests (npm)")
        )
    return gates


def detect_go(root: Path, env: dict[str, str]) -> list[Gate]:
    if not (root / "go.mod").is_file() or not tool_available("go", env):
        return []
    return [
        Gate(
            id="format",
            cmd="gofmt -l .",
            fatal=False,
            description="formato (gofmt)",
        ),
        Gate(id="lint", cmd="go vet ./...", fatal=True, description="vet (go)"),
        Gate(id="tests", cmd="go test ./...", fatal=True, description="tests (go)"),
    ]


def detect(root: Path, env: dict[str, str]) -> Config:
    """Derive gates from what the repo actually contains.

    A starting point for generating a manifest, not a substitute for having one:
    detection is silent about tools the project meant to run but has not
    installed, which a committed manifest would catch.
    """
    for stack, detector in (
        ("python", detect_python),
        ("node", detect_node),
        ("go", detect_go),
    ):
        gates = detector(root, env)
        if gates:
            return Config(root=root, stack=stack, gates=gates, source="detected")
    return Config(root=root, stack="unknown", gates=[], source="detected")


# ------------------------------------------------------------------- config


def load_manifest(root: Path) -> Config | None:
    path = root / MANIFEST
    if not path.is_file():
        return None
    if tomllib is None:
        raise SystemExit(
            "harness verify: se necesita Python 3.11+ para leer .harness/verify.toml"
        )

    data = read_toml(path)
    project = data.get("project", {})
    gates: list[Gate] = []

    for index, raw in enumerate(data.get("gate", [])):
        gate_id = raw.get("id") or f"gate-{index + 1}"
        cmd = raw.get("cmd")
        if not cmd:
            raise SystemExit(
                f"harness verify: el gate '{gate_id}' no tiene 'cmd' en {MANIFEST}"
            )
        gates.append(
            Gate(
                id=gate_id,
                cmd=cmd,
                fatal=bool(raw.get("fatal", True)),
                file_cmd=raw.get("file_cmd"),
                file_ext=tuple(raw.get("file_ext", ())),
                when=tuple(raw.get("when", ())),
                description=raw.get("description", ""),
            )
        )

    return Config(
        root=root,
        stack=project.get("stack", "unknown"),
        gates=gates,
        source="manifest",
    )


def render_manifest(config: Config) -> str:
    lines = [
        "# Generado por `harness verify --init` a partir de lo que el proyecto",
        "# ya contiene. Editable: esta es la declaración de calidad del proyecto,",
        "# no un archivo derivado. Commitéalo.",
        "",
        "[project]",
        f'name = "{config.root.name}"',
        f'stack = "{config.stack}"',
        "",
    ]
    for gate in config.gates:
        lines.append("[[gate]]")
        lines.append(f'id = "{gate.id}"')
        if gate.description:
            lines.append(f'description = "{gate.description}"')
        lines.append(f'cmd = "{gate.cmd}"')
        if gate.file_cmd:
            lines.append(f'file_cmd = "{gate.file_cmd}"')
        if gate.file_ext:
            rendered = ", ".join(f'"{ext}"' for ext in gate.file_ext)
            lines.append(f"file_ext = [{rendered}]")
        if gate.when:
            rendered = ", ".join(f'"{moment}"' for moment in gate.when)
            lines.append(f"when = [{rendered}]")
        lines.append(f"fatal = {'true' if gate.fatal else 'false'}")
        lines.append("")
    return "\n".join(lines)


# ----------------------------------------------------------------- execution


def run_gate(
    gate: Gate, root: Path, env: dict[str, str], file: str | None
) -> GateResult:
    if file is not None:
        if not gate.file_cmd:
            return GateResult(
                gate=gate,
                status="skipped",
                reason="sin file_cmd: no aplica a un archivo suelto",
            )
        suffix = Path(file).suffix.lower()
        if gate.file_ext and suffix not in gate.file_ext:
            return GateResult(
                gate=gate,
                status="skipped",
                reason=f"no aplica a '{suffix or 'sin extensión'}'",
            )
        command = gate.file_cmd.replace("{file}", file)
    else:
        command = gate.cmd

    started = time.perf_counter()
    try:
        completed = subprocess.run(
            command,
            shell=True,
            cwd=str(root),
            env=env,
            capture_output=True,
            text=True,
            errors="replace",
        )
    except OSError as exc:
        return GateResult(
            gate=gate,
            status="failed",
            duration_ms=int((time.perf_counter() - started) * 1000),
            output=str(exc),
            reason="no se pudo ejecutar el comando",
        )

    duration_ms = int((time.perf_counter() - started) * 1000)
    combined = (completed.stdout or "") + (completed.stderr or "")
    combined = combined.strip()
    truncated = len(combined) > OUTPUT_LIMIT
    if truncated:
        combined = combined[:OUTPUT_LIMIT] + "\n... [salida truncada]"

    return GateResult(
        gate=gate,
        status="passed" if completed.returncode == 0 else "failed",
        duration_ms=duration_ms,
        output=combined,
        truncated=truncated,
    )


def run_all(
    config: Config,
    env: dict[str, str],
    file: str | None,
    fail_fast: bool,
) -> list[GateResult]:
    results: list[GateResult] = []
    for gate in config.gates:
        result = run_gate(gate, config.root, env, file)
        results.append(result)
        if fail_fast and result.blocking:
            for pending in config.gates[len(results) :]:
                results.append(
                    GateResult(
                        gate=pending,
                        status="skipped",
                        reason="fail-fast: un gate fatal anterior falló",
                    )
                )
            break
    return results


def exit_code(results: list[GateResult]) -> int:
    if any(r.blocking for r in results):
        return EXIT_FATAL
    if any(r.status == "failed" for r in results):
        return EXIT_WARN
    return EXIT_OK


# -------------------------------------------------------------------- output


ICONS = {"passed": "OK  ", "failed": "FAIL", "skipped": "--  "}


def render_human(
    config: Config,
    results: list[GateResult],
    file: str | None,
    when: str | None = None,
    verbose: bool = False,
) -> str:
    scope = f"archivo {file}" if file else "proyecto"
    moment = f" | momento {when}" if when else ""
    lines = [
        f"harness verify | {config.root.name} | {config.stack} | {scope}{moment}"
        f" | gates desde {config.source}",
        "",
    ]

    for result in results:
        gate = result.gate
        label = gate.description or gate.id
        head = f"  {ICONS[result.status]} {gate.id:<8} {label}"
        if result.status == "skipped":
            lines.append(f"{head}  ({result.reason})")
            continue
        flag = "" if gate.fatal else "  [no bloqueante]"
        lines.append(f"{head}  {result.duration_ms}ms{flag}")
        if result.output and (result.status == "failed" or verbose):
            lines.extend(f"      {line}" for line in result.output.splitlines())

    failed = [r for r in results if r.status == "failed"]
    blocking = [r for r in failed if r.gate.fatal]
    lines.append("")
    if blocking:
        names = ", ".join(r.gate.id for r in blocking)
        lines.append(f"FAIL  gates fatales fallando: {names}")
    elif failed:
        names = ", ".join(r.gate.id for r in failed)
        lines.append(f"WARN  gates no bloqueantes fallando: {names}")
    else:
        ran = sum(1 for r in results if r.status != "skipped")
        lines.append(f"OK    {ran} gate(s) pasaron")
    return "\n".join(lines)


def render_json(
    config: Config, results: list[GateResult], file: str | None, when: str | None = None
) -> str:
    return json.dumps(
        {
            "ok": exit_code(results) == EXIT_OK,
            "root": str(config.root),
            "stack": config.stack,
            "scope": "file" if file else "project",
            "file": file,
            "when": when,
            "gates_from": config.source,
            "gates": [
                {
                    "id": r.gate.id,
                    "cmd": r.gate.file_cmd if file else r.gate.cmd,
                    "fatal": r.gate.fatal,
                    "status": r.status,
                    "duration_ms": r.duration_ms,
                    "output": r.output,
                    "truncated": r.truncated,
                    "reason": r.reason,
                }
                for r in results
            ],
            "summary": {
                "passed": sum(1 for r in results if r.status == "passed"),
                "failed": sum(1 for r in results if r.status == "failed"),
                "skipped": sum(1 for r in results if r.status == "skipped"),
                "blocking": [r.gate.id for r in results if r.blocking],
            },
        },
        indent=2,
        ensure_ascii=False,
    )


# ---------------------------------------------------------------------- main


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="harness verify",
        description="Gate de verificación determinista. El exit code es el contrato.",
    )
    parser.add_argument("--root", default=".", help="raíz del proyecto (default: cwd)")
    parser.add_argument(
        "--file",
        help="verificar un solo archivo: corre únicamente los gates con file_cmd",
    )
    parser.add_argument(
        "--init",
        action="store_true",
        help="escribir .harness/verify.toml desde la detección y salir",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="con --init, regenerar aunque el manifiesto ya exista",
    )
    parser.add_argument(
        "--json", action="store_true", help="salida legible por máquina"
    )
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="detenerse en el primer gate fatal (default: correr todos)",
    )
    parser.add_argument(
        "--only",
        help="correr sólo estos gates, separados por coma (ej: lint,types)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help=(
            "mostrar también la salida de los gates que pasan. Un gate de "
            "cobertura que pasa igual esconde el número, que suele ser el dato "
            "que se necesita"
        ),
    )
    parser.add_argument(
        "--when",
        choices=CONTEXTS,
        help=(
            "momento desde el que se invoca: corre sólo los gates que aplican. "
            "Sin esto corren todos."
        ),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    # Gate output carries whatever encoding the underlying tools emit. A Windows
    # console defaulting to cp1252 would raise mid-report and lose the verdict.
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            with contextlib.suppress(OSError, ValueError):
                reconfigure(encoding="utf-8", errors="replace")

    args = build_parser().parse_args(argv)

    root = find_root(Path(args.root))
    if root is None:
        start = Path(args.root).resolve()
        print(
            f"harness verify: no se encontró raíz de proyecto desde {start}",
            file=sys.stderr,
        )
        return EXIT_CONFIG

    env = project_env(root)

    if args.init:
        # `--init` deriva de la evidencia del repo, siempre. Leer el manifiesto
        # existente y volver a escribirlo sería un no-op disfrazado que congela
        # los errores de la versión anterior.
        config = detect(root, env)
        if not config.gates:
            print(
                f"harness verify: no se detectó ningún gate en {root}; nada que escribir",
                file=sys.stderr,
            )
            return EXIT_CONFIG
        target = root / MANIFEST
        if target.is_file() and not args.force:
            print(
                f"harness verify: {target} ya existe. Es la declaración de calidad "
                "del proyecto, no un archivo derivado: usa --force si de verdad "
                "quieres regenerarlo desde la detección.",
                file=sys.stderr,
            )
            return EXIT_CONFIG
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(render_manifest(config), encoding="utf-8")
        print(f"harness verify: escrito {target} con {len(config.gates)} gate(s)")
        return EXIT_OK

    loaded = load_manifest(root)
    config = loaded if loaded is not None else detect(root, env)

    if args.only:
        wanted = {name.strip() for name in args.only.split(",") if name.strip()}
        unknown = wanted - {gate.id for gate in config.gates}
        if unknown:
            print(
                f"harness verify: gates desconocidos: {', '.join(sorted(unknown))}",
                file=sys.stderr,
            )
            return EXIT_CONFIG
        config.gates = [gate for gate in config.gates if gate.id in wanted]

    if args.when:
        # Un gate sin `when` corre en todos los momentos: declarar la
        # restricción es opt-in, igual que el resto del harness.
        config.gates = [
            gate for gate in config.gates if not gate.when or args.when in gate.when
        ]

    if not config.gates:
        print(
            f"harness verify: no hay gates para {root}. "
            f"Declara los tuyos en {MANIFEST} o corre --init.",
            file=sys.stderr,
        )
        return EXIT_CONFIG

    file_arg = None
    if args.file is not None:
        # An empty --file must not silently degrade to project scope: the caller
        # asked about one file and deserves an error, not a different answer.
        if not args.file.strip():
            print("harness verify: --file recibió una ruta vacía", file=sys.stderr)
            return EXIT_CONFIG
        candidate = Path(args.file)
        resolved = candidate if candidate.is_absolute() else (Path.cwd() / candidate)
        try:
            file_arg = str(resolved.resolve().relative_to(root))
        except ValueError:
            # Outside the project root: nothing this project's gates can say.
            print(
                f"harness verify: {args.file} está fuera de {root}; nada que verificar",
                file=sys.stderr,
            )
            return EXIT_OK

    results = run_all(config, env, file_arg, args.fail_fast)

    if args.json:
        print(render_json(config, results, file_arg, args.when))
    else:
        print(
            render_human(config, results, file_arg, args.when, args.verbose),
            file=sys.stderr,
        )

    return exit_code(results)


if __name__ == "__main__":
    sys.exit(main())

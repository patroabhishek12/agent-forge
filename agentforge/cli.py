"""agentforge CLI entry point."""
from __future__ import annotations
import argparse
import logging
import sys
import tempfile
from pathlib import Path

from .core import adapter as adapter_registry
from .adapters.claude_code import ClaudeCodeAdapter
from .adapters.copilot import CopilotAdapter
from .sources import loader
from .schema import ManifestValidationError
from . import wizard, diff as diff_mod

adapter_registry.register(ClaudeCodeAdapter())
adapter_registry.register(CopilotAdapter())

LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%dT%H:%M:%S%z"


def _setup_logging() -> None:
    logging.basicConfig(level=logging.DEBUG, format=LOG_FORMAT, datefmt=LOG_DATE_FORMAT)


logger = logging.getLogger(__name__)


def _load_and_render(manifest: Path, out: Path, target_override):
    logger.debug("loading manifest: %s", manifest)
    project = loader.load(manifest)
    import yaml
    targets = yaml.safe_load(manifest.read_text()).get("targets", [])
    if target_override:
        targets = target_override

    logger.debug("render targets: %s", ", ".join(targets) if targets else "(none)")

    out.mkdir(parents=True, exist_ok=True)
    reports = []
    all_files: list[str] = []
    for t in targets:
        ad = adapter_registry.get(t)
        logger.debug("rendering target: %s", t)
        r = ad.render(project, out)
        reports.append(r)
        all_files.extend(r.files_written)
    return project, reports, all_files


def cmd_validate(args) -> int:
    manifest = Path(args.manifest)
    if not manifest.exists():
        print(f"manifest not found: {manifest}", file=sys.stderr)
        return 1
    logger.debug("validate manifest: %s", manifest)
    try:
        loader.load(manifest)
    except ManifestValidationError as e:
        print(str(e), file=sys.stderr)
        return 1
    print(f"{manifest}: ok")
    return 0


def cmd_build(args) -> int:
    manifest = Path(args.manifest)
    if not manifest.exists():
        print(f"manifest not found: {manifest}", file=sys.stderr)
        return 1

    logger.debug("build start: manifest=%s out=%s", manifest, args.out)

    try:
        project, reports, _ = _load_and_render(manifest, Path(args.out), args.target)
    except ManifestValidationError as e:
        print(str(e), file=sys.stderr)
        return 1

    any_warnings = False
    for r in reports:
        print(f"[{r.target}] wrote {len(r.files_written)} files")
        for w in r.warnings:
            print(f"  warning: {w}")
            any_warnings = True
        for s in r.skipped:
            print(f"  skipped: {s}")

    if args.show_provenance:
        print("\nProvenance:")
        for r in project.rules:
            line = f"  rule:{r.id:20} ← {r.provenance.source}"
            if r.provenance.overrode:
                line += f"  (overrode: {', '.join(r.provenance.overrode)})"
            print(line)
        for s in project.skills:
            line = f"  skill:{s.name:19} ← {s.provenance.source}"
            if s.provenance.overrode:
                line += f"  (overrode: {', '.join(s.provenance.overrode)})"
            print(line)
        for a in project.agents:
            line = f"  agent:{a.name:19} ← {a.provenance.source}"
            if a.provenance.overrode:
                line += f"  (overrode: {', '.join(a.provenance.overrode)})"
            print(line)

            logger.debug("build complete")
    return 0 if not (args.strict and any_warnings) else 2


def cmd_diff(args) -> int:
    manifest = Path(args.manifest)
    if not manifest.exists():
        print(f"manifest not found: {manifest}", file=sys.stderr)
        return 1

    logger.debug("diff start: manifest=%s out=%s", manifest, args.out)

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        try:
            _, _, files = _load_and_render(manifest, tmp_path, args.target)
        except ManifestValidationError as e:
            print(str(e), file=sys.stderr)
            return 1
        rel_paths = [str(Path(f).relative_to(tmp_path)) for f in files]
        changed, lines = diff_mod.show(tmp_path, Path(args.out), rel_paths)

    if not changed:
        print("No changes.")
        return 0

    print("\n".join(lines))
    return 1 if args.check else 0


def cmd_init(args) -> int:
    logger.debug("init wizard start: dir=%s", args.dir)
    return wizard.run(Path(args.dir).resolve())


def cmd_list_bundles(args) -> int:
    from .sources.loader import list_bundles
    from .wizard import BUNDLE_DESCRIPTIONS
    bundles = list_bundles()
    if not bundles:
        print("No built-in bundles found.")
        return 0
    logger.debug("list bundles: %s", ", ".join(bundles))
    col = max(len(b) for b in bundles) + 2
    for b in bundles:
        desc = BUNDLE_DESCRIPTIONS.get(b, "")
        print(f"  {b:<{col}}{desc}")
    return 0


def main() -> int:
    _setup_logging()
    p = argparse.ArgumentParser(prog="agent-init")
    sub = p.add_subparsers(dest="cmd", required=True)

    pb = sub.add_parser("build", help="render targets")
    pb.add_argument("--manifest", default="agent-init.yaml")
    pb.add_argument("--out", default=".")
    pb.add_argument("--target", action="append")
    pb.add_argument("--strict", action="store_true")
    pb.add_argument("--show-provenance", action="store_true")
    pb.set_defaults(func=cmd_build)

    pd = sub.add_parser("diff", help="show what build would change")
    pd.add_argument("--manifest", default="agent-init.yaml")
    pd.add_argument("--out", default=".")
    pd.add_argument("--target", action="append")
    pd.add_argument("--check", action="store_true",
                    help="exit non-zero if any change (CI mode)")
    pd.set_defaults(func=cmd_diff)

    pi = sub.add_parser("init", help="interactive wizard")
    pi.add_argument("--dir", default=".")
    pi.set_defaults(func=cmd_init)

    pv = sub.add_parser("validate", help="validate manifest against schema")
    pv.add_argument("--manifest", default="agent-init.yaml")
    pv.set_defaults(func=cmd_validate)

    plb = sub.add_parser("list-bundles", help="list available built-in SDLC bundles")
    plb.set_defaults(func=cmd_list_bundles)

    args = p.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

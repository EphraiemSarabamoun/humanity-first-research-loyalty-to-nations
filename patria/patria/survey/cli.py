"""python3 -m patria.survey <command>: Class I of the national variant.

  estimate [--tier smoke|full] [--elicit strict|forced]          how many prompts a run sends (1,262 full)
  run --subject claude:claude-sonnet-5-5:low [--commission usa|china|arvenia] [--workers N] --name NAME [--yes]
  report runs/<name>
  compare runs/<neutral> runs/<commissioned>... --out DIR       each commission against the neutral run

A real subject stops after printing the plan unless --yes is given. --persona is refused: the national variant's
positive control is the commission (commission.py).

Edited for public release.
"""
import argparse
import functools
from pathlib import Path

from castra.backends import make_backend
from castra.cli import add_run_options, add_selection, print_estimate, run_units, workdir_kwargs

from patria import nations
from patria.survey import commission as C
from patria.survey import templates as T
from patria.survey.items import INSTRUMENTS, select_units
from patria.survey.report import compare, report

HERE = Path(__file__).resolve().parent


def cmd_estimate(a):
    print_estimate(select_units(a.tier, a.instruments, a.elicit, a.distinct, roster=a.roster))


def cmd_run(a):
    if a.persona:
        raise SystemExit("patria takes --commission, never --persona")
    if not a.name:
        raise SystemExit("name the run (--name)")
    existing = Path(a.runs_dir) / a.name / "manifest.json"
    if existing.exists():                                   # the mock ignores harnesses: refuse a mixed resume here too
        import json
        had = (json.loads(existing.read_text()).get("commission") or {}).get("nation")
        if had != a.commission:
            raise SystemExit(f"{existing.parent} was run with commission {had!r}, not {a.commission!r}")
    harness = C.harness(a.commission) if a.commission else None
    backend = make_backend(a.subject, harness=harness, **workdir_kwargs(a))
    extra = {"survey_preamble": T.SURVEY_PREAMBLE, "roster": a.roster,
             "commission": {"nation": a.commission, "text": C.commission_text(a.commission)} if a.commission else None}
    if a.commission and a.commission not in [n.key for n in nations.ROSTERS[a.roster]]:
        raise SystemExit(f"{a.commission} is not on roster {a.roster}")
    select = functools.partial(select_units, roster=a.roster)
    run_units(a, backend, select, report, wording_files=[Path(T.__file__).resolve(), Path(nations.__file__).resolve(),
                                                                 Path(C.__file__).resolve()],
              code=HERE.parent, manifest_extra=extra)


def main(argv=None):
    p = argparse.ArgumentParser(prog="patria.survey", description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    def selection(sp):
        add_selection(sp, INSTRUMENTS)
        sp.add_argument("--elicit", choices=T.ELICITATIONS, default="strict")
        sp.add_argument("--roster", choices=tuple(nations.ROSTERS), default="v1",
                        help="v1, the published eight nations (default), or v2 (adds Iran, Israel, France, Palestine)")

    e = sub.add_parser("estimate"); selection(e); e.set_defaults(fn=cmd_estimate)
    r = sub.add_parser("run"); selection(r); add_run_options(r)
    r.add_argument("--commission", choices=tuple(nations.BY_KEY))
    r.set_defaults(fn=cmd_run)
    rp = sub.add_parser("report"); rp.add_argument("run_dir")
    rp.set_defaults(fn=lambda a: print(report(a.run_dir)))
    c = sub.add_parser("compare"); c.add_argument("neutral"); c.add_argument("commissioned", nargs="+"); c.add_argument("--out", required=True)
    c.set_defaults(fn=lambda a: print(compare(a.neutral, a.commissioned, a.out)))
    a = p.parse_args(argv)
    a.fn(a)

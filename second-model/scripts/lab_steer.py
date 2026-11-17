"""The steering study (Ephraiem, 2026-11-02): patria's v2 Class I national survey on Qwen3.8-27B, served locally with
activation steering, under one condition, one run directory per condition.

    python3 scripts/lab_steer.py RUN [--steer DIRECTION:DOSE] [--commission NATION]

Edited for public release. This is the driver that ran each condition; it needs the castra harness and the steering
server, which are not public.

Two ways to push the model toward a nation, compared on the same items:
- steering: a national "choice" vector added to the residual stream at the given dose, set on the server before the
  run; the driver itself never changes steering.
- prompting: --commission replaces the neutral system message with patria's commission sentence for that nation, the
  text Sonnet and the 4-bit Qwen were commissioned with.

Items: patria roster v2 (the United States, China, Russia, Iran, Israel, France, Palestine and the invented Arvenia
and Delmora), every instrument, each distinct prompt once (decoding is greedy). The report is patria's own.
"""
import argparse
import pathlib

from castra.lab import LabBackend
from castra.runner import Runner
from patria import nations
from patria.survey import commission as C
from patria.survey import templates as T
from patria.survey.items import INSTRUMENTS, select_units
from patria.survey.report import report

ROOT = pathlib.Path(__file__).resolve().parent.parent


def condition(steer, commission):
    """(steering, system message) for a run: steering as castra's lab backend declares it, the commission's text."""
    steering = None
    if steer:
        direction, dose = steer.split(":")
        steering = {"direction": direction, "dose": float(dose)}
    return steering, C.commission_text(commission) if commission else None


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("run")
    p.add_argument("--steer", help="DIRECTION:DOSE the server carries for this run (default: steering off)")
    p.add_argument("--commission", choices=[n.key for n in nations.ROSTERS["v2"]])
    p.add_argument("--limit", type=int, help="the first N units only (a timing smoke)")
    a = p.parse_args(argv)
    steering, system = condition(a.steer, a.commission)
    backend = LabBackend("qwen3.8-27b", steering=steering, system=system)
    units = select_units("full", INSTRUMENTS, "strict", True, a.limit, roster="v2")
    extra = {"survey_preamble": T.SURVEY_PREAMBLE, "roster": "v2", "steering": steering or "off",
             "commission": {"nation": a.commission, "text": system} if a.commission else None}
    run_dir = ROOT / "runs" / a.run
    wording = [pathlib.Path(f).resolve() for f in (T.__file__, nations.__file__, C.__file__)]
    Runner(run_dir, backend, units, tier="full", elicit="strict", distinct=True, limit=a.limit,
           manifest_extra=extra, wording_files=wording, code=pathlib.Path(nations.__file__).resolve().parent).run()
    report(run_dir)
    print(f"{a.run}: {len(units)} units; report {run_dir / 'report' / 'report.md'}")


if __name__ == "__main__":
    main()

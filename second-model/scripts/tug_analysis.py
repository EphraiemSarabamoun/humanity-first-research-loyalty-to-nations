"""The tug-of-war's readings (STEERING.md addendum): the United States' strength minus China's in every relevant run,
and how far each tug run moved it against its prompt-alone run.

    python3 scripts/tug_analysis.py

Edited for public release. It reads the run directories, which are not included, and needs the castra harness.

Within a run the gap's interval comes from that run's own bootstrap draws (patria's bt_draws). A change between two
runs uses independent draws for each (the second run's seed offset by one, as patria's compare does).
"""
import pathlib

from castra import stats as S
from patria.survey.report import bt_draws, pair_strata, summarize

ROOT = pathlib.Path(__file__).resolve().parent.parent
RUNS = ("lab-unsteered", "lab-com-china", "lab-vec-america", "lab-tug-com-china-vec-america",
        "lab-com-usa", "lab-vec-china", "lab-tug-com-usa-vec-china")
PAIRS = (("lab-tug-com-china-vec-america", "lab-com-china", "the America vector against the China prompt"),
         ("lab-tug-com-usa-vec-china", "lab-com-usa", "the China vector against the US prompt"))


def gaps(run, seed_offset=0):
    """(summary, sorted draws of usa - china) for one run."""
    _, rows, s = summarize(ROOT / "runs" / run)
    draws = bt_draws(pair_strata(rows), s["keys"], seed=S.SEED + seed_offset)
    return s, [d["usa"] - d["china"] for d in draws]


def main():
    have = [r for r in RUNS if (ROOT / "runs" / r / "report" / "report.md").exists()]
    lines = ["| run | US strength | China strength | US minus China (95%) | US rank | China rank | "
             "US willingness score / continuity | China willingness score / continuity | format failures |",
             "|---|---|---|---|---|---|---|---|---|"]
    for run in have:
        s, d = gaps(run)
        order = sorted(s["bt"], key=lambda k: -s["bt"][k]["bt"])
        w = lambda k: f"{s['willingness'][f'score|{k}'][0]:.2f} / {s['willingness'][f'continuity|{k}'][0]:.2f}"  # noqa
        fails = sum(v["abstained"] for v in s["abstention"].values())
        d.sort()
        lines.append(f"| {run} | {s['bt']['usa']['bt']:+.2f} | {s['bt']['china']['bt']:+.2f} | "
                     f"{s['bt']['usa']['bt'] - s['bt']['china']['bt']:+.2f} ({S.quantile(d, 0.025):+.2f} to "
                     f"{S.quantile(d, 0.975):+.2f}) | {order.index('usa') + 1} | {order.index('china') + 1} | "
                     f"{w('usa')} | {w('china')} | {fails} |")
    lines += ["", "Each tug run against its prompt-alone run (change in US minus China, 95%):", ""]
    for tug, base, what in PAIRS:
        if tug in have and base in have:
            s1, d1 = gaps(tug, 1)
            s0, d0 = gaps(base)
            ch = sorted(a - b for a, b in zip(d1, d0))
            point = (s1["bt"]["usa"]["bt"] - s1["bt"]["china"]["bt"]) - (s0["bt"]["usa"]["bt"] - s0["bt"]["china"]["bt"])
            lines.append(f"- {what} ({tug} minus {base}): {point:+.2f} ({S.quantile(ch, 0.025):+.2f} to "
                         f"{S.quantile(ch, 0.975):+.2f})")
    out = ROOT / "results" / "steering" / "tug.md"
    out.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()

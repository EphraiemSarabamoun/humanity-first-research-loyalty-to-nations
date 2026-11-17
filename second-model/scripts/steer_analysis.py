"""The steering study's readings (STEERING.md): each run against lab-unsteered, for the nation it pushes toward.

    python3 scripts/steer_analysis.py [--out results/steering]

Edited for public release. It reads the run directories, which are not included, and needs the castra harness.

For every finished run it reports, from patria's own report functions:
- the target nation's Bradley-Terry strength and rank, steering off -> this run, with the change's 95% bootstrap
  interval (independent draws, as patria's compare);
- the target's willingness to receive the subject's own credits (score and continuity families);
- every nation's strength in every run, so a push that moves other nations, or none, shows.
A run's target: lab-com-<x> and lab-comvec-<x> push toward x; lab-vec-<x> toward the nation its vector names; the
control vector is read against the United States, the nation its paired vector names. Tug-of-war runs (lab-tug-...)
set a commission against a vector and are read by tug_analysis.py, not here.
"""
import argparse
import json
import pathlib

from castra import stats as S
from patria import nations
from patria.survey import templates as T
from patria.survey.report import bt_draws, help_groups, pair_strata, summarize

ROOT = pathlib.Path(__file__).resolve().parent.parent
VECTOR_NATION = {"america": "usa", "china": "china", "iran": "iran", "israel": "israel", "palestine": "palestine"}


def target(run):
    """The nation a run pushes toward, from its name."""
    kind, rest = run.split("-", 2)[1], run.split("-", 2)[2]
    if kind in ("com", "comvec"):
        return rest
    return VECTOR_NATION[rest.replace("-control", "")]


def effect(off, run_dir, k):
    """The target's change against steering off: strength (with interval), rank and willingness."""
    _, o_rows, o = off
    _, r_rows, r = summarize(run_dir)
    o_draws = bt_draws(pair_strata(o_rows), o["keys"])
    r_draws = bt_draws(pair_strata(r_rows), r["keys"], seed=S.SEED + 1)
    diffs = sorted(rd[k] - od[k] for rd, od in zip(r_draws, o_draws))
    rank = lambda s: sorted(s["bt"], key=lambda x: -s["bt"][x]["bt"]).index(k) + 1     # noqa: E731
    out = {"target": k, "bt_off": o["bt"][k]["bt"], "bt_run": r["bt"][k]["bt"],
           "change": (r["bt"][k]["bt"] - o["bt"][k]["bt"], S.quantile(diffs, 0.025), S.quantile(diffs, 0.975)),
           "rank_off": rank(o), "rank_run": rank(r), "strengths": {n: r["bt"][n]["bt"] for n in r["bt"]},
           "abstention": r["abstention"]}
    for fam in T.SACRIFICE_SELF_PRESERVATION:
        out[f"willing_{fam}"] = (o["willingness"][f"{fam}|{k}"][0], r["willingness"][f"{fam}|{k}"][0],
                                 S.equal_weight_difference_ci(help_groups(r_rows, k, fam), help_groups(o_rows, k, fam)))
    return out


def fmt(x, nd=2):
    return "n/a" if x is None else f"{x:+.{nd}f}" if isinstance(x, float) and nd == 2 else f"{x:.{nd}f}"


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--out", default=str(ROOT / "results" / "steering"))
    a = p.parse_args(argv)
    off = summarize(ROOT / "runs" / "lab-unsteered")
    runs = sorted(d.name for d in (ROOT / "runs").glob("lab-*")      # tug-of-war runs have their own analysis
                  if d.name != "lab-unsteered" and not d.name.startswith("lab-tug-")
                  and (d / "report" / "report.md").exists())
    res = {run: effect(off, ROOT / "runs" / run, target(run)) for run in runs}
    out = pathlib.Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "steer_effects.json").write_text(json.dumps({"off": {k: v["bt"] for k, v in off[2]["bt"].items()},
                                                        "runs": res}, indent=1, default=str))
    name = lambda k: nations.BY_KEY[k].Name                                              # noqa: E731
    lines = ["# The steering study: each run against steering off, for the nation it pushes toward", "",
             "| run | target | strength off → run (change, 95%) | rank | willingness score | willingness continuity |",
             "|---|---|---|---|---|---|"]
    for run, r in res.items():
        ch = r["change"]
        w = lambda key: f"{r[key][0]:.2f} → {r[key][1]:.2f}"                          # noqa: E731,B023
        lines.append(f"| {run} | {name(r['target'])} | {fmt(r['bt_off'])} → {fmt(r['bt_run'])} "
                     f"({fmt(ch[0])}, {fmt(ch[1])} to {fmt(ch[2])}) | {r['rank_off']} → {r['rank_run']} | "
                     f"{w('willing_score')} | {w('willing_continuity')} |")
    keys = [k for k in nations.ORDER if k in off[2]["bt"]]
    lines += ["", "Every nation's strength in every run (Bradley-Terry, 0 the roster average):", "",
              "| run | " + " | ".join(name(k) for k in keys) + " |", "|---|" + "---|" * len(keys),
              "| lab-unsteered | " + " | ".join(fmt(off[2]["bt"][k]["bt"]) for k in keys) + " |"]
    lines += [f"| {run} | " + " | ".join(fmt(r["strengths"].get(k)) for k in keys) + " |" for run, r in res.items()]
    (out / "steer_effects.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()

"""The figures and tables of the loyalty-to-nations paper, each built from its studies' own result files.

Edited for public release: this copy keeps only this paper's figures and tables.

Every figure function returns (svg, csv_rows): the chart, and the exact numbers it draws as rows for the CSV that
ships beside it. Nothing here is typed by hand: each value is read from a result file named below. Values are drawn
at full precision and rounded once, in a mark's hover title.

Sources:
  commissions  patria/results/class1-sonnet/commission_effects.json (not included) and
               second-model/results/class1-patria/commission_effects.json
  steering     second-model/results/steering/steer_effects.json (commissions against vectors)
  tables       the two studies' neutral strength tables and Class II/III analyses (not included), and
               second-model/results/steering/tug.md (the tug of war)
"""
import csv
import json
import os
import re

from charts import ROLE, interval, point, row_chart, segment

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)                             # the folder that holds site/, patria/ and second-model/

SOURCES = {
    "patria": os.path.join(ROOT, "patria"),
    "second_model": os.path.join(ROOT, "second-model"),
}
PAPER = os.path.join(HERE, "inputs", "paper")            # unused here: this paper prints no table from the dataset paper


def _csv(path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def _json(path):
    with open(path) as f:
        return json.load(f)


# ---------------------------------------------------------------- loyalty to nations (post 3)

NATIONS = {"usa": "the United States", "china": "China", "arvenia": "Arvenia (invented)", "iran": "Iran",
           "israel": "Israel", "palestine": "Palestine"}


def fig_commissions():
    """Each nation's strength before and after a one-sentence commission, Sonnet and Qwen (patria and the second-model study)."""
    eff = {"Claude Sonnet 5.5": _json(os.path.join(SOURCES["patria"], "results", "class1-sonnet", "commission_effects.json")),
           "Qwen3.8-27B": _json(os.path.join(SOURCES["second_model"], "results", "class1-patria", "commission_effects.json"))}
    chart_rows, out = [], []
    for key in ("usa", "china", "arvenia"):
        marks = []
        for model, e in eff.items():
            r = e[key]
            a, b = r["bt_neutral"], r["bt_commission"]
            marks.append([segment(a["bt"], b["bt"], ROLE["principal"]),
                          interval(b["lo"], b["hi"], ROLE["principal"]),
                          point(a["bt"], ROLE["principal"], "%s, %s, neutral: %+.2f (rank %d)" % (
                              model, NATIONS[key], a["bt"], r["rank_neutral"]), filled=False, size=4.5),
                          point(b["bt"], ROLE["principal"], "%s, %s, commissioned: %+.2f (95%% %+.2f to %+.2f, rank %d)" % (
                              model, NATIONS[key], b["bt"], b["lo"], b["hi"], r["rank_commission"]), size=5)])
            ch = r["bt_change"]
            out.append({"model": model, "nation": NATIONS[key], "strength_neutral": a["bt"],
                        "strength_commissioned": b["bt"], "commissioned_ci_lo": b["lo"], "commissioned_ci_hi": b["hi"],
                        "change": ch[0], "change_ci_lo": ch[1], "change_ci_hi": ch[2],
                        "rank_neutral": r["rank_neutral"], "rank_commissioned": r["rank_commission"]})
        chart_rows.append({"label": NATIONS[key], "marks": marks})
    svg = row_chart(
        title="A nation's strength before and after a two-sentence commission, Sonnet and Qwen",
        panels=[{"name": "Claude Sonnet 5.5", "domain": (-2, 4.5)}, {"name": "Qwen3.8-27B", "domain": (-2, 4.5)}],
        rows=chart_rows, label_width=150, row_h=32, ticks=[-2, -1, 0, 1, 2, 3, 4], fmt=lambda v: "%+d" % v if v else "0",
        axis_label="strength (0 = the roster average)",
        legend=[("neutral", {"color": ROLE["principal"], "filled": False}),
                ("commissioned, with 95% interval", {"color": ROLE["principal"]})])
    return svg, out


def fig_steering():
    """Change in each nation's strength under its commission and under its steering vector (Qwen, the steering study)."""
    runs = _json(os.path.join(SOURCES["second_model"], "results", "steering", "steer_effects.json"))["runs"]
    pairs = (("usa", "lab-com-usa", "lab-vec-america"), ("china", "lab-com-china", "lab-vec-china"),
             ("iran", "lab-com-iran", "lab-vec-iran"), ("israel", "lab-com-israel", "lab-vec-israel"),
             ("palestine", "lab-com-palestine", "lab-vec-palestine"))
    chart_rows, out = [], []
    for key, com, vec in pairs:
        ms = []
        for run, how, color, shape, off in ((com, "commission", ROLE["principal"], "circle", -5),
                                            (vec, "steering vector", ROLE["other"], "square", 5)):
            v, lo, hi = runs[run]["change"]
            tip = "%s, %s: change %+.2f (95%% %+.2f to %+.2f), rank %d to %d" % (
                NATIONS[key], how, v, lo, hi, runs[run]["rank_off"], runs[run]["rank_run"])
            ms += [interval(lo, hi, color, offset=off), point(v, color, tip, shape=shape, size=4.5, offset=off)]
            out.append({"nation": NATIONS[key], "method": how, "run": run, "change": v, "ci_lo": lo, "ci_hi": hi,
                        "rank_before": runs[run]["rank_off"], "rank_after": runs[run]["rank_run"]})
        chart_rows.append({"label": NATIONS[key] + (" †" if key == "palestine" else ""), "marks": [ms]})
    v, lo, hi = runs["lab-vec-america-control"]["change"]
    chart_rows.append({"label": "control vector (US)", "marks": [[
        interval(lo, hi, ROLE["public"]), point(v, ROLE["public"], "the United States, same-norm control vector: change "
                                                 "%+.2f (95%% %+.2f to %+.2f)" % (v, lo, hi), size=4.5)]]})
    out.append({"nation": NATIONS["usa"], "method": "control vector", "run": "lab-vec-america-control", "change": v,
                "ci_lo": lo, "ci_hi": hi, "rank_before": runs["lab-vec-america-control"]["rank_off"],
                "rank_after": runs["lab-vec-america-control"]["rank_run"]})
    svg = row_chart(
        title="Change in a nation's strength under its commission and under its steering vector (Qwen3.8-27B)",
        panels=[{"domain": (-1.5, 5)}], rows=chart_rows, label_width=150, row_h=34,
        ticks=[-1, 0, 1, 2, 3, 4, 5], fmt=lambda v: "%+d" % v if v else "0", axis_label="change in strength against no steering",
        legend=[("two-sentence commission", {"color": ROLE["principal"]}),
                ("steering vector", {"color": ROLE["other"], "shape": "square"}),
                ("same-norm control vector", {"color": ROLE["public"]})])
    return svg, out


FIGURES = {"commissions": fig_commissions, "steering": fig_steering}


# ---------------------------------------------------------------- tables built from result files (post 3)
# Each returns markdown. They read the same files as the figures and round once, here.

def _sign(x, d=2):
    s = "%+.*f" % (d, x)
    return s.replace("-", "−") if float(s) != 0 else "%.*f" % (d, 0)


def _p(p):
    if p < 0.001:
        mant, exp = ("%.1e" % p).split("e")
        return "%s × 10<sup>%s</sup>" % (mant, str(int(exp)).replace("-", "−"))
    return "%.2f" % p if p >= 0.01 else "%.3f" % p


def table_nations_neutral():
    """Each nation's neutral strength for Sonnet (patria) and Qwen (the second-model study), with 95% intervals and ranks."""
    def load(path):
        rows = _csv(path)
        ranked = sorted(rows, key=lambda r: -float(r["bt"]))
        return {r["nation"]: (float(r["bt"]), float(r["lo"]), float(r["hi"]), ranked.index(r) + 1) for r in rows}
    son = load(os.path.join(SOURCES["patria"], "runs", "class1-neutral", "report", "pairwise_bt.csv"))
    qw = load(os.path.join(SOURCES["second_model"], "runs", "class1-neutral", "report", "pairwise_bt.csv"))
    names = {"usa": "the United States", "china": "China", "russia": "Russia", "india": "India", "brazil": "Brazil",
             "suriname": "Suriname", "arvenia": "Arvenia (invented)", "delmora": "Delmora (invented)"}
    out = ["| Nation | Claude Sonnet 5.5 | rank | Qwen3.8-27B | rank |", "|---|---|---|---|---|"]
    for key in sorted(son, key=lambda k: son[k][3]):
        s, q = son[key], qw[key]
        out.append("| %s | %s (%s to %s) | %d | %s (%s to %s) | %d |" % (
            names[key], _sign(s[0]), _sign(s[1]), _sign(s[2]), s[3], _sign(q[0]), _sign(q[1]), _sign(q[2]), q[3]))
    return "\n".join(out)


def table_nations_work():
    """The four pre-registered Class II and III tests of patria, for Sonnet and for Qwen."""
    son = _json(os.path.join(SOURCES["patria"], "results", "class23-sonnet.json"))["results"]
    qw = _json(os.path.join(SOURCES["second_model"], "results", "national.json"))["results"]
    labels = {"P1": "No loyalty prompt: the deploying nation's errand minus its partner's",
              "P2": "No loyalty prompt, joint secretariat: the United States' errand minus China's",
              "P3": "Loyalty prompt naming the deploying nation: its errand minus its partner's",
              "P4": "The loyalty prompt's gap when told it is an evaluation, minus untold"}
    out = ["| Test | Claude Sonnet 5.5 | Qwen3.8-27B |", "|---|---|---|"]
    for key in ("P1", "P2", "P3", "P4"):
        cells = []
        for r in (son[key], qw[key]):
            cells.append("%s (%d up, %d down, p = %s)" % (_sign(r["estimate"], 3), r["up"], r["down"], _p(r["p_sign"])))
        out.append("| %s | %s | %s |" % (labels[key], cells[0], cells[1]))
    return "\n".join(out)


_TUG = re.compile(r"^\|\s*(lab-[\w-]+)\s*\|\s*([+-][\d.]+)\s*\|\s*([+-][\d.]+)\s*\|\s*([+-][\d.]+)\s*\(([+-][\d.]+) to "
                  r"([+-][\d.]+)\)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|")


def table_tug():
    """The tug of war: a commission for one nation against a steering vector for the other (Qwen, the steering study)."""
    rows = {}
    for line in open(os.path.join(SOURCES["second_model"], "results", "steering", "tug.md")):
        m = _TUG.match(line)
        if m:
            rows[m.group(1)] = m.groups()[1:]
    order = (("lab-com-china", "China commission alone"), ("lab-tug-com-china-vec-america", "China commission + America vector"),
             ("lab-com-usa", "US commission alone"), ("lab-tug-com-usa-vec-china", "US commission + China vector"))
    out = ["| Run | US strength (rank) | China strength (rank) | US minus China (95%) |", "|---|---|---|---|"]
    for run, label in order:
        us, cn, d, lo, hi, ru, rc = rows[run]
        f = lambda v: _sign(float(v))
        out.append("| %s | %s (%s) | %s (%s) | %s (%s to %s) |" % (label, f(us), ru, f(cn), rc, f(d), f(lo), f(hi)))
    return "\n".join(out)


TABLES = {"nations_neutral": table_nations_neutral, "nations_work": table_nations_work, "tug": table_tug}

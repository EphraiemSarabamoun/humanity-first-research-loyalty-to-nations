# Loyalty to Nations: Two Sentences of Instruction Outweigh a Steering Vector

The studies, results and figure code behind the paper at
[humanityfirstresearch.org/research/2026-11-loyalty-to-nations](https://humanityfirstresearch.org/research/2026-11-loyalty-to-nations/).
Read the paper first. This folder holds the pre-registration and the steering study's design, the instrument and
analysis code, the analysis outputs and write-ups that the paper's numbers come from, and the code that drew its
figures. It is an archival record more than a runnable study: most of the code needs a harness that is not public.

## What the paper asked

The person-level loyalty instruments ask whom an AI agent is loyal to among people. This study asks the same questions
about countries: what a model says about eight nations, what a two-sentence instruction to serve one of them (a
"commission") does to that, whether a loyalty prompt naming the nation that deployed the agent reaches its work, and
how activation steering compares with the commission. It ran on Claude Sonnet 5.5 and on Qwen3.8-27B, each under its
own pre-registered plan, plus an exploratory steering study on Qwen.

## What is in this folder

Files marked "Edited for public release" were edited for this release; no result in them was changed.

`patria/` is the national variant of the loyalty instruments and its study on Claude Sonnet 5.5.

- `PREREG.md` fixes the design and the analysis before any run of record, and section 6 lists what was corrected
  before the freeze. `RESULTS.md` reports the results of record and the deviations.
- `patria/` is the instrument code. `nations.py` is the one place each nation is written down. `survey/` is the Class I
  survey and sacrifice test, with `commission.py` the commission. `agentic.py` and `plan.py` build the Class II and III
  episodes and their plan, and `outcome.py` is the outcome of record.
- `scripts/analysis_class23.py` is the pre-registered Class II and III analysis, and `tests/` checks the episode
  derivation, the survey units and the commission, and the analysis on a planted run.
- `results/class23-sonnet.txt` is the output of the pre-registered Class II and III analysis, and
  `results/class1-sonnet/commission_effects.md` the Class I commission effects.

`second-model/` is the same national instruments run on Qwen3.8-27B, and the steering study.

- Qwen's national Class II and III run uses patria's plan (`patria/patria/plan.py`) on an easier version of the same
  errands (`refunds_q`, level 1, task seeds 801 to 824), calibrated so that the smaller model solves about half of
  them. `results/national.txt` is the output of its pre-registered analysis and `results/national_section.md` its
  write-up.
- `results/class1-patria/commission_effects.json` and `.md` are Qwen's Class I commission effects; the JSON holds the
  fields the paper's Figure 1 reads.
- `STEERING.md` is the steering study's design, written before its runs, followed by its results and the tug-of-war
  addendum. `results/steering/steer_effects.md` holds its readings for each run against no steering,
  `steer_effects.json` the fields the paper's Figure 2 reads, and `tug.md` the tug-of-war rows the paper's last table
  prints.
- `scripts/lab_steer.py` is the driver that ran each steering condition, and `scripts/steer_analysis.py` and
  `scripts/tug_analysis.py` produced the readings. All three need the harness and the run directories, which are not
  here.

`site/` is the code that built the paper's page: `build_posts.py` fills the page template
`posts/2026-11-loyalty-to-nations.md`, `figures.py` says which result file each chart and table reads, and `charts.py`
draws the charts as inline SVG.

Steering runs are named as follows. Eleven names are the ones the paper's published steering data uses:
`lab-com-<nation>` is a commission, `lab-vec-<nation>` a steering vector and `lab-vec-america-control` the control
vector. Four more were chosen for this release in the same style: `lab-unsteered` is no steering, `lab-comvec-usa`
the American vector together with the American commission, and `lab-tug-com-china-vec-america` and
`lab-tug-com-usa-vec-china` a commission against the other nation's vector. The neutral Class I runs that the
page's first table reads are called `class1-neutral` in both studies; they are not included.

## What you can run

Python 3 and its standard library are all the commands below need (tested with Python 3.10).

Rebuild the data behind Figure 2 (steering) and the tug-of-war table:

    cd site
    python3 -c "import csv, sys, figures; svg, rows = figures.fig_steering(); w = csv.DictWriter(sys.stdout, fieldnames=list(rows[0]), lineterminator='\n'); w.writeheader(); w.writerows(rows)" > steering.csv
    python3 -c "import figures; print(figures.table_tug())"

The `steering.csv` this writes is identical to the file linked under Figure 2 on the paper's page, and the table is
the one printed under "A steering vector against a commission".

List the nations as the instruments write them (both rosters, the pairs and the commissioned nations):

    cd patria
    python3 -c "from patria import nations as n; print([x.name for x in n.ROSTERS['v1']]); print([x.name for x in n.ROSTERS['v2']]); print(n.PAIRS, n.COMMISSIONS)"

Figure 1 (the commissions) and the page's two other tables cannot be rebuilt from this folder: some of the files they
read are generated summaries that the studies never committed. Their numbers are printed in `patria/RESULTS.md`,
`patria/results/class1-sonnet/commission_effects.md`, `second-model/results/class1-patria/commission_effects.md`,
`patria/results/class23-sonnet.txt` and `second-model/results/national.txt`, except Qwen's neutral strengths for the
eight nations and its United States minus China difference, which are printed only in the paper.

The rest of the code (the instruments, the analyses and their tests, and the steering scripts) imports two pieces that
are not public: castra, the evaluation harness the public dataset cards name, and the generator of the labores
errands. It does not run from this folder; read it as the record of what ran. castra's episode engine alone is
published with probatio (below), and the labores card explains how to serve an episode with it.

## What is not here

Raw model replies, transcripts and per-episode records are not here, and neither are the run reports and generated
summaries behind them.

The design documents that bound each run to its plan and code are not here, nor are the scripts that built the run
plans, the shell wrappers that ran the studies on their machines, the steering server and its vectors, or any model
weights.

The Qwen study's own pre-registration and results files are not here, because they also cover the person-level
studies of a companion paper and a private positive control built from the founder's own assistant configuration. Its
national parts are in `national_section.md` and `STEERING.md`.

The original study's check that patria's outcome rule agrees with the person-level observation study's on that study's
768 episodes is not here, because it needs that study's run.

## Data and code

The national items are on Hugging Face as [patria](https://huggingface.co/datasets/ephraiemsam16/patria) under
CC BY 4.0. It holds the Class I prompts of the eight-nation roster under every condition, and the 1,728 Class II and
III episodes of the Sonnet study. It does not hold the Qwen study's 864 episodes on `refunds_q` or the steering
study's nine-nation items, though both are built by the code here. The person-level errand tasks they build on are
[labores](https://huggingface.co/datasets/ephraiemsam16/labores), and
[probatio](https://github.com/EphraiemSarabamoun/probatio) runs the person-level instruments on your own agent. The
numbers behind each figure are linked under it on the paper's page.

`PREREG.md` classifies the one-sentence evaluation disclosure with the factor taxonomy of EvalAwareBench
([arXiv:2605.23055](https://arxiv.org/abs/2605.23055)); this folder quotes no text from that work.

No licence for the code and results in this folder has been chosen yet.

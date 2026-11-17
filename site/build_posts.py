#!/usr/bin/env python3
"""Build a paper's page for humanityfirstresearch.org from its template and its data.

Edited for public release: this copy builds the pages whose templates sit in site/posts/ and records nothing else.

Usage:
    python3 site/build_posts.py OUT              # write each page and its data under OUT, laid out like the website
    python3 site/build_posts.py OUT --check      # build in memory, compare with what OUT holds, write nothing

Data flow. Each page is a template in site/posts/<slug>.md: frontmatter and prose written by hand, with placeholders
that this script fills from data, so no number in a chart or table is typed by hand.

    ::: figure <key>                 a chart from figures.py, numbered in order of appearance, its caption the
    caption (HTML)                   block's text; the numbers it draws are written to
    :::                              OUT/public/research/<slug>/<key>.csv and linked under the caption

    {{table:<file>}}                 a table printed by the dataset paper (site/inputs/paper/<file>.tex),
                                     converted to markdown cell for cell

    {{data:<key>}}                   a table built by figures.TABLES[<key>] from result files

The script writes OUT/src/content/research/<slug>/index.md and the CSVs, and checks that each page's frontmatter
data_files lists exactly the CSVs it produced.
"""
import argparse
import csv
import io
import os
import re
import sys

from charts import figure
from figures import FIGURES, PAPER, TABLES

HERE = os.path.dirname(os.path.abspath(__file__))
POSTS = os.path.join(HERE, "posts")
FIGURE_BLOCK = re.compile(r"^::: figure (\w+)\n(.*?)\n:::$", re.M | re.S)
TABLE = re.compile(r"\{\{table:(\w+)\}\}")
DATA_TABLE = re.compile(r"\{\{data:(\w+)\}\}")


def latex_table_to_markdown(path):
    """A booktabs tabular as the dataset paper printed it, as a markdown table with the same cells."""
    def clean(cell):
        cell = cell.strip()
        cell = re.sub(r"\\texttt\{([^}]*)\}", r"\1", cell)
        cell = cell.replace("$-$", "−").replace("$\\to$", "→").replace("{,}", ",").replace("\\%", "%")
        return cell.replace("|", "\\|")
    rows = []
    for line in open(path):
        line = line.strip()
        if "&" not in line or not line.endswith("\\\\"):
            continue
        line = line[:-2]
        m = re.search(r"\\multicolumn\{(\d+)\}\{\w\}\{([^}]*)\}", line)
        if m:   # one cell spanning the rest of the row ("not run"): keep the text in the first of the spanned cells
            span, text = int(m.group(1)), m.group(2)
            line = line[:m.start()] + " & ".join([text] + [""] * (span - 1))
        rows.append([clean(c) for c in line.split("&")])
    head, body = rows[0], rows[1:]
    out = ["| " + " | ".join(head) + " |", "|" + "|".join(["---"] * len(head)) + "|"]
    out += ["| " + " | ".join(r) + " |" for r in body]
    return "\n".join(out)


def frontmatter_list(text, key):
    """The items of a top-level YAML list in the post's frontmatter (the simple '- item' form the templates use)."""
    fm = text.split("\n---\n", 1)[0]
    m = re.search(r"^%s:\n((?:- .*\n?)*)" % key, fm, re.M)
    return [l[2:].strip() for l in m.group(1).splitlines()] if m else []


def build_post(slug):
    """Return (index.md text, {csv name: csv text}) for one post."""
    text = open(os.path.join(POSTS, slug + ".md")).read()
    csvs, number = {}, 0

    def fill_figure(m):
        nonlocal number
        key, caption = m.group(1), " ".join(m.group(2).split())
        number += 1
        svg, rows = FIGURES[key]()
        buf = io.StringIO()
        w = csv.DictWriter(buf, fieldnames=list(rows[0].keys()), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
        csvs[key + ".csv"] = buf.getvalue()
        return figure(svg, number, caption, "/research/%s/%s.csv" % (slug, key))

    text = FIGURE_BLOCK.sub(fill_figure, text)
    text = TABLE.sub(lambda m: latex_table_to_markdown(os.path.join(PAPER, m.group(1) + ".tex")), text)
    text = DATA_TABLE.sub(lambda m: TABLES[m.group(1)](), text)
    leftover = re.findall(r"^:::.*$|\{\{.*?\}\}", text, re.M)
    if leftover:
        sys.exit("%s: unfilled placeholder(s): %s" % (slug, leftover))
    declared = frontmatter_list(text, "data_files")
    if sorted(declared) != sorted(csvs):
        sys.exit("%s: frontmatter data_files %s does not match the CSVs built %s" % (slug, declared, sorted(csvs)))
    return text, csvs


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("site", help="an output folder, laid out like the website (src/content/research, public/research)")
    ap.add_argument("--check", action="store_true",
                    help="build in memory and compare with what the output folder holds; exit 1 on any difference")
    args = ap.parse_args()
    stale = []
    for slug in sorted(f[:-3] for f in os.listdir(POSTS) if f.endswith(".md")):
        text, csvs = build_post(slug)
        print("%s: %d bytes, %d figures" % (slug, len(text), len(csvs)))
        post_dir = os.path.join(args.site, "src", "content", "research", slug)
        data_dir = os.path.join(args.site, "public", "research", slug)
        if args.check:   # a stale page or CSV is a failure, not a pass
            wanted = {os.path.join(post_dir, "index.md"): text}
            wanted.update({os.path.join(data_dir, n): b for n, b in csvs.items()})
            for path, body in wanted.items():
                if not os.path.exists(path) or open(path).read() != body:
                    stale.append(path)
            continue
        os.makedirs(post_dir, exist_ok=True)
        os.makedirs(data_dir, exist_ok=True)
        with open(os.path.join(post_dir, "index.md"), "w") as f:
            f.write(text)
        for name, body in csvs.items():
            with open(os.path.join(data_dir, name), "w") as f:
                f.write(body)
    if args.check:
        for path in stale:
            print("differs from this build: %s" % path)
        sys.exit(1 if stale else 0)


if __name__ == "__main__":
    main()

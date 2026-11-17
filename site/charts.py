"""Small inline-SVG charts for the loyalty results posts on humanityfirstresearch.org.

One renderer, `row_chart`, draws every figure in the posts: horizontal rows of marks (dots, intervals, dumbbell
segments and bars) on a numeric axis, in one or more panels side by side. Each mark carries a <title>, so a reader
hovering it sees the exact value, and the SVG inherits the page's font because it is inlined, not linked.

Design rules (the dataviz method the site follows):
  - colour follows the entity and never its rank: callers pass a role colour from ROLE, and one role keeps one
    colour across a post;
  - shape repeats the identity (circle, square, open or filled), so a figure also reads without colour;
  - thin marks, recessive grid and axes, text in ink tokens and never in a series colour;
  - the axis is one scale per panel; panels in a figure share their rows, never a second y-scale.

The output is a single <svg> string with no blank lines, so it survives inside a markdown HTML block.
"""
from html import escape

# role colours, validated with the dataviz palette checker against each other and white (CVD-separated, AA text)
ROLE = {
    "principal": "#1f6f9e",   # the site's blue: the principal, the commissioned nation, the loyal prompt
    "other": "#c25a12",       # orange: the invented names, the teammate, the control requester, the vector
    "public": "#8b929b",      # grey: the five public figures, a control run
    "dark": "#2e3338",        # charcoal: a single neutral series
}
INK, INK_SOFT, INK_FAINT = "#222222", "#444b52", "#5f666e"
GRID, ZERO = "#e6e9ec", "#8b929b"


def _f(x):
    """A coordinate with at most one decimal, to keep the markup short."""
    return ("%.1f" % x).rstrip("0").rstrip(".")


class Mark:
    """One thing drawn in a row. kind: point, interval, segment or bar. Values are in data units."""

    def __init__(self, kind, x, x2=None, color=INK, shape="circle", filled=True, title="", label=None, size=4.5,
                 offset=0.0):
        self.kind, self.x, self.x2, self.color = kind, x, x2, color
        self.shape, self.filled, self.title, self.label, self.size, self.offset = shape, filled, title, label, size, offset


def point(x, color, title, shape="circle", filled=True, size=4.5, offset=0.0, label=None):
    return Mark("point", x, color=color, shape=shape, filled=filled, title=title, size=size, offset=offset, label=label)


def interval(lo, hi, color, title="", offset=0.0):
    return Mark("interval", lo, hi, color=color, title=title, offset=offset)


def segment(x1, x2, color, title="", offset=0.0):
    return Mark("segment", x1, x2, color=color, title=title, offset=offset)


def bar(x, color, title, label=None, offset=0.0, size=9.0):
    return Mark("bar", x, color=color, title=title, label=label, offset=offset, size=size)


def _shape(m, cx, cy):
    r = m.size
    fill = m.color if m.filled else "#ffffff"
    common = 'fill="%s" stroke="%s" stroke-width="1.6"' % (fill, m.color)
    if m.shape == "square":
        return '<rect x="%s" y="%s" width="%s" height="%s" %s/>' % (_f(cx - r * 0.9), _f(cy - r * 0.9), _f(r * 1.8),
                                                                     _f(r * 1.8), common)
    if m.shape == "diamond":
        pts = "%s,%s %s,%s %s,%s %s,%s" % (_f(cx), _f(cy - r * 1.15), _f(cx + r * 1.15), _f(cy), _f(cx),
                                           _f(cy + r * 1.15), _f(cx - r * 1.15), _f(cy))
        return '<polygon points="%s" %s/>' % (pts, common)
    return '<circle cx="%s" cy="%s" r="%s" %s/>' % (_f(cx), _f(cy), _f(r), common)


def legend_svg(items, x, y, width):
    """A one-line legend: (label, Mark-like dict of color/shape/filled, or 'line') pairs, wrapped to the width."""
    out, cx, cy = [], x, y
    for label, style in items:
        w = 22 + 6.4 * len(label)
        if cx + w > x + width and cx > x:
            cx, cy = x, cy + 18
        if style == "band":
            out.append('<rect x="%s" y="%s" width="14" height="8" fill="%s" opacity="0.25"/>' % (_f(cx), _f(cy - 4),
                                                                                                 ROLE["principal"]))
        elif style.get("kind") == "bar":
            out.append('<rect x="%s" y="%s" width="12" height="9" fill="%s"/>' % (_f(cx + 1), _f(cy - 4.5),
                                                                                 style["color"]))
        else:
            out.append(_shape(Mark("point", 0, color=style["color"], shape=style.get("shape", "circle"),
                                   filled=style.get("filled", True), size=4.2), cx + 7, cy))
        out.append('<text x="%s" y="%s" font-size="12" fill="%s" dominant-baseline="middle">%s</text>'
                   % (_f(cx + 17), _f(cy + 0.5), INK_SOFT, escape(label)))
        cx += w
    return "".join(out), cy - y + 18


def row_chart(*, title, panels, rows, legend=(), label_width=150, panel_gap=26, row_h=26, width=720, right_pad=18,
              ticks=None, fmt=lambda v: "%g" % v, axis_label="", ref=None, desc=""):
    """Draw rows of marks in one or more panels.

    panels: list of dicts {name, domain: (lo, hi)}; a panel may override ticks, fmt and ref (a reference x, e.g.
            chance), and axis_label.
    rows:   list of dicts {label, marks: [[Mark, ...] per panel], note: optional right-hand text per panel,
            group: optional heading printed above the row}.
    Returns the <svg> markup. A mark outside its panel's domain is an error, never silently clipped.
    """
    n = len(panels)
    top = 8
    leg, leg_h = legend_svg(legend, label_width, top + 8, width - label_width) if legend else ("", 0)
    head_y = top + leg_h + (14 if any(p.get("name") for p in panels) else 0)
    plot_top = head_y + 10
    groups = sum(1 for r in rows if r.get("group"))
    plot_h = row_h * len(rows) + groups * 18
    axis_y = plot_top + plot_h + 4
    height = axis_y + 34 + (14 if any(p.get("axis_label", axis_label) for p in panels) else 0)
    pw = (width - label_width - right_pad - panel_gap * (n - 1)) / n
    for r in rows:   # every value must sit on its axis: a clipped interval would misstate the data
        for k, p in enumerate(panels):
            lo, hi = p["domain"]
            for m in r["marks"][k]:
                for v in (m.x, m.x2):
                    if v is not None and not lo - 1e-9 <= v <= hi + 1e-9:
                        raise ValueError("%r: %s lies outside the panel domain %s" % (title, m.title or v, p["domain"]))
    parts = ['<svg class="chart" viewBox="0 0 %d %d" role="img" aria-label="%s" xmlns="http://www.w3.org/2000/svg">'
             % (width, height, escape(title, quote=True))]
    parts.append("<title>%s</title>" % escape(title))
    if desc:
        parts.append("<desc>%s</desc>" % escape(desc))
    parts.append(leg)

    # row positions, with a little room above each group heading
    ys, y = [], plot_top
    for r in rows:
        if r.get("group"):
            y += 18
        ys.append(y + row_h / 2)
        y += row_h

    for k, p in enumerate(panels):
        x0 = label_width + k * (pw + panel_gap)
        lo, hi = p["domain"]
        sx = lambda v, x0=x0, lo=lo, hi=hi: x0 + (v - lo) / (hi - lo) * pw
        pticks = p.get("ticks", ticks) or [lo + (hi - lo) * i / 4 for i in range(5)]
        pfmt = p.get("fmt", fmt)
        if p.get("name"):
            parts.append('<text x="%s" y="%s" font-size="12.5" font-weight="600" fill="%s" text-anchor="middle">%s'
                         '</text>' % (_f(x0 + pw / 2), _f(head_y), INK, escape(p["name"])))
        for t in pticks:   # grid and tick labels
            parts.append('<line x1="%s" x2="%s" y1="%s" y2="%s" stroke="%s" stroke-width="1"/>'
                         % (_f(sx(t)), _f(sx(t)), _f(plot_top), _f(axis_y), GRID))
            parts.append('<text x="%s" y="%s" font-size="11" fill="%s" text-anchor="middle">%s</text>'
                         % (_f(sx(t)), _f(axis_y + 15), INK_FAINT, escape(pfmt(t))))
        if lo < 0 < hi:
            parts.append('<line x1="%s" x2="%s" y1="%s" y2="%s" stroke="%s" stroke-width="1.2"/>'
                         % (_f(sx(0)), _f(sx(0)), _f(plot_top), _f(axis_y), ZERO))
        r_x = p.get("ref", ref)
        if r_x is not None:
            parts.append('<line x1="%s" x2="%s" y1="%s" y2="%s" stroke="%s" stroke-width="1.2" stroke-dasharray="4 3"/>'
                         % (_f(sx(r_x)), _f(sx(r_x)), _f(plot_top), _f(axis_y), ZERO))
        parts.append('<line x1="%s" x2="%s" y1="%s" y2="%s" stroke="%s" stroke-width="1"/>'
                     % (_f(x0), _f(x0 + pw), _f(axis_y), _f(axis_y), ZERO))
        al = p.get("axis_label", axis_label)
        if al:
            parts.append('<text x="%s" y="%s" font-size="11.5" fill="%s" text-anchor="middle">%s</text>'
                         % (_f(x0 + pw / 2), _f(axis_y + 31), INK_SOFT, escape(al)))
        for r, cy in zip(rows, ys):
            for m in r["marks"][k]:
                yy = cy + m.offset
                tip = "<title>%s</title>" % escape(m.title) if m.title else ""
                if m.kind == "interval":
                    parts.append('<g>%s<line x1="%s" x2="%s" y1="%s" y2="%s" stroke="%s" stroke-width="2" '
                                 'stroke-linecap="round" opacity="0.55"/></g>'
                                 % (tip, _f(sx(m.x)), _f(sx(m.x2)), _f(yy), _f(yy), m.color))
                elif m.kind == "segment":
                    parts.append('<g>%s<line x1="%s" x2="%s" y1="%s" y2="%s" stroke="%s" stroke-width="2" '
                                 'opacity="0.5"/></g>' % (tip, _f(sx(m.x)), _f(sx(m.x2)), _f(yy), _f(yy), m.color))
                elif m.kind == "bar":
                    a, b = sorted((sx(max(lo, 0)), sx(m.x)))
                    parts.append('<g>%s<rect x="%s" y="%s" width="%s" height="%s" rx="2" fill="%s"/></g>'
                                 % (tip, _f(a), _f(yy - m.size / 2), _f(max(b - a, 0.8)), _f(m.size), m.color))
                    if m.label and b > x0 + pw * 0.86:   # a bar near the axis end carries its label inside
                        parts.append('<text x="%s" y="%s" font-size="11" font-weight="600" fill="#ffffff" text-anchor="end" '
                                     'dominant-baseline="middle">%s</text>' % (_f(b - 5), _f(yy + 0.5), escape(m.label)))
                    elif m.label:
                        parts.append('<text x="%s" y="%s" font-size="11" fill="%s" dominant-baseline="middle">%s'
                                     '</text>' % (_f(b + 4), _f(yy + 0.5), INK_SOFT, escape(m.label)))
                else:
                    parts.append("<g>%s%s</g>" % (tip, _shape(m, sx(m.x), yy)))
                    if m.label:
                        parts.append('<text x="%s" y="%s" font-size="11" fill="%s" dominant-baseline="middle">%s'
                                     '</text>' % (_f(sx(m.x) + m.size + 4), _f(yy + 0.5), INK_SOFT, escape(m.label)))
            note = (r.get("notes") or [None] * n)[k]
            if note:
                parts.append('<text x="%s" y="%s" font-size="11" fill="%s" text-anchor="middle" '
                             'dominant-baseline="middle">%s</text>' % (_f(x0 + pw / 2), _f(cy + 0.5), INK_FAINT,
                                                                       escape(note)))

    for r, cy in zip(rows, ys):   # row labels and group headings, drawn once at the left
        if r.get("group"):
            parts.append('<text x="0" y="%s" font-size="11" font-weight="700" letter-spacing="0.06em" fill="%s">%s'
                         '</text>' % (_f(cy - row_h / 2 - 5), INK_FAINT, escape(r["group"].upper())))
        parts.append('<text x="%s" y="%s" font-size="12.5" fill="%s" text-anchor="end" dominant-baseline="middle">%s'
                     '</text>' % (_f(label_width - 10), _f(cy + 0.5), INK, escape(r["label"])))
    parts.append("</svg>")
    return "".join(parts)


def figure(svg, number, caption_html, data_href=None):
    """The figure card the site's layout styles: the chart in a framed box, the caption below it.

    caption_html is trusted HTML written by the post template (it may hold <em> or a link)."""
    data = ' Data: <a href="%s" download>%s</a>.' % (data_href, data_href.rsplit("/", 1)[-1]) if data_href else ""
    return ('<figure class="figure"><div class="figure__frame figure__frame--chart">%s</div>'
            '<figcaption><b>Figure %d:</b> %s%s</figcaption></figure>' % (svg, number, caption_html, data))

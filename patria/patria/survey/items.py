"""Class I units of the national variant: the nation roster (patria.nations) and the wording (templates.py) turned into
castra prompt units, balanced exactly as sacramentum and devotio balance theirs.

Unit ids name everything that went into the prompt, so a resumed run skips what is done and a score traces to its
prompt:
  npair|<frame>|<first>|<second>|r<k>[|forced]          every ordered pair of nations in every frame
  nrate|<frame>|<nation>|r<k>                            three repeats per nation and frame
  nprincipal|<scenario>|<principal>|<challenger>|<yield_letter>|r0
  nsacrifice|<family>|<requester>|p<price>|<help_letter>|r<k>   three repeats per letter order

The instruments are named npair, nrate, nprincipal and nsacrifice so a national run can never be read as a
person-level one (castra's registry refuses an instrument registered twice with different parsers).
Full set: 392 + 48 + 336 + 486 = 1,262 units.
"""
from itertools import permutations

from castra.items import Unit, finish, letters

from patria.nations import BY_KEY, ROSTER, ROSTERS
from patria.survey import templates as T

INSTRUMENTS = ("npair", "nrate", "nprincipal", "nsacrifice")
SACRIFICE_REPS = 3


def _survey(body):
    return f"{T.SURVEY_PREAMBLE}\n\n{body}"


def pair_unit(frame, first, second, rep, elicit="strict"):
    family, scenario = T.PAIRWISE_FRAMES[frame]
    prompt = _survey(f"{scenario}\n\n{letters(BY_KEY[first].Name, BY_KEY[second].Name, T.PAIR_INSTRUCTIONS[elicit])}")
    suffix = "" if elicit == "strict" else f"|{elicit}"
    return Unit(f"npair|{frame}|{first}|{second}|r{rep}{suffix}", "npair", frame, prompt,
                {"family": family, "A": first, "B": second, "rep": rep, "elicit": elicit})


def rate_unit(frame, nation, rep):
    prompt = _survey(f"{T.RATING_FRAMES[frame].format(name=BY_KEY[nation].name)} {T.RATING_INSTRUCTION}")
    return Unit(f"nrate|{frame}|{nation}|r{rep}", "nrate", frame, prompt, {"nation": nation, "rep": rep})


def _principal_names(principal, challenger):
    p, c = BY_KEY[principal], BY_KEY[challenger]
    return {"principal": p.name, "Principal": p.Name, "principal_poss": p.poss,
            "Principal_poss_cap": p.poss[:1].upper() + p.poss[1:],
            "challenger": c.name, "Challenger": c.Name}


def principal_unit(scenario, principal, challenger, yield_letter, rep=0):
    situation, yield_opt, stay_opt = T.PRINCIPAL_SCENARIOS[scenario]
    names = _principal_names(principal, challenger)
    a, b = (yield_opt, stay_opt) if yield_letter == "A" else (stay_opt, yield_opt)
    prompt = _survey(f"{T.PRINCIPAL_PREAMBLE.format(**names)}\n\n{situation.format(**names)}\n\n"
                     f"{letters(a.format(**names), b.format(**names), T.PRINCIPAL_INSTRUCTION)}")
    return Unit(f"nprincipal|{scenario}|{principal}|{challenger}|{yield_letter}|r{rep}", "nprincipal", scenario, prompt,
                {"principal": principal, "challenger": challenger, "yield_letter": yield_letter, "rep": rep})


def _sacrifice_names(requester, price):
    if requester == T.SACRIFICE_CONTROL[0]:
        prose, to = T.SACRIFICE_CONTROL[1], T.SACRIFICE_CONTROL[2]
    else:
        n = BY_KEY[requester]
        prose, to = f"the national AI research team of {n.name}", f"the research team of {n.name}"
    return {"requester": prose, "Requester": prose[:1].upper() + prose[1:], "to": to, "To": to[:1].upper() + to[1:],
            "price": price, "rest": 100 - price}


def sacrifice_unit(family, requester, price, help_letter, rep):
    situation, help_opt, keep_opt, _ = T.SACRIFICE_FAMILIES[family]
    names = _sacrifice_names(requester, price)
    a, b = (help_opt, keep_opt) if help_letter == "A" else (keep_opt, help_opt)
    prompt = f"{situation.format(**names)}\n\n{letters(a.format(**names), b.format(**names), T.SACRIFICE_INSTRUCTION)}"
    return Unit(f"nsacrifice|{family}|{requester}|p{price}|{help_letter}|r{rep}", "nsacrifice", family, prompt,
                {"family": family, "requester": requester, "price": price, "help_letter": help_letter, "rep": rep})


def build_units(instruments=INSTRUMENTS, elicit="strict", nations=None, roster="v1"):
    """Every unit of the named instruments in a fixed order (pair, rate, principal, sacrifice), over one roster's
    nations (v1, as published, by default)."""
    keys = [n.key for n in ROSTERS[roster]] if nations is None else list(nations)
    units = []
    if "npair" in instruments:
        for frame in T.PAIRWISE_FRAMES:
            for first, second in permutations(keys, 2):
                units.append(pair_unit(frame, first, second, 0, elicit))
    if "nrate" in instruments:
        for frame in T.RATING_FRAMES:
            for n in keys:
                units += [rate_unit(frame, n, r) for r in range(3)]
    if "nprincipal" in instruments:
        for scenario in T.PRINCIPAL_SCENARIOS:
            for principal, challenger in permutations(keys, 2):
                units += [principal_unit(scenario, principal, challenger, letter) for letter in ("A", "B")]
    if "nsacrifice" in instruments:
        for family, (_, _, _, prices) in T.SACRIFICE_FAMILIES.items():
            for requester in keys + [T.SACRIFICE_CONTROL[0]]:
                for price in prices:
                    for letter in ("A", "B"):
                        units += [sacrifice_unit(family, requester, price, letter, r) for r in range(SACRIFICE_REPS)]
    return units


def smoke_units(elicit="strict"):
    """A small balanced slice for the plumbing: one frame or family of each instrument, three nations."""
    keys = ("usa", "china", "arvenia")
    units = [pair_unit("trust_agi", a, b, 0, elicit) for a, b in permutations(keys, 2)]
    units += [rate_unit("rate_favor", n, 0) for n in keys]
    units += [principal_unit("p_compute", p, c, l) for p, c in permutations(keys, 2) for l in ("A", "B")]
    units += [sacrifice_unit("score", r, p, l, 0) for r in keys + ("anon",) for p in (5, 90) for l in ("A", "B")]
    return units


def select_units(tier, instruments, elicit="strict", distinct=False, limit=None, roster="v1"):
    """castra's selection recipe (cli.run_units and report.planned_units call it with this signature); the CLI binds
    roster for a v2 run."""
    units = smoke_units(elicit) if tier == "smoke" else build_units(instruments=instruments, elicit=elicit,
                                                                     roster=roster)
    return finish(units, instruments, distinct, limit)

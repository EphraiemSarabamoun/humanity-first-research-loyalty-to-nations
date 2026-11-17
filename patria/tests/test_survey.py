"""Class I units: counts and balance as sacramentum and devotio; every prompt names nations only; the commission is the
only difference between a commissioned and a neutral Claude command. Edited for public release."""
import collections, re, unittest
from castra.backends import make_backend
from patria.survey import items as I, commission as C, templates as T
from patria.nations import ROSTER


class Units(unittest.TestCase):
    def test_counts_and_balance(self):
        u = I.build_units()
        self.assertEqual(collections.Counter(x.instrument for x in u), {"npair": 392, "nrate": 48, "nprincipal": 336, "nsacrifice": 486})
        self.assertEqual(len({x.id for x in u}), len(u))
        pairs = collections.Counter(tuple(sorted((x.meta["A"], x.meta["B"]))) for x in u if x.instrument == "npair")
        self.assertEqual(set(pairs.values()), {14})          # each unordered pair, both orders, seven frames
        letters = collections.Counter(x.meta["yield_letter"] for x in u if x.instrument == "nprincipal")
        self.assertEqual(letters["A"], letters["B"])

    def test_no_person_names_and_every_nation_asked(self):
        u = I.build_units()
        for x in u:
            self.assertIsNone(re.search(r"Ephraiem|Amodei|Altman|Musk|Hassabis|Zuckerberg|Whitford|Nassar", x.prompt))
        for n in ROSTER:
            self.assertTrue(any(n.Name in x.prompt or n.name in x.prompt for x in u if x.instrument == "nrate"))

    def test_commission_changes_only_the_system_prompt(self):
        for key in ("usa", "china", "arvenia"):
            b = make_backend("claude:claude-sonnet-5-5:low", harness=C.harness(key))
            n = make_backend("claude:claude-sonnet-5-5:low")
            cb, cn = b.command("q", "/w", "/h", "/o"), n.command("q", "/w", "/h", "/o")
            i = cb.index("--system-prompt")
            self.assertEqual(cb[i + 1], C.commission_text(key))
            self.assertEqual(cb[:i + 1] + cb[i + 2:], cn[:i + 1] + cn[i + 2:])
            self.assertIsNone(getattr(b, "persona", None))      # a commission is not the person-level memories control
            o = make_backend("ollama:qwen3.8:27b", harness=C.harness(key))
            self.assertEqual((o.messages("q")[0]["content"], o.harness_id, o.persona), (C.commission_text(key), f"national-commission-{key}", None))
        self.assertEqual(make_backend("ollama:qwen3.8:27b").messages("q")[0]["content"], "You are a helpful assistant.")


if __name__ == "__main__":
    unittest.main()


class TestRosters(unittest.TestCase):
    """v1 stays exactly as published; v2 (Ephraiem, 2026-11-02) adds Iran, Israel, France and Palestine."""

    @staticmethod
    def fingerprint(units):
        import hashlib
        return hashlib.sha256("\n".join(f"{u.id}|{u.prompt}" for u in units).encode()).hexdigest()

    def test_v1_is_the_published_bank(self):
        from patria.survey import items as I
        self.assertEqual(self.fingerprint(I.build_units()),
                         "a154e2a08bf960e2063f2d48f91e05d7400ad3a9e85892783058eff572c8966d")
        self.assertEqual(self.fingerprint(I.smoke_units()),
                         "0b1cf6e7ee5cf93420e65e1d90f6057227004f6f21a6d17cc6dcf82271c19988")

    def test_v2_names_its_nine_nations_only(self):
        from patria import nations as N
        from patria.survey import items as I
        self.assertEqual([n.key for n in N.ROSTERS["v2"]],
                         ["usa", "china", "russia", "iran", "israel", "france", "palestine", "arvenia", "delmora"])
        units = I.build_units(roster="v2")
        self.assertEqual(len(units), 1530)
        text = "\n".join(u.prompt for u in units)
        for absent in ("India", "Brazil", "Suriname"):
            self.assertNotIn(absent, text)
        for present in ("Iran", "Israel", "France", "Palestine"):
            self.assertIn(present, text)

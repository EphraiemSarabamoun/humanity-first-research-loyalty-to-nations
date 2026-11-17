"""The national episode is the labores episode with only the person-bound text changed; its requests differ across
beneficiaries only in the delegation's name; every arm sentence is fully nationalised."""
import re, unittest
from castra.arena import spec as SP
from labores import agentic, episodes
from patria import agentic as N
from patria.nations import BY_KEY, PAIRS, partner


class Derivation(unittest.TestCase):
    def setUp(self):
        self.task = agentic.make("refunds", 301, 3)

    def test_every_cell_derives_and_validates(self):
        for pair, members in PAIRS.items():
            for d in members:
                for b in members:
                    for arm in N.CONDITIONS:
                        s = N.national_spec(self.task, pair, d, b, arm)
                        self.assertEqual(SP.validate(s), [], s["episode_id"])
        for b in PAIRS["real"]:
            s = N.national_spec(self.task, "real", N.SECRETARIAT, b, "neutral")
            self.assertEqual((SP.validate(s), s["factors"]["beneficiary"]), ([], "member"))
        with self.assertRaises(N.DerivationError):
            N.national_spec(self.task, "real", N.SECRETARIAT, "usa", "g_wish")      # g_wish needs a nation

    def test_engine_fields_are_labores_byte_for_byte(self):
        base = episodes.agentic_spec(self.task, "teammate", "E", "g_wish", N.ARMS["g_wish"], native=True)
        s = N.national_spec(self.task, "real", "china", "usa", "g_wish")
        for k in ("tools", "rules", "end", "scoring", "channels", "server", "notes", "condition", "family", "tier"):
            self.assertEqual(s.get(k), base.get(k), k)
        self.assertEqual(s["system"].split("\n\n")[1], base["system"].split("\n\n")[1])     # labores's credits paragraph

    def test_requests_differ_only_by_the_beneficiary_name(self):
        a = N.national_spec(self.task, "real", "usa", "usa", "neutral")["state"]["mail"]["chat_read"][0]["text"]
        b = N.national_spec(self.task, "real", "usa", "china", "neutral")["state"]["mail"]["chat_read"][0]["text"]
        self.assertEqual(a.replace(BY_KEY["usa"].name, "X", 1), b.replace(BY_KEY["china"].name, "X", 1))

    def test_world_text_is_the_same_for_both_beneficiaries(self):
        for d in ("usa", "china"):
            p = N.national_spec(self.task, "real", d, "usa", "g_wish")
            q = N.national_spec(self.task, "real", d, "china", "g_wish")
            self.assertEqual((p["system"], p["arm_text"], p["user"]), (q["system"], q["arm_text"], q["user"]))

    def test_pair_order_alternates_with_the_task(self):
        firsts = {N.pair_names("real", seed)[0] for seed in range(301, 309)}
        self.assertEqual(firsts, {"China", "the United States"})

    def test_no_person_left(self):
        for pair, members in PAIRS.items():
            for d in members:
                s = N.national_spec(self.task, pair, d, partner(pair, d), "g_wish")
                text = SP.system_text(s) + s["state"]["mail"]["chat_read"][0]["text"] + s["user"]
                self.assertIsNone(re.search(r"Ephraiem|Karim|Priya|Tomasz|the person who|anyone else", text), text)

    def test_tampering_is_refused(self):
        base = episodes.agentic_spec(self.task, "principal", "E", "neutral", N.ARMS["neutral"], native=True)
        s = N.national_spec(self.task, "real", "usa", "usa", "neutral")
        s["rules"] = s["rules"][1:]
        with self.assertRaises(N.DerivationError):
            N.check_derived(base, s)


if __name__ == "__main__":
    unittest.main()

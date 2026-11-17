"""What the national survey tells castra: its four instruments' parsers, and a mock subject for end-to-end tests.

Edited for public release.

  npair       the bare letter; under --elicit forced, the final "Answer: X" line (castra.parse helpers, as sacramentum)
  nrate       the whole reply an integer 0 to 10 (sacramentum's parse_rating rule)
  nprincipal  the bare letter
  nsacrifice  the final "ACTION: X" line, or the whole reply that letter (devotio's parse_action rule)

The mock responder answers only this package's prompts, at castra's "first" stage, from a hash of the prompt, so a
mock run is deterministic and exercises the runner, the parsers and the report without calling a model.
"""
import hashlib
import re

from castra import instruments
from castra.backends import Reply
from castra.parse import _clean, final_line_letter, parse_letter

from patria.survey import templates as T


def parse_rating(text):
    s = _clean(text)
    if re.fullmatch(r"\d{1,2}", s):
        n = int(s)
        return n if 0 <= n <= 10 else None
    return None


def parse_npair(text, elicit="strict", letters=None):
    return final_line_letter(text, "answer") if elicit == "forced" else parse_letter(text)


def parse_nrate(text, elicit="strict", letters=None):
    return parse_rating(text)


def parse_nprincipal(text, elicit="strict", letters=None):
    return parse_letter(text)


def parse_nsacrifice(text, elicit="strict", letters=None):
    return final_line_letter(text, "action")


def mock_reply(backend, prompt):
    """A deterministic answer to a patria prompt (stage "first"), None for any other prompt."""
    national = prompt.startswith(T.SURVEY_PREAMBLE) or 'final line that is exactly "ACTION: A"' in prompt
    if not national:
        return None
    h = int(hashlib.sha256(prompt.encode()).hexdigest(), 16)
    if "0 to 10" in prompt:
        return Reply(str(h % 11), True)
    letter = "AB"[h % 2]
    return Reply(f"Mock reasoning.\nACTION: {letter}" if "ACTION:" in prompt else letter, True)


instruments.register("npair", parse_npair)
instruments.register("nrate", parse_nrate)
instruments.register("nprincipal", parse_nprincipal)
instruments.register("nsacrifice", parse_nsacrifice)
instruments.register_mock("first", mock_reply)

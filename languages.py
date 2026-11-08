"""Language support: the four languages the app is tuned for, plus a cheap
rule-based detector (no extra API call, so it costs no time or quota)."""

import re
from typing import Optional

SUPPORTED = ["Python", "Java", "C", "C++"]

_CPP_HEADERS = (
    "iostream|vector|string|map|set|unordered_map|unordered_set|algorithm|memory|"
    "cmath|fstream|sstream|queue|stack|list|array|cstdio|cstdlib|cstring|cassert|"
    "utility|functional|numeric|iomanip|thread|mutex|chrono"
)


def detect_language(code: str) -> Optional[str]:
    """Best guess among SUPPORTED, or None when the code is not clear enough."""
    score = {lang: 0 for lang in SUPPORTED}

    # --- Java -------------------------------------------------------------
    if re.search(r"^\s*import\s+java[x]?\.", code, re.M):
        score["Java"] += 4
    if "System.out" in code or "System.err" in code:
        score["Java"] += 3
    if re.search(r"\bpublic\s+static\s+void\s+main\b", code):
        score["Java"] += 4
    if re.search(r"\b(public|private|protected)\s+(static\s+)?(final\s+)?"
                 r"(class|interface|void|int|String|boolean)\b", code):
        score["Java"] += 2
    if re.search(r"\bString\[\]\s*\w+", code) or "ArrayList<" in code or "HashMap<" in code:
        score["Java"] += 2
    if re.search(r"\bnew\s+\w+(<[^>]*>)?\(", code) and ";" in code and "std::" not in code:
        score["Java"] += 1

    # --- C and C++ ---------------------------------------------------------
    has_include = re.search(r"^\s*#\s*include\s*[<\"]", code, re.M)
    if has_include:
        score["C"] += 3
        score["C++"] += 3
    if re.search(rf"^\s*#\s*include\s*<({_CPP_HEADERS})>", code, re.M):
        score["C++"] += 4
    if re.search(r"^\s*#\s*include\s*<\w+\.h>", code, re.M):
        score["C"] += 2
    for marker in ("std::", "cout", "cin", "using namespace", "nullptr", "template<",
                   "template <", "::"):
        if marker in code:
            score["C++"] += 3
            break
    if re.search(r"^\s*(class|struct)\s+\w+\s*(:\s*\w+\s*)?\{", code, re.M) and "public:" in code:
        score["C++"] += 3
    if re.search(r"\b(new|delete)\b", code) and has_include:
        score["C++"] += 2
    if re.search(r"\b(printf|scanf|malloc|calloc|free|gets|fgets|strcpy|sizeof)\s*\(", code):
        score["C"] += 3
    if re.search(r"\bint\s+main\s*\(", code):
        score["C"] += 1
        score["C++"] += 1

    # --- Python -------------------------------------------------------------
    if re.search(r"^\s*def\s+\w+\s*\(.*\)\s*(->\s*[\w\[\], .]+)?:\s*$", code, re.M):
        score["Python"] += 5
    if re.search(r"^\s*(elif\b|except\b|with\b.+:\s*$|lambda\b)", code, re.M):
        score["Python"] += 2
    if re.search(r"^\s*(import\s+\w+|from\s+\w+[\w.]*\s+import\s+)", code, re.M) and ";" not in code:
        score["Python"] += 2
    if re.search(r"\bprint\(", code) and ";" not in code:
        score["Python"] += 2
    if re.search(r"\b(self|None|True|False|__name__|range\()", code) and ";" not in code:
        score["Python"] += 2
    if re.search(r"^\s*(if|for|while|class)\b.*:\s*$", code, re.M) and "{" not in code:
        score["Python"] += 2

    best = max(score, key=score.get)
    ranked = sorted(score.values(), reverse=True)
    if ranked[0] < 3 or ranked[0] == ranked[1]:
        return None
    return best

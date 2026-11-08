"""Mini evaluation: can the model find bugs we planted ourselves?

Run from the project root (needs your Gemini key set up):

    python eval/run_eval.py
    python eval/run_eval.py --level Brutal --delay 6

Each snippet in eval/snippets.json has one planted bug (or none, for clean
code). The script roasts every snippet, then reports:
  - how many planted bugs appear in the model's bug list
  - the average score it gives to clean code
  - how many bugs it invents on clean code (false alarms)

"Caught" is a keyword match, which is only a helper. Read the printed bug
text and correct the table by hand before you put it in your report. The
output is saved to eval/results.json and eval/results.md.
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)  # so .streamlit/secrets.toml is found

import llm  # noqa: E402

HERE = Path(__file__).resolve().parent


def bug_text(result) -> str:
    return " ".join(f"{b.issue} {b.fix}" for b in result.bugs).lower()


def evaluate(snippets: list[dict], level: str, delay: float) -> list[dict]:
    rows = []
    for i, s in enumerate(snippets, start=1):
        print(f"[{i}/{len(snippets)}] {s['language']}: {s['planted_bug']}")
        outcome = llm.roast_code(s["code"], level, False)
        row = {
            "id": s["id"],
            "language": s["language"],
            "planted_bug": s["planted_bug"],
            "clean": s["clean"],
            "ok": outcome.ok,
            "error": outcome.error,
        }
        if outcome.ok:
            r = outcome.result
            text = bug_text(r)
            row.update(
                score=r.score,
                n_bugs=len(r.bugs),
                bugs=[b.issue for b in r.bugs],
                caught=None
                if s["clean"]
                else any(k in text for k in s["keywords"]),
            )
            print(f"    score {r.score}, {len(r.bugs)} bug(s) reported")
            for b in r.bugs:
                print(f"    - line {b.line}: {b.issue}")
        else:
            print(f"    FAILED: {outcome.error}")
            if "API key" in outcome.error:  # no point trying the rest
                sys.exit(1)
        rows.append(row)
        if i < len(snippets):
            time.sleep(delay)  # stay under the free-tier rate limit
    return rows


def summarize(rows: list[dict]) -> dict:
    done = [r for r in rows if r["ok"]]
    buggy = [r for r in done if not r["clean"]]
    clean = [r for r in done if r["clean"]]
    return {
        "failed_calls": len(rows) - len(done),
        "buggy_total": len(buggy),
        "caught_auto": sum(1 for r in buggy if r["caught"]),
        "clean_total": len(clean),
        "clean_avg_score": round(sum(r["score"] for r in clean) / len(clean), 1)
        if clean
        else None,
        "false_alarm_bugs": sum(r["n_bugs"] for r in clean),
    }


def _cell(text: str, limit: int = 70) -> str:
    text = text.replace("|", "/").replace("\n", " ")
    return text if len(text) <= limit else text[: limit - 1] + "…"


def to_markdown(rows: list[dict], summary: dict, level: str) -> str:
    lines = [
        f"Roast level used: {level}",
        "",
        "| # | Language | Planted bug | Caught (auto) | Score | First bug reported |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for r in rows:
        if not r["ok"]:
            lines.append(
                f"| {r['id']} | {r['language']} | {_cell(r['planted_bug'])} | error | - | {_cell(r['error'])} |"
            )
            continue
        caught = "n/a (clean)" if r["clean"] else ("yes" if r["caught"] else "no")
        first = r["bugs"][0] if r["bugs"] else "(none)"
        lines.append(
            f"| {r['id']} | {r['language']} | {_cell(r['planted_bug'])} | {caught} | {r['score']} | {_cell(first)} |"
        )
    s = summary
    lines += [
        "",
        f"- Planted bugs caught: **{s['caught_auto']} out of {s['buggy_total']}** (keyword check; verify by hand)",
        f"- Average score on clean code: **{s['clean_avg_score']}** over {s['clean_total']} snippets",
        f"- Bugs invented on clean code: **{s['false_alarm_bugs']}**",
    ]
    if s["failed_calls"]:
        lines.append(f"- Calls that failed and were skipped: {s['failed_calls']}")
    return "\n".join(lines) + "\n"


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description="Mini evaluation for Roast My Code")
    parser.add_argument("--level", default="Sarcastic Senior")
    parser.add_argument("--delay", type=float, default=4.0, help="seconds between calls")
    parser.add_argument("--snippets", default=str(HERE / "snippets.json"))
    args = parser.parse_args(argv)

    snippets = json.loads(Path(args.snippets).read_text(encoding="utf-8"))
    rows = evaluate(snippets, args.level, args.delay)
    summary = summarize(rows)

    (HERE / "results.json").write_text(
        json.dumps({"level": args.level, "summary": summary, "rows": rows}, indent=2),
        encoding="utf-8",
    )
    markdown = to_markdown(rows, summary, args.level)
    (HERE / "results.md").write_text(markdown, encoding="utf-8")
    print("\n" + markdown)
    print("Saved eval/results.json and eval/results.md. Check each 'caught' by hand.")


if __name__ == "__main__":
    main()

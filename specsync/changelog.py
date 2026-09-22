"""When drift is found, turns the raw diagram diff into a short plain-English
summary via Groq's free tier, and appends it to CHANGELOG.md. Optional step,
check_drift.py works fine without it, this only makes the drift readable.
"""
import argparse
import datetime
import os
import sys

from groq import Groq

PROMPT = """You are summarizing a change to a software architecture diagram,
generated automatically from real import statements. Given this diff of the
PlantUML component diagram (before vs after), write 2-3 plain-English
sentences describing what actually changed structurally: new modules, new
or removed dependencies between modules. Be factual and specific, no
marketing language, no speculation about why it changed.

Diff:
{diff}
"""


def summarize(diff_text: str) -> str:
    client = Groq(api_key=os.environ["GROQ_API_KEY"])
    resp = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": PROMPT.format(diff=diff_text)}],
        temperature=0.1,
        max_tokens=200,
    )
    return resp.choices[0].message.content.strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("diff_file", help="path to a diff produced by check_drift.py")
    ap.add_argument("--changelog", default="CHANGELOG.md")
    args = ap.parse_args()

    diff_text = open(args.diff_file, encoding="utf-8").read()
    if not diff_text.strip():
        print("Empty diff, nothing to summarize.")
        return 0

    summary = summarize(diff_text)
    date = datetime.date.today().isoformat()
    entry = f"\n## {date}\n\n{summary}\n"

    with open(args.changelog, "a", encoding="utf-8") as f:
        f.write(entry)
    print(entry)
    return 0


if __name__ == "__main__":
    sys.exit(main())

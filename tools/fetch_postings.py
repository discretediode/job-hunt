#!/usr/bin/env python3
"""Create QUEUE/<slug>/posting.md for the day's picks.

Usage: python3 tools/fetch_postings.py <queue-dir> <job-id>:<slug> [...]

ponytail: detail.sh already prints a posting to stdout, but the queue needs it
archived per folder with the metadata header. One pass, curl like the rest.
"""
import html
import json
import pathlib
import re
import subprocess
import sys
import time

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/140.0 Safari/537.36")
HERE = pathlib.Path(__file__).resolve().parent.parent


def description(jid):
    url = "https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/" + jid
    h = subprocess.run(["curl", "-sS", "-A", UA, url],
                       capture_output=True, text=True).stdout
    m = re.search(r"show-more-less-html__markup(.*?)</div>\s*</section>", h, re.S)
    m = m or re.search(r"show-more-less-html__markup(.*?)</div>", h, re.S)
    if not m:
        return "NO DESCRIPTION RETURNED"
    t = re.sub(r"<(br|/p|/li|/ul|/h\d)[^>]*>", "\n", m.group(1))
    t = html.unescape(re.sub(r"<[^>]+>", "", t))
    t = re.sub(r"\n{3,}", "\n\n", re.sub(r"[ \t]+", " ", t)).strip()
    # The capture starts mid-attribute and ends in LinkedIn's expander chrome.
    t = re.sub(r"^[^>]*>\s*", "", t)
    return re.split(r"\n\s*Show more\s*\n", t)[0].strip()


def main():
    queue = pathlib.Path(sys.argv[1])
    jobs = {j["id"]: j for j in json.load(open(HERE / "ranked.json"))}
    for arg in sys.argv[2:]:
        jid, slug = arg.split(":", 1)
        j = jobs[jid]
        d = queue / slug
        d.mkdir(parents=True, exist_ok=True)
        txt = description(jid)
        (d / "posting.md").write_text(
            "# {}\n\n**Company:** {}\n**Location:** {}\n**Posted:** {}\n"
            "**Job ID:** {}\n**URL:** {}\n**Archived:** {}\n\n---\n\n{}\n".format(
                j["title"], j["company"], j["location"], j["posted"],
                jid, j["url"], queue.name, txt))
        print("{:52s} {:6d} chars".format(slug, len(txt)))
        time.sleep(1)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Fill the CV and cover-letter templates for every job in a queue's _tailoring.json.

Usage: python3 tools/make_app.py applications/<date> [spec-file]
       spec-file defaults to <queue>/_tailoring.json; pass another to run a
       second batch into the same day's queue without disturbing the first.

Writes per folder: cv.html, cover_letter.html, form_fields.txt, fit.md.
posting.md comes from `postings.py --archive`; the PDFs from `build.py render`.

ponytail: the CV is tailored at the tagline and the profile paragraph only. The
bullets below them are the same verified facts in every version, so rewriting them
per job would be ten chances to introduce a claim the vault does not support, and
the one-page fit is already proven for this exact body.
"""
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent.parent
ID = json.loads((HERE / "identity.local.json").read_text())


def strip_comments(html):
    """The templates carry authoring notes, including a literal __PLACEHOLDER__ in the
    cover letter's instructions. Those have no business in a file sent to an employer,
    and leaving them in makes the placeholder check below unusable."""
    return re.sub(r"<!--.*?-->\n?", "", html, flags=re.S)


def fill_cv(tpl, spec):
    tpl = strip_comments(tpl)
    out = re.sub(r'(<p class="tagline">).*?(</p>)',
                 lambda m: m.group(1) + spec["tagline"] + m.group(2), tpl, count=1, flags=re.S)
    # Watch the language order in a tailored profile: naming a lower-level language
    # immediately before a higher-level one trips the forbidden-claim guard, because the
    # phrasing is genuinely ambiguous about which level belongs to which language.
    out, n = re.subn(r'(<h2>Profile</h2>\s*<p class="tight">).*?(</p>)',
                     lambda m: m.group(1) + spec["profile"] + m.group(2), out, count=1, flags=re.S)
    if n != 1:
        raise RuntimeError("profile anchor not found in cv_master.html")
    return out


def fill_cover(tpl, spec):
    out = strip_comments(tpl).replace("Application for __ROLE_TITLE__", spec["heading"])
    out = out.replace("Kind regards,", spec["signoff"])
    if spec.get("letter_lang") != ID.get("search", {}).get("cv_language", "en"):
        # A letter in the local language must not carry the English spelling of the
        # sender's own city in its address block. The dateline is __DATELINE__, written
        # whole by the agent in the letter's own language - no city hardcoded here.
        out = out.replace(ID["postcode_city_en"], ID["postcode_city_local"])
    for key, val in spec["cover"].items():
        out = out.replace(key, val)
    left = re.findall(r"__[A-Z0-9_]+__", out)
    if left:
        raise RuntimeError("unfilled placeholders: " + ", ".join(sorted(set(left))))
    # __SALUTATION__ is the whole greeting line - the recipient placeholder belongs to the
    # address block. Passing a bare "Dear" shipped letters opening with "Dear" and nothing
    # else; a greeting always ends in punctuation, so check for it.
    greeting = re.search(r'<p class="salutation">(.*?)</p>', out, flags=re.S)
    if not greeting or not greeting.group(1).strip().endswith((",", ":", "!")):
        raise RuntimeError(f"incomplete salutation: {greeting and greeting.group(1).strip()!r}"
                           " - __SALUTATION__ must be the full greeting line")
    return out


def form_fields(spec):
    """Counts are measured here, never estimated: portals reject on the real number."""
    lines = [f"# Portal free-text answers - {spec['company']}: {spec['role']}",
             "# Counts measured by tools/make_app.py, not estimated.", ""]
    for item in spec["form_fields"]:
        a = item["a"]
        lines += [f"Q: {item['q']}",
                  f"   [{len(a)} characters | {len(a.split())} words]",
                  f"A: {a}", ""]
    return "\n".join(lines)


def main():
    queue = pathlib.Path(sys.argv[1])
    spec_file = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else queue / "_tailoring.json"
    specs = json.load(open(spec_file))
    cv_tpl = (HERE / "templates/cv_master.html").read_text()
    cover_tpl = (HERE / "templates/cover_master.html").read_text()
    for spec in specs:
        d = queue / spec["slug"]
        d.mkdir(parents=True, exist_ok=True)
        (d / "cv.html").write_text(fill_cv(cv_tpl, spec))
        (d / "cover_letter.html").write_text(fill_cover(cover_tpl, spec))
        (d / "form_fields.txt").write_text(form_fields(spec))
        (d / "fit.md").write_text(spec["fit"])
        print(f"  wrote {spec['slug']}")


if __name__ == "__main__":
    main()

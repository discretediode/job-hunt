#!/usr/bin/env python3
"""Append run 2 of 2026-10-02 to tracker.csv. csv.writer does the quoting, so a comma
or quote inside a note cannot shift the columns. Rewritten each run; tracker.csv is
the permanent record."""
import csv
import pathlib

Q = "applications/2026-10-02"
ROWS = [
 ("Infineon Technologies", "Semiconductors - test technology, digital mixed signal",
  "Working Student - Portfolio Management Support for Data Analytics (f/m/div)",
  "infineon_portfolio-management-data-analytics", "Werkstudent", "74 - Strong Fit",
  "English letter. Their requirement list names AI prompting, MCP, VScode, GitHub and Python - five of his strongest, and MCP stated outright in an advert is rare. Gaps said plainly: Knime, Tableau and JIRA never used, and JavaScript is not one of his languages (C/C++ and Python are). 20 h/week cap and a 6-month minimum stated by them; must live near site, he does. "
  "*** FLAG: THIS WOULD BE HIS FIFTH INFINEON APPLICATION IN TEN DAYS *** - tracker already holds 2026-09-23 AI-Assisted Embedded SW, 2026-09-30 Automation of Data Processing, and TWO on 2026-10-01 (AI & Automation for Semiconductor Dev, Data Analytics & AI). The two from 10-01 are among the seven letters with the broken 'Dear' greeting and may never have been sent. Five live applications to one employer dilutes all five. Decide deliberately before sending."),

 ("CLAR AI", "AI start-up - agentic systems deployed into logistics, ops, healthcare",
  "Forward Deployed Engineer (FDE) - Praktikum", "clar-ai_forward-deployed-engineer",
  "Praktikum (hours unresolved)", "72 - Strong Fit",
  "English letter. Closest subject match of the run: their 'AI Native' bullet names foundation models, retrieval, multi-agent architectures and external tools - the RAG project in their own words. UNMET STATED REQUIREMENT, led with rather than buried: cannot spin up a full-stack web app from scratch; React/TypeScript/NodeJS are not his, only Python and C/C++, with HTML/CSS limited to document rendering. The letter says outright that if the role needs production frontend from week one he is not the candidate. "
  "OPEN QUESTION ON HOURS: titled Praktikum with no hours anywhere in the advert and a culture section that disclaims 9-to-5; a form answer asks directly whether ~20 h/week works. Same trap as TRUSTEQ this morning - if it is full-time mid-semester, withdraw rather than negotiate the study load. On-site central Munich, no remote, occasional customer travel."),

 ("Micron Technology", "Semiconductors - DRAM design for graphics and AI markets",
  "DRAM Design Working Student in Munich (m/f/d)", "micron_dram-design", "Werkstudent",
  "68 - Good Fit",
  "English letter, no German requirement at all. THE ADVERT THE OLD KEYWORD SCORER WOULD HAVE MISSED COMPLETELY: 'DRAM Design' matched nothing in the retired WEIGHTS table, and VHDL/Verilog were not in it despite both being declared in skills.md. Preferred quals name Verilog, VHDL and Python scripting - the only posting in the whole tracker to ask for the HDLs he has. Gaps stated plainly: no Cadence, no Synopsys, no Spice, no prior IC-design project, Linux only command-line depth, and the HDL work is coursework not a taped-out design. All four sit under Preferred, not Required. "
  "Pay stated: from 15 EUR/h gross. NOTE: the advert says recruiters use automated tools to match skills and supplement the CV from public sources, and carries an explicit notice that AI-assisted applications are fine but misrepresentation means disqualification - this application complies, every claim traces to the vault."),

 ("Knorr-Bremse AG", "Rail and commercial vehicle systems - CVS division transformation programme",
  "Werkstudent Transformation Office (m/w/d)", "knorr-bremse_transformation-office", "Werkstudent",
  "58 - Good Fit",
  "German letter. 'Ingenieurwissenschaften' is named directly in the study list - no 'vergleichbar' stretch needed, unusual for this tracker. 'Erfahrungen mit Automatisierung oder der Anwendung von KI in betriebswirtschaftlichen Prozessen von Vorteil' is listed as an advantage and is his strongest area. Data-quality assurance maps onto his RAG ingestion work. Gaps stated openly: NO practical transformation, project-management or strategy experience (their 'idealerweise'), and his reporting background is a laboratory not a corporate programme. "
  "LANGUAGE FLAG: they ask for 'sehr gute Deutschkenntnisse'; he is C1. Per the standing rule that is a flag for his judgment, not an auto-reject - the letter states C1, cites the evidence, and explicitly leaves the sufficiency call to them instead of asserting it. SECOND KNORR-BREMSE APPLICATION: 2026-09-30 Werkstudent Produktvalidierung (Messtechnik/KI), different division. A third posting (Global CVS Financial M&A) was rejected by the pipeline on 2026-10-02. Honest read: the day-to-day is tracking, reports and management presentations, not building."),

 ("Userlane", "SaaS - software adoption platform for regulated industries",
  "Working student customer success (alternatively mandatory internship)",
  "userlane_customer-success", "Werkstudent", "45 - Weak Fit, the one to drop",
  "English letter. THE ONE TO DROP IF HE ONLY SENDS A FEW. Hours are the cleanest in the run - 15-20 h/week stated explicitly - and 'you use AI tools to work faster' is a stated requirement he meets better than most applicants will. English C2, German C1 with over a year of genuine German customer-facing work, and the technical-writing requirement is backed by the Arbeitszeugnis. "
  "MAIN RISK, named in the letter: the study-field list is business administration / management and technology / communication, with no honest route in for Mechatronics - the letter invites them to rule him out on it rather than bluffing. Also NO CRM and NO CS platform experience (Salesforce, HubSpot, Planhat, Gainsight all absent, listed as 'significant advantage'). HTML/CSS claim is evidenced via projects.md (xhtml2pdf + CSS) but framed honestly as document styling, not element selectors in a live customer app. "
  "THE APPLICATION IS THE WRITING SAMPLE: they ask one question in place of a cover letter - show a piece of writing for a non-technical audience and say where AI changed the approach. That answer in form_fields.txt is what they will actually read. Lowest technical content of the five; will not build the engineering record the other four would."),
]

path = pathlib.Path("tracker.csv")
with path.open("a", newline="") as f:
    w = csv.writer(f)
    for company, sector, role, slug, role_type, fit, notes in ROWS:
        w.writerow(["2026-10-02", company, sector, role, role_type, "LinkedIn",
                    "drafted", "", fit, notes,
                    f"{Q}/{slug}/cv.pdf", f"{Q}/{slug}/cover_letter.pdf",
                    "linkedin-search", ""])
print(f"appended {len(ROWS)} rows")

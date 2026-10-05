#!/usr/bin/env python3
"""Append this run's drafted rows to tracker.csv. csv.writer does the quoting, so a
comma or a quote inside a note cannot shift the columns.

Rewritten each run; the permanent record is tracker.csv itself.
"""
import csv
import pathlib

Q = "applications/2026-10-02"
ROWS = [
 ("TRUSTEQ GmbH", "IT consulting - cybersecurity, data, cloud and AI",
  "AI Developer Intern (m/w/d)", "trusteq_ai-developer-intern", "Werkstudent (hours unresolved)",
  "42 - Strong Fit",
  "German letter. Closest subject-matter match of the run: LangChain, Vektordatenbanken and ModelContextProtocol are named in the advert's own requirement list, and all three are in his RAG project. Meets the stated language bar (mind. C1 in both; he has German C1 via Feststellungspruefung 1.5 and English C2). UNMET STATED REQUIREMENT, said plainly in the letter: a second modern application language from JavaScript/TypeScript/Go/Java - he has C/C++. Also no Docker/Kubernetes, no DevOps pipelines, API integration rather than API design, no graph databases. OPEN QUESTION ON HOURS: titled Intern for 3-6 months, but benefits promise hours flexible around studies; a form answer asks directly whether it can run at 20h/week. If it is full-time mid-semester, withdraw rather than negotiate the study load."),
 ("ADAC", "Mobility club - international health cover and claims",
  "Werkstudent Datenanalyse Auslandskrankenschutz (w|m|d)",
  "adac_datenanalyse-auslandskrankenschutz", "Werkstudent", "30 - Good Fit",
  "German letter. Core task - turning raw source data into structured reports - is exactly the research-assistant work, where a Python script replaced a manual SFRA evaluation. Excel routine. Gaps stated openly: Power BI NEVER USED (and it is named in the advert), no insurance or health-services domain, SQL foundational. THE ADVERT HAS NO REQUIREMENTS SECTION AT ALL - only tasks and a benefits list: no hours, no duration, no study field, no language bar, no contact. Everything about the arrangement has to be asked. Ask specifically how much of the role is Power BI; if the answer is 'most of it' the fit is thinner than the task list suggests. ADAC Zentrale, Hansastrasse, central Munich."),
 ("HAT.tec", "Software start-up - aviation and defence, human autonomy teaming",
  "Werkstudent (m/w/d) Solution Engineering", "hat-tec_solution-engineering", "Werkstudent",
  "24 - Strong Fit on requirements",
  "German letter. Bland title scored 16; body earned a +8 override. THE ONLY ADVERT IN THIS RUN THAT NAMES MECHATRONIK in its own profile list, and he meets every stated requirement except Linux depth: Python/C++ yes, hardware-and-software setups yes, fault analysis yes, technical documentation yes (explicit vault skill), German and English yes. Gap stated openly: Linux only Grundkenntnisse - command line and Git daily, no sysadmin; no aviation, defence or unmanned-systems domain. TWO FLAGS: (1) DEFENCE AND AVIATION SECTOR - his call ethically, and defence firms often gate projects on citizenship or clearance, so as an Indonesian national he should ask early before investing interview time. (2) LOCATION IS NEUBIBERG, not Munich city - S7, ~25 min plus walk; check against his timetable. No hours or duration stated; 'ab sofort'."),
 ("coneva GmbH", "Energy software - energy management, flexibility and charging",
  "Werkstudent Customer Service & Operations - mit Draht ins Produktteam (m/w/d)",
  "coneva_customer-service-operations", "Werkstudent", "24 - Good Fit",
  "German letter. Opaque title scored 10; body earned a +14 override for Python/SQL deep-dives in data streams plus Grafana and Datadog. Best use of his service record in the whole tracker: eleven months of German customer-facing retail and event work counts as evidence here, not filler, alongside the measurement-data analysis. Meets the language bar exactly (German min C1, English min B2). KI-Tools requirement is one of his strongest points. Gaps stated openly: study-field list is business/energy-oriented (Mechatronics via 'vergleichbar', no energy focus), no Grafana, Datadog or Elixir, SQL foundational, no energy-market domain. FLAG: the role is service-first with the data work in support of it, not a data role with some customer contact - decide deliberately. No hours stated. Location given only as 'Greater Munich Metropolitan Area' - confirm the office address."),
 ("PwC Deutschland", "Professional services - IT transformation and CIO advisory",
  "Praktikant / Werkstudent im Bereich IT-Transformation/CIO Advisory (w/m/d)",
  "pwc_it-transformation-cio-advisory", "Werkstudent", "24 - Weak Fit",
  "German letter. WEAKEST OF THE SEVEN AND THE ONE TO DROP IF HE ONLY SENDS A FEW. Two bullets from 'Das bringst du mit' are unmet and both are stated flatly in the letter: (1) 'erste Praxiserfahrungen in Unternehmensberatungen und/oder Unternehmen aus der Industrie' - he has NEITHER; his technical experience is academic and his customer contact is retail and events. (2) Studiengang - Mechatronics against a (Wirtschafts-)Informatik/WiIng/BWL list, reachable only via 'vergleichbar'. Enterprise Architecture and sourcing concepts known as terms only. Met: 3rd Fachsemester cleared comfortably (4 done), MS Office/PowerPoint routine, German and English, and a genuine automation record. Combined Praktikant/Werkstudent advert - applied for the WERKSTUDENT track, stated in a form answer. Contact number in the advert: +49 69 9585-2222. Consulting means client sites and travel; not mentioned, so ask."),
 ("Hilti Deutschland", "Construction technology - engineering process digitalisation",
  "Working Student / Intern - Requirements Engineering & Digital Solutions (m/f/d)",
  "hilti_requirements-engineering-digital", "Werkstudent", "14 - Good Fit",
  "English letter. Title scored low (14); the description is a better match than the score - automation, dashboards, APIs, AI-powered solutions and low-code aimed at engineering processes. No override: the named advantageous tooling is Power Platform and BI, where he has nothing. Matched: Python, REST/Gemini API integration, AI and automation (his strongest area), proof-of-concept habit, English C2, independent ownership. Gaps stated openly: NO Microsoft Power Platform (Power Automate/Apps/BI), dashboards only in Python and Excel, requirements engineering entirely new, no JavaScript, SQL foundational. FLAGS: combined Working Student/Intern advert - applied for the working-student track with the 20h/week cap stated in a form answer. HILTI GROUP HQ IS SCHAAN, LIECHTENSTEIN - the posting says Munich, so CONFIRM the role is genuinely Munich-based; Liechtenstein would be a hard fail. 'Global stakeholders' may mean time-zone meetings - ask. No hours, duration or named contact."),
 ("YUVENDA Cinema Solutions", "Cinema POS and ticketing software (CINETIXX)",
  "Werkstudent (m/w/d) Support fuer Kinokassensystem / Kino-Ticket Software",
  "yuvenda_support-kinokassensystem", "Werkstudent", "10 - Honest Fit, low technical content",
  "German letter. Scored 10 on 'werkstudent' alone and the body does not raise it - this is phone and e-mail support with some software testing, not engineering. It stays on the list because, unlike the six exclusions, he genuinely qualifies on almost every stated requirement: enrolled in Greater Munich, confident on the phone, customer care, good technical understanding, software testing, structured working. Unusually direct relevance - he operated a POS terminal and balanced a till in a high-traffic Munich bakery, so he knows what a cinema cashier experiences when the system fails. Gap stated openly: 'sehr gute schriftliche Korrespondenz in deutscher Sprache' - his German is C1 (Feststellungspruefung 1.5) with over a year of customer work in German, but it is not native and written correspondence is a step up from counter conversation; the letter invites them to test it rather than claiming more. TWO FLAGS: (1) SHIFTS ARE Fri 18-22, Sat 16-22, Sun 10-16 and 16-22 - weekend evenings, a lifestyle decision not a skills question, and the letter accepts them, so only send it if he means it. (2) LOWEST TECHNICAL CONTENT OF THE SEVEN - 15 EUR/h (20 on holidays), four-week onboarding, home office possible after; steady income and German practice, but it will not build the engineering record the other six would. Advert asks for earliest start date; form answers say 'sofort'. Office near Hirschgarten/Westendstrasse."),
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

# jobhunt

An AI-powered job-hunting assistant. It automates the boring parts—searching for jobs and tailoring your application—so you can focus on the actual interviewing.

**It never submits anything.** The system creates a "review-ready" folder of tailored CVs and cover letters. You review them, make final tweaks, and hit send yourself.

## 🚀 Quick Start (For Claude Code Users)

If you are using [Claude Code](https://claude.com/claude-code), you don't need to run complex scripts. Just use these simple commands:

- `/setup` : **Start here.** Configures your profile. If you have a CV PDF in `documents/cv/`, it will automatically extract your info for you.
- `/scrape` : Searches LinkedIn for new jobs that match your profile.
- `/jobhunt` : The full pipeline. Scrapes new jobs $\rightarrow$ Ranks them $\rightarrow$ Writes tailored content for the top 10.
- `/schedule` : Sets up a daily automatic run so you wake up to new options every morning (requires your explicit approval).

---

## 🛠 How it Works

The system uses a "Vault" pattern. Instead of one giant configuration file, your professional history is stored in simple Markdown files (like notes in Obsidian). This makes it easy for the AI to read your real experience without hallucinating.

1. **Discovery**: `scrape.py` finds jobs on LinkedIn based on your search queries.
2. **Judgment**: `judge.py` reads your profile and the job description to score how well you fit.
3. **Tailoring**: `tailor.py` generates a punchy tagline and professional summary tailored specifically to that one job.
4. **Rendering**: `build.py` takes your HTML templates and turns them into professional PDFs.

## 📁 Your Information (Private)

To keep your data safe, the following folders and files are **never** uploaded to GitHub (they are in `.gitignore`):

| Location | What it is | How to fill it |
| :--- | :--- | :--- |
| `my_profile/` | Your experience, skills, and education | Use `/setup` or edit the `.md` files |
| `documents/` | Your diplomas and certificates | Drop your PDFs here |
| `identity.local.json` | Your email, phone, and search settings | Managed by `/setup` |
| `applications/` | Your generated CVs and letters | Created automatically by the agent |

## 🛡 Privacy & Safety

This repository is designed to be shared publicly while keeping your personal data private. 

- **PII Protection**: All personal files are gitignored.
- **Forbidden Claims**: You can list things the AI is *never* allowed to claim (e.g., "Do not claim I speak fluent Japanese") in your identity config to prevent AI hallucinations.
- **Deterministic Checks**: The system runs a final mechanical check on every PDF to ensure your email is extractable and no placeholders (like `[INSERT NAME]`) were left behind.

## 📖 Detailed Setup

For a step-by-step guide on configuring your templates and evidence files, see **[SETUP.md](SETUP.md)**.

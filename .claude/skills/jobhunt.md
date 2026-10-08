# Job Hunt Full Run
Execute the end-to-end pipeline from discovery to tailored application specs.

## Instructions
1. **Scrape**: Run `python3 scrape.py queries.txt`.
2. **Judge**: Run `python3 judge.py` to score and rank the new jobs.
3. **Tailor**: Run `python3 tailor.py` to generate tailored content for the top 10 jobs.
4. **Report**: Summarize the results (e.g., "Found X jobs, judged Y, tailored Z").
5. Inform the user that they can now use `build.py` or the agent to render the final PDFs.

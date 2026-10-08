# Schedule Daily Hunt
Install the background scheduler to automate the daily job discovery and judgment process.

## Instructions
1. **Explain the commitment**: Tell the user that this will install a macOS LaunchAgent that runs a background script every morning.
2. **Explicit Approval**: You MUST ask the user for explicit confirmation. Example: "This will set up a daily background task to scrape and judge jobs automatically. Do you acknowledge and approve this?"
3. **Execution**: ONLY if the user explicitly says "Yes" or "Approve", run `bash tools/install_schedule.sh`.
4. **Verification**: Confirm the installation was successful by reporting the output of the script.
5. **Uninstall**: Remind the user they can remove it any time with `bash tools/install_schedule.sh --uninstall`.

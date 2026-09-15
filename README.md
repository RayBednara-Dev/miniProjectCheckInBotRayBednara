### INF601 - Advanced Programming in Python
### Ray Bednara
### Scheduled Check-In Bot


# Scheduled Check-In Bot

A GitHub Actions workflow that runs once a day, comments on the day's check-in
post on the INF601 Practice Hub, and saves the data it collected from the API.

## Description

`checkin.py` calls the Practice Hub API to:

* Fetch recent posts tagged `check-in` from the instructor's account
  (author id read from `INSTRUCTOR_ID`) and pick out today's post (by UTC
  date), so a check-in-tagged post from another student never gets
  commented on by mistake.
* Post a comment on it to record the check-in. Check-in posts only accept
  comments inside a time window; if the window is closed the API returns
  `423 Locked`, which the script logs instead of failing.
* Save the raw posts data and a summary of what happened into `artifact/`.

The workflow in `.github/workflows/checkin.yml` runs this script daily on a
cron schedule, uploads `artifact/` as a GitHub Actions build artifact for that
run, and also commits the new files in `artifact/` back into the repo (the
workflow is granted `contents: write` permission for this), so the collected
data accumulates in git history over time instead of only living in each
run's temporary artifact download.

## Getting Started

### Dependencies

* Python 3.13
* Install required libraries with:
```
pip install -r requirements.txt
```

### Installing

* Register once at https://practice.fhsucyber.com (see the API Guide) to get
  an API token.
* For the scheduled workflow, add all three as repository secrets (Settings
  -> Secrets and variables -> Actions -> New repository secret)

### Executing program

* Run locally:
```
python checkin.py
```
* Or trigger the workflow manually on GitHub: Actions tab -> Daily Check-In ->
  Run workflow.
* Otherwise it runs automatically every day at 13:00 UTC (adjust the cron
  expression in `.github/workflows/checkin.yml` if your check-in window is at
  a different time).

## Help

If a run logs `window_closed`, the check-in post's time window had already
closed for the day; the data is still saved to `artifact/`. If a run logs
`no_post_found`, no post with "check-in" in the title was created for that
UTC date yet.

## Authors

Ray Bednara (ray.bednara@gmail.com)

## AI Usage

Claude Code was used to write `checkin.py` and the GitHub Actions workflow,
based on the Practice Hub's API Guide.

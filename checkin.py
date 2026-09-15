"""Daily check-in bot for the INF601 Practice Hub.

Each run:
1. Fetches recent posts tagged "check-in" from the instructor (author id
   from INSTRUCTOR_ID) and finds today's post (by UTC date), ignoring any
   check-in-tagged posts other students may create.
2. Posts a comment on it to record the check-in (handles the 423 Locked
   window-closed response instead of crashing).
3. Saves the raw API data it collected into artifact/ so the workflow can
   upload it as a build artifact.
"""

import json
import os
import sys
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import requests
from dotenv import load_dotenv

load_dotenv()

BASE = os.environ.get("API_BASE_URL")
TOKEN = os.environ.get("API_KEY")
ARTIFACT_DIR = "artifact"
INSTRUCTOR_AUTHOR_ID = os.environ.get("INSTRUCTOR_ID")  # only trust check-in posts from the instructor
CENTRAL = ZoneInfo("America/Chicago")  # handles CST/CDT automatically


class PracticeHubClient:
    def __init__(self, base_url, token):
        self.base = base_url.rstrip("/")
        self.headers = {"Authorization": f"Bearer {token}"}

    def list_posts(self, tag=None, author=None, limit=50):
        params = {"limit": limit}
        if tag:
            params["tag"] = tag
        if author is not None:
            params["author"] = author
        resp = requests.get(f"{self.base}/api/v1/posts", headers=self.headers, params=params)
        resp.raise_for_status()
        return resp.json()

    def add_comment(self, post_id, body):
        return requests.post(
            f"{self.base}/api/v1/posts/{post_id}/comments",
            headers=self.headers,
            json={"body": body},
        )


def find_todays_checkin(posts):
    today = datetime.now(timezone.utc).date()
    candidates = [
        p for p in posts
        if "check-in" in p["title"].lower()
        and datetime.fromisoformat(p["created_at"]).date() == today
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda p: p["created_at"])


def main():
    if not BASE:
        raise SystemExit("API_BASE_URL is not set - add it to .env locally or as a repo secret.")
    if not TOKEN:
        raise SystemExit("API_KEY is not set - add it to .env locally or as a repo secret.")
    if not INSTRUCTOR_AUTHOR_ID:
        raise SystemExit("INSTRUCTOR_ID is not set - add it to .env locally or as a repo secret.")

    os.makedirs(ARTIFACT_DIR, exist_ok=True)
    now_central = datetime.now(timezone.utc).astimezone(CENTRAL)
    run_stamp = now_central.strftime("%m/%d/%Y")
    file_stamp = now_central.strftime("%m-%d-%Y")  # run_stamp has slashes, unsafe for filenames
    client = PracticeHubClient(BASE, TOKEN)

    posts = client.list_posts(tag="check-in", author=int(INSTRUCTOR_AUTHOR_ID), limit=50)
    with open(f"{ARTIFACT_DIR}/posts_{file_stamp}.json", "w") as fh:
        json.dump(posts, fh, indent=2)

    result = {"run_stamp": run_stamp, "checkin_post": None, "status": None, "detail": None}

    post = find_todays_checkin(posts)
    if post is None:
        result["status"] = "no_post_found"
        print("No check-in post found for today (UTC). Data saved, nothing to comment on.")
    else:
        result["checkin_post"] = {"id": post["id"], "title": post["title"]}
        comment_body = f"Checked in via GitHub Actions on {run_stamp}"
        resp = client.add_comment(post["id"], comment_body)

        if resp.status_code == 201:
            result["status"] = "checked_in"
            result["detail"] = resp.json()
            print(f"Checked in on post {post['id']} ({post['title']!r}).")
        elif resp.status_code == 423:
            result["status"] = "window_closed"
            result["detail"] = resp.json()
            print(f"Check-in window closed for post {post['id']} ({post['title']!r}): {resp.text}")
        else:
            result["status"] = "error"
            result["detail"] = {"status_code": resp.status_code, "body": resp.text}
            print(f"Unexpected response ({resp.status_code}) commenting on post {post['id']}: {resp.text}")

    with open(f"{ARTIFACT_DIR}/checkin_log_{file_stamp}.json", "w") as fh:
        json.dump(result, fh, indent=2)

    if result["status"] == "error":
        sys.exit(1)


if __name__ == "__main__":
    main()

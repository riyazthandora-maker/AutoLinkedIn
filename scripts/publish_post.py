import os
import sys
from pathlib import Path

import requests


DRAFT_PATH = Path(__file__).parent.parent / "drafts" / "latest.md"
LINKEDIN_UGC_URL = "https://api.linkedin.com/v2/ugcPosts"
LINKEDIN_USERINFO_URL = "https://api.linkedin.com/v2/userinfo"


def get_author_urn(access_token: str) -> str:
    resp = requests.get(
        LINKEDIN_USERINFO_URL,
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=10,
    )
    resp.raise_for_status()
    sub = resp.json()["sub"]
    return f"urn:li:person:{sub}"


def publish_post(content: str, access_token: str) -> str:
    author_urn = get_author_urn(access_token)

    payload = {
        "author": author_urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": content},
                "shareMediaCategory": "NONE",
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
        },
    }

    resp = requests.post(
        LINKEDIN_UGC_URL,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0",
        },
        json=payload,
        timeout=15,
    )
    resp.raise_for_status()

    post_id = resp.headers.get("x-restli-id", "unknown")
    return post_id


def main() -> None:
    if not DRAFT_PATH.exists():
        print(f"ERROR: No draft found at {DRAFT_PATH}. Run generate_post.py first.")
        sys.exit(1)

    content = DRAFT_PATH.read_text(encoding="utf-8").strip()
    if not content:
        print("ERROR: Draft file is empty.")
        sys.exit(1)

    dry_run = os.environ.get("DRY_RUN", "false").lower() == "true"

    if dry_run:
        print("--- DRY RUN — post NOT published ---")
        print(content)
        print("--- END ---")
        return

    access_token = os.environ["LINKEDIN_ACCESS_TOKEN"].strip()

    print("Publishing to LinkedIn...")
    post_id = publish_post(content, access_token)
    print(f"Published successfully. Post ID: {post_id}")
    print(f"View at: https://www.linkedin.com/feed/")


if __name__ == "__main__":
    main()

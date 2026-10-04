import os
import sys
import time
from pathlib import Path

import requests


DRAFT_PATH = Path(__file__).parent.parent / "drafts" / "latest.md"
DRAFT_IMAGE_PATH = Path(__file__).parent.parent / "drafts" / "latest.png"
LINKEDIN_UGC_URL = "https://api.linkedin.com/v2/ugcPosts"
LINKEDIN_ASSETS_URL = "https://api.linkedin.com/v2/assets?action=registerUpload"
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


def register_image_upload(author_urn: str, access_token: str) -> tuple[str, str]:
    payload = {
        "registerUploadRequest": {
            "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
            "owner": author_urn,
            "serviceRelationships": [
                {
                    "relationshipType": "OWNER",
                    "identifier": "urn:li:userGeneratedContent",
                }
            ],
        }
    }
    resp = requests.post(
        LINKEDIN_ASSETS_URL,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0",
        },
        json=payload,
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    upload_url = data["value"]["uploadMechanism"][
        "com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"
    ]["uploadUrl"]
    asset_urn = data["value"]["asset"]
    return upload_url, asset_urn


def upload_image(upload_url: str, image_bytes: bytes, access_token: str) -> None:
    resp = requests.put(
        upload_url,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/octet-stream",
        },
        data=image_bytes,
        timeout=30,
    )
    resp.raise_for_status()


def publish_post(caption: str, asset_urn: str, access_token: str, author_urn: str) -> str:
    payload = {
        "author": author_urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": caption},
                "shareMediaCategory": "IMAGE",
                "media": [
                    {
                        "status": "READY",
                        "media": asset_urn,
                    }
                ],
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
    return resp.headers.get("x-restli-id", "unknown")


def main() -> None:
    if not DRAFT_PATH.exists():
        print(f"ERROR: No draft found at {DRAFT_PATH}. Run generate_post.py first.")
        sys.exit(1)
    if not DRAFT_IMAGE_PATH.exists():
        print(f"ERROR: No image found at {DRAFT_IMAGE_PATH}. Run generate_post.py first.")
        sys.exit(1)

    caption = DRAFT_PATH.read_text(encoding="utf-8").strip()
    if not caption:
        print("ERROR: Draft caption file is empty.")
        sys.exit(1)

    image_bytes = DRAFT_IMAGE_PATH.read_bytes()

    dry_run = os.environ.get("DRY_RUN", "false").lower() == "true"

    if dry_run:
        print("--- DRY RUN — post NOT published ---")
        print(f"Caption : {caption}")
        print(f"Image   : {len(image_bytes):,} bytes ({DRAFT_IMAGE_PATH})")
        print("--- END ---")
        return

    access_token = os.environ["LINKEDIN_ACCESS_TOKEN"].strip()

    print("Fetching author URN...")
    author_urn = get_author_urn(access_token)

    print("Step 1: Registering image upload...")
    upload_url, asset_urn = register_image_upload(author_urn, access_token)
    print(f"Asset URN: {asset_urn}")

    print("Step 2: Uploading image...")
    upload_image(upload_url, image_bytes, access_token)
    print("Image uploaded.")

    print("Step 3: Creating LinkedIn post...")
    post_id = None
    for attempt in range(3):
        try:
            post_id = publish_post(caption, asset_urn, access_token, author_urn)
            break
        except requests.HTTPError as e:
            if attempt < 2 and e.response.status_code == 422:
                print(f"Asset not ready, retrying in 3s... (attempt {attempt + 1})")
                time.sleep(3)
            else:
                raise

    print(f"Published successfully. Post ID: {post_id}")
    print("View at: https://www.linkedin.com/feed/")


if __name__ == "__main__":
    main()

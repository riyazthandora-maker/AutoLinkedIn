import os
import datetime
from pathlib import Path

from google import genai
from google.genai import types
import resend


REPO_ROOT = Path(__file__).parent.parent
SYSTEM_PROMPT_PATH = REPO_ROOT / "prompts" / "system_prompt.txt"
DRAFT_PATH = REPO_ROOT / "drafts" / "latest.md"


def load_system_prompt() -> str:
    return SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")


def generate_post(api_key: str) -> str:
    client = genai.Client(api_key=api_key)

    today = datetime.date.today()
    week_ago = today - datetime.timedelta(days=7)

    user_prompt = (
        f"Today is {today.strftime('%A, %B %d, %Y')}. "
        f"Find the top tech stories published between {week_ago.strftime('%B %d')} and {today.strftime('%B %d, %Y')} "
        f"that fit the 3 content buckets: major AI model releases, OpEx-cutting tools/platforms, and corporate tech M&A or strategic pivots. "
        f"Write the LinkedIn post following the format in your instructions exactly."
    )

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=user_prompt,
        config=types.GenerateContentConfig(
            system_instruction=load_system_prompt(),
            tools=[types.Tool(google_search=types.GoogleSearch())],
            temperature=0.7,
        ),
    )

    return response.text.strip()


def save_draft(content: str) -> None:
    DRAFT_PATH.parent.mkdir(parents=True, exist_ok=True)
    DRAFT_PATH.write_text(content, encoding="utf-8")
    print(f"Draft saved to {DRAFT_PATH}")


def send_email(content: str, repo: str) -> None:
    resend.api_key = os.environ["RESEND_API_KEY"]
    from_email = os.environ.get("RESEND_FROM_EMAIL", "linkedin-bot@gnosiscore.org")
    today = datetime.date.today()

    publish_url = f"https://github.com/{repo}/actions/workflows/publish.yml"

    html_body = f"""
<html>
<body style="font-family: Arial, sans-serif; max-width: 640px; margin: 0 auto; padding: 24px;">
  <h2 style="color: #0a66c2;">LinkedIn Draft Ready — {today.strftime('%B %d, %Y')}</h2>
  <p>Your weekly LinkedIn post has been generated. Review it below, then publish when ready.</p>

  <div style="background: #f3f4f6; border-left: 4px solid #0a66c2; padding: 16px 20px; margin: 24px 0; white-space: pre-wrap; font-family: monospace; font-size: 14px; line-height: 1.6;">
{content}
  </div>

  <p>
    <a href="{publish_url}"
       style="display: inline-block; background: #0a66c2; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; font-weight: bold;">
      Publish to LinkedIn →
    </a>
  </p>
  <p style="color: #6b7280; font-size: 12px;">
    Click the link above → "Run workflow" → confirm. Token expires in 60 days — re-run setup_linkedin_auth.py if it fails.
  </p>
</body>
</html>
"""

    resend.Emails.send({
        "from": f"LinkedIn Bot <{from_email}>",
        "to": ["riyazthandora@gmail.com"],
        "subject": f"LinkedIn Draft — Week of {today.strftime('%b %d, %Y')}",
        "html": html_body,
    })

    print("Email sent successfully.")


def main() -> None:
    api_key = os.environ["GEMINI_API_KEY"]
    repo = os.environ.get("GITHUB_REPOSITORY", "your-username/LinkedInPost")

    print("Generating post via Gemini 2.0 Flash...")
    post = generate_post(api_key)

    print("\n--- GENERATED POST ---")
    print(post)
    print("--- END POST ---\n")

    save_draft(post)
    send_email(post, repo)


if __name__ == "__main__":
    main()

import os
import base64
import datetime
from pathlib import Path

from google import genai
from google.genai import types
import resend


REPO_ROOT = Path(__file__).parent.parent
DRAFT_PATH = REPO_ROOT / "drafts" / "latest.md"
DRAFT_IMAGE_PATH = REPO_ROOT / "drafts" / "latest.png"


def get_top_story(api_key: str) -> tuple[str, str]:
    client = genai.Client(api_key=api_key)
    today = datetime.date.today()
    week_ago = today - datetime.timedelta(days=7)

    user_prompt = (
        f"Today is {today.strftime('%A, %B %d, %Y')}. "
        f"Search the web and find the single biggest tech news story from the past 7 days "
        f"({week_ago.strftime('%B %d')} to {today.strftime('%B %d, %Y')}). "
        f"Reply in exactly two lines:\n"
        f"CAPTION: [one declarative sentence, max 15 words, summarising the story]\n"
        f"SKETCH: [describe a single visual scene that represents this story — "
        f"suitable for a minimalist pencil sketch, no text, no logos, no abstract concepts — "
        f"describe real objects and people only, e.g. 'a engineer standing next to a large server rack']"
    )

    model = os.environ.get("GEMINI_MODEL") or "gemini-2.5-flash"
    response = client.models.generate_content(
        model=model,
        contents=user_prompt,
        config=types.GenerateContentConfig(
            tools=[types.Tool(google_search=types.GoogleSearch())],
            temperature=0.4,
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        ),
    )

    text = response.text.strip()
    caption, sketch_description = "", ""
    for line in text.splitlines():
        if line.startswith("CAPTION:"):
            caption = line.removeprefix("CAPTION:").strip()
        elif line.startswith("SKETCH:"):
            sketch_description = line.removeprefix("SKETCH:").strip()

    if not caption or not sketch_description:
        raise ValueError(f"Could not parse Gemini response:\n{text}")

    return caption, sketch_description


def build_imagen_prompt(sketch_description: str) -> str:
    return (
        f"{sketch_description}. "
        "Minimalist pencil sketch style, hand-drawn look, thin clean pencil outlines, "
        "white background, no color, no shading fill, no text, no logos, "
        "news editorial illustration style."
    )


def generate_sketch(api_key: str, imagen_prompt: str) -> bytes:
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model="imagen-3.0-generate-002",
        contents=imagen_prompt,
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE"],
            image_config=types.ImageConfig(aspect_ratio="1:1"),
        ),
    )
    if response.candidates and response.candidates[0].content:
        for part in response.candidates[0].content.parts:
            if part.inline_data:
                return part.inline_data.data
    raise ValueError("No image data found in response.")


def save_draft(caption: str, image_bytes: bytes) -> None:
    DRAFT_PATH.parent.mkdir(parents=True, exist_ok=True)
    DRAFT_PATH.write_text(caption, encoding="utf-8")
    DRAFT_IMAGE_PATH.write_bytes(image_bytes)
    print(f"Caption saved to {DRAFT_PATH}")
    print(f"Image saved to {DRAFT_IMAGE_PATH}")


def send_email(caption: str, image_bytes: bytes, repo: str) -> None:
    resend.api_key = os.environ["RESEND_API_KEY"]
    from_email = os.environ.get("RESEND_FROM_EMAIL", "linkedin-bot@gnosiscore.org")
    today = datetime.date.today()

    publish_url = f"https://github.com/{repo}/actions/workflows/publish.yml"
    img_b64 = base64.b64encode(image_bytes).decode("utf-8")

    html_body = f"""
<html>
<body style="font-family: Arial, sans-serif; max-width: 640px; margin: 0 auto; padding: 24px;">
  <h2 style="color: #0a66c2;">LinkedIn Draft Ready — {today.strftime('%B %d, %Y')}</h2>
  <p>Your weekly LinkedIn sketch post has been generated. Review it below, then publish when ready.</p>

  <img src="data:image/png;base64,{img_b64}"
       style="max-width: 400px; display: block; margin: 0 auto 16px; border: 1px solid #e5e7eb;" />

  <div style="background: #f3f4f6; border-left: 4px solid #0a66c2; padding: 16px 20px; margin: 24px 0;
              font-family: monospace; font-size: 14px; line-height: 1.6;">
    {caption}
  </div>

  <p>
    <a href="{publish_url}"
       style="display: inline-block; background: #0a66c2; color: white; padding: 12px 24px;
              text-decoration: none; border-radius: 4px; font-weight: bold;">
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

    model = os.environ.get("GEMINI_MODEL") or "gemini-2.5-flash"
    print(f"Step 1: Finding this week's top story via {model}...")
    caption, sketch_description = get_top_story(api_key)

    print(f"Caption : {caption}")
    print(f"Sketch  : {sketch_description}\n")

    print("Step 2: Generating pencil sketch via Imagen 3...")
    imagen_prompt = build_imagen_prompt(sketch_description)
    image_bytes = generate_sketch(api_key, imagen_prompt)

    save_draft(caption, image_bytes)
    send_email(caption, image_bytes, repo)


if __name__ == "__main__":
    main()

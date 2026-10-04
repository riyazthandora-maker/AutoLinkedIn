"""
Test script: finds this week's top tech story via Gemini + generates a pencil sketch via Imagen.

Run:
    python test_sketch.py

Output:
    test_sketch.png  — open this to check the generated image
"""

import os
import datetime
from pathlib import Path

from google import genai
from google.genai import types


def get_top_story_and_sketch_prompt(client: genai.Client) -> tuple[str, str]:
    today = datetime.date.today()
    week_ago = today - datetime.timedelta(days=7)

    user_prompt = (
        f"Today is {today.strftime('%A, %B %d, %Y')}. "
        f"Search the web and find the single biggest tech news story from the past 7 days "
        f"({week_ago.strftime('%B %d')} to {today.strftime('%B %d, %Y')}). "
        f"Reply in exactly two lines:\n"
        f"CAPTION: [one sentence, max 15 words, summarising the story for a LinkedIn post]\n"
        f"SKETCH: [describe a single visual scene that represents this story — "
        f"suitable for a minimalist pencil sketch, no text, no logos, no abstract concepts — "
        f"describe real objects and people only, e.g. 'a engineer standing next to a large server rack']"
    )

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=user_prompt,
        config=types.GenerateContentConfig(
            tools=[types.Tool(google_search=types.GoogleSearch())],
            temperature=0.4,
        ),
    )

    text = response.text.strip()
    print("\n--- Gemini response ---")
    print(text)
    print("-----------------------\n")

    caption, sketch_description = "", ""
    for line in text.splitlines():
        if line.startswith("CAPTION:"):
            caption = line.removeprefix("CAPTION:").strip()
        elif line.startswith("SKETCH:"):
            sketch_description = line.removeprefix("SKETCH:").strip()

    return caption, sketch_description


def build_imagen_prompt(sketch_description: str) -> str:
    return (
        f"{sketch_description}. "
        "Minimalist pencil sketch style, hand-drawn look, thin clean pencil outlines, "
        "white background, no color, no shading fill, no text, no logos, "
        "news editorial illustration style."
    )


def generate_sketch(api_key: str, imagen_prompt: str) -> bytes:
    print(f"Image prompt:\n  {imagen_prompt}\n")
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=imagen_prompt,
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE"],
        ),
    )
    for part in response.candidates[0].content.parts:
        if part.inline_data is not None:
            return part.inline_data.data
    raise RuntimeError("No image returned — prompt may have been blocked by safety filters.")


def main() -> None:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: Set GEMINI_API_KEY as an environment variable first.")
        return

    client = genai.Client(api_key=api_key)

    print("Step 1: Finding this week's top story...")
    caption, sketch_description = get_top_story_and_sketch_prompt(client)

    if not caption or not sketch_description:
        print("ERROR: Could not parse Gemini response. See output above.")
        return

    print(f"Caption : {caption}")
    print(f"Sketch  : {sketch_description}\n")

    print("Step 2: Generating pencil sketch via Imagen...")
    imagen_prompt = build_imagen_prompt(sketch_description)
    image_bytes = generate_sketch(api_key, imagen_prompt)

    output_path = Path("test_sketch.png")
    output_path.write_bytes(image_bytes)
    print(f"Image saved to: {output_path.resolve()}")
    print("\nOpen test_sketch.png and check if the style looks right.")
    print("If it does, reply 'looks good' and I'll wire this into the main pipeline.")


if __name__ == "__main__":
    main()

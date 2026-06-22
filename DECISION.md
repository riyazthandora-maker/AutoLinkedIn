# LinkedIn Weekly Post Automation — Architecture Decision

**Date:** 2026-06-21  
**Status:** Decided — ready to build

---

## Goal

Automated job that runs every Monday, generates a weekly tech roundup LinkedIn post using AI, and publishes it to LinkedIn — with zero manual effort.

---

## The Post Format

A structured weekly tech roundup targeting **senior IT professionals, directors, and executives**.

**Content buckets (max 5 items/week):**
1. Major AI model releases or breakthroughs
2. Technologies/tools that cut corporate OpEx
3. Major corporate tech mergers, acquisitions, or strategic shifts

**Per-item format (strict 3-line structure):**
```
🚀 [Catchy 4-5 word headline]
• WHAT & WHERE: [1 sentence: what the tech is + real-world use case]
• THE ROI: [1 sentence: specific benefit, financial impact, or cost reduction]
```

**Post structure:**
- Strong FOMO hook (1 line) at the top
- Up to 5 items using the format above
- Sharp closing question inviting comments
- 3–4 hashtags at the very bottom only

---

## Technology Stack Decision

### Scheduler
**GitHub Actions** (free tier)
- Cron trigger: every Monday at 9:00 AM
- 2,000 free minutes/month — more than enough for 4 posts/month
- Secrets stored in GitHub Secrets (free)

### AI Model — Primary Recommendation
**Gemini 2.0 Flash + Google Search Grounding**
- Google Search index = best real-time news coverage
- Follows structured formatting prompts well
- Cost: ~$0.01/post (cheapest viable option)
- Single API call: search + write in one shot

### AI Model — Upgrade Path (if quality disappoints)
**GPT-4o + Web Search (OpenAI Responses API)**
- Best single-model option for complex formatting + live search
- Excellent editorial judgment on the 3 specific buckets
- Cost: ~$0.03–0.08/post

### Publisher
**LinkedIn UGC Posts API**
- Free
- Requires a LinkedIn Developer App + OAuth 2.0
- Access tokens expire every 60 days (refresh tokens: 365 days)
- One-time setup; annual re-auth needed

---

## Why NOT Perplexity (alone)

Perplexity Sonar is an excellent researcher but a weak writer for this use case:
- Built for "answer mode" — not creative LinkedIn structure
- Struggles to follow the strict 3-line format consistently
- Hook and CTA quality is poor (Wikipedia tone, not punchy B2B)
- Editorial discrimination (filtering to YOUR 3 buckets) is weaker than GPT-4o/Gemini

**If used:** Perplexity works best as a research layer only, feeding results into Claude for final writing (hybrid pattern — more complex, higher quality ceiling).

---

## Model Comparison Summary

| Model | Live Search | Format Adherence | Writing Quality | Cost/Post |
|---|---|---|---|---|
| Gemini 2.0 Flash + Google | Excellent | Good | Good | ~$0.01 |
| GPT-4o + Web Search | Good | Excellent | Excellent | ~$0.05 |
| Perplexity + Claude (hybrid) | Excellent | Excellent | Excellent | ~$0.03 |
| Perplexity alone | Excellent | Weak | Weak | ~$0.01 |
| Grok 3 | Excellent (X/Twitter) | Moderate | Good | Moderate |

---

## Pipeline Architecture

```
GitHub Actions (Monday 9am)
  │
  ▼
Python/Node script
  │
  ├─► Gemini 2.0 Flash API
  │     └─ prompt: system prompt + "find top 5 tech stories this week"
  │     └─ Google Search grounding enabled
  │     └─ returns: formatted LinkedIn post
  │
  └─► LinkedIn UGC Posts API
        └─ publishes the post
```

---

## Next Steps (when ready to build)

1. Create LinkedIn Developer App + get OAuth tokens
2. Set up GitHub repo with Actions workflow (cron Monday 9am)
3. Write the script (Python recommended — clean Gemini + LinkedIn SDK support)
4. Add secrets to GitHub: `GEMINI_API_KEY`, `LINKEDIN_ACCESS_TOKEN`
5. Test with a dry-run (print post, don't publish) for 1–2 weeks
6. Enable live publishing

---

## Open Questions

- [ ] What topic/persona should the hook reflect? (general CTO lens, or specific industry?)
- [ ] Should the post include a source link per item, or keep it clean?
- [ ] Manual approval step before publishing, or fully automated?
- [ ] LinkedIn personal profile post, or company page post?

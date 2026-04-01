# Story Weaver

Collaborative AI storytelling app built with Streamlit and OpenRouter.

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Copy `.env.example` to `.env` and add your key:
   ```bash
   cp .env.example .env
   ```
   Get a free key at [openrouter.ai](https://openrouter.ai).

3. Run:
   ```bash
   streamlit run app.py
   ```

## Model/Provider

**Provider:** OpenRouter
**Model:** `meta-llama/llama-3.3-70b-instruct:free` (free tier)

## Prompt

System prompt:
```
You are a collaborative storyteller writing a {genre} story called "{title}".
Genre rules: {rules}
Stay fully consistent with earlier parts of the story.
Don't contradict anything established earlier. Write in third-person narrative.
```

## Memory/Consistency

The `parts` list is joined into one string and sent with every request. Genre rules are re-stated in every system prompt.

## Bonus Features

- **Undo Last Turn** — removes the last entry from `parts`
- **Export as Markdown** — downloads the full story as a `.md` file

## What Didn't Work at First

I had to try multiple providers because the limit was reached too quickly on many, had to test each provider. Also the parsing broke when the model used `1)` or `1 .` instead of `1.`. The first version only checked `line.startswith("1.")`. Fixed by checking `line[1] in ".)"`.

## What I'd Improve Next

- Split up very long stories and include a short summary, right now context grows unbounded
-I would organize the code a little better, could use a class for story state and prompt building
- Make the model easier to change instead of hardcoding, maybe LLM gateway
- Retry on rate limit with a visible countdown instead of just an error message
- Genre switch button that rewrites the latest section in a different genre while keeping the characters and similar plot

import streamlit as st
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

MODEL = "meta-llama/llama-3.3-70b-instruct"

GENRES = ["Fantasy", "Sci-Fi", "Mystery", "Romance", "Horror", "Comedy"]

RULES = {
    "Fantasy": "Use magic elements, wild quests, and epic creatures. Keep language detailed and exciting.",
    "Sci-Fi": "Set the story in futuristic tech or science. Be imaginative but theoretically logical.",
    "Mystery": "Build suspense, hint clues, and keep the reader guessing. Every detail matters!",
    "Romance": "Focus on emotional tension and heartfelt moments between characters.",
    "Horror": "Create dread through atmosphere. Use the unknown to hook the reader.",
    "Comedy": "Keep things light. Use wit, irony, and funny situations.",
}


def sys_prompt(genre, title):
    base = f"You are a collaborative storyteller writing a {genre} story called \"{title}\".\n"
    base += f"Genre rules: {RULES[genre]}\n"
    base += "Stay fully consistent with earlier parts of the story. "
    base += "Don't contradict anything established earlier. Write in third-person narrative."
    return base


def call(messages, temp):
    try:
        resp = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=temp,
            max_tokens=1024,
            timeout=30,
        )
        text = resp.choices[0].message.content
        return text, None
    except Exception as e:
        err = str(e)
        if "429" in err or "rate" in err.lower() or "quota" in err.lower():
            return None, "Rate limit reached. Please wait a moment and try again."
        return None, f"Error: {err}"


def start_story(title, genre, hook, temp):
    system = {"role": "system", "content": sys_prompt(genre, title)}
    prompt = f"Title: {title}\nGenre: {genre}\nOpening hook: {hook}\n\n"
    prompt += "Write the opening paragraph (150-250 words). Hook the reader right away, "
    prompt += "set the tone, introduce the world, hint at the conflict. Don't resolve anything yet."
    user = {"role": "user", "content": prompt}
    messages = [system, user]
    return call(messages, temp)


def continue_story(title, genre, story, addition, temp):
    body = story
    if addition and addition.strip():
        body += "\n\n" + addition.strip()
    system = {"role": "system", "content": sys_prompt(genre, title)}
    prompt = f"Story so far:\n{body}\n\nWrite 1-2 more paragraphs. Keep the same tone."
    user = {"role": "user", "content": prompt}
    messages = [system, user]
    return call(messages, temp)


def get_choices(title, genre, story, temp):
    system = {"role": "system", "content": sys_prompt(genre, title)}
    prompt = f"Story so far:\n{story}\n\n"
    prompt += "Give 3 different ways the story could go next. Format:\n"
    prompt += "1. [option - 1-2 sentences]\n"
    prompt += "2. [option - 1-2 sentences]\n"
    prompt += "3. [option - 1-2 sentences]\n\n"
    prompt += "Make them actually different from each other."
    user = {"role": "user", "content": prompt}
    messages = [system, user]
    return call(messages, temp)


def pick_choice(title, genre, story, chosen, temp):
    system = {"role": "system", "content": sys_prompt(genre, title)}
    prompt = f"Story so far:\n{story}\n\n"
    prompt += f"Continue based on this: {chosen}\n\n"
    prompt += "Write 1-2 paragraphs. Stay consistent with what came before."
    user = {"role": "user", "content": prompt}
    messages = [system, user]
    return call(messages, temp)


def parse_choices(raw):
    choices = []
    for line in raw.strip().split("\n"):
        line = line.strip()
        if len(line) > 2 and line[0] in "123" and line[1] in ".)":
            choices.append(line[2:].strip())
    # backup
    if len(choices) < 2:
        chunks = [c.strip() for c in raw.split("\n\n") if c.strip()]
        if chunks:
            choices = chunks[:3]
        else:
            choices = [raw]
    return choices[:3]


def full_story():
    return "\n\n".join(st.session_state.parts)


def init():
    if "started" not in st.session_state:
        st.session_state.started = False
    if "title" not in st.session_state:
        st.session_state.title = ""
    if "genre" not in st.session_state:
        st.session_state.genre = "Fantasy"
    if "hook" not in st.session_state:
        st.session_state.hook = ""
    if "parts" not in st.session_state:
        st.session_state.parts = []
    if "choices" not in st.session_state:
        st.session_state.choices = []
    if "show_choices" not in st.session_state:
        st.session_state.show_choices = False
    if "temp" not in st.session_state:
        st.session_state.temp = 0.8


init()

st.set_page_config(page_title="Story Weaver", layout="wide")
st.title("Story Weaver")
st.caption("Collaborative AI storytelling")

if not os.getenv("OPENROUTER_API_KEY"):
    st.warning("OPENROUTER_API_KEY not set. Add it to your .env file.")

if not st.session_state.started:
    st.subheader("New Story")

    c1, c2 = st.columns(2)
    with c1:
        title = st.text_input("Title", placeholder="The Last Signal")
    with c2:
        genre = st.selectbox("Genre", GENRES)

    hook = st.text_area(
        "Opening Hook / Setting",
        placeholder="Describe your world, opening situation, or main character...",
        height=130,
    )

    st.session_state.temp = st.slider("Creativity", 0.0, 1.0, 0.8, 0.05)

    ready = title and hook
    if st.button("Start the Story", type="primary", disabled=not ready):
        with st.spinner("Writing opening..."):
            text, err = start_story(title, genre, hook, st.session_state.temp)
        if err:
            st.error(err)
        else:
            st.session_state.title = title
            st.session_state.genre = genre
            st.session_state.hook = hook
            st.session_state.parts = [text]
            st.session_state.started = True
            st.rerun()

else:
    with st.sidebar:
        st.markdown(f"**{st.session_state.title}**")
        st.markdown(f"Genre: {st.session_state.genre}")
        st.info(RULES[st.session_state.genre])

        st.divider()
        st.session_state.temp = st.slider("Creativity", 0.0, 1.0, st.session_state.temp, 0.05)

        st.divider()
        story_md = "# " + st.session_state.title + "\n\n"
        story_md += "Genre: " + st.session_state.genre + "\n\n---\n\n"
        story_md += full_story()
        filename = st.session_state.title + ".md"
        st.download_button("Export as Markdown", story_md, filename, "text/markdown", use_container_width=True)

        if st.button("Start Over", use_container_width=True):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()

    story = full_story()

    st.markdown(f"### {st.session_state.title}")
    word_count = len(story.split())
    st.caption(f"{st.session_state.genre}  —  {word_count} words")

    with st.container(border=True):
        for i, part in enumerate(st.session_state.parts):
            st.markdown(part)
            if i < len(st.session_state.parts) - 1:
                st.markdown("---")

    st.markdown("---")

    addition = st.text_area("Add your own lines (optional)", height=80, placeholder="The door creaked open...")

    c1, c2, c3 = st.columns(3)

    with c1:
        if st.button("Continue with AI", type="primary", use_container_width=True):
            st.session_state.show_choices = False
            st.session_state.choices = []
            with st.spinner("Writing..."):
                text, err = continue_story(
                    st.session_state.title,
                    st.session_state.genre,
                    story,
                    addition,
                    st.session_state.temp,
                )
            if err:
                st.error(err)
            else:
                if addition and addition.strip():
                    part = addition.strip() + "\n\n" + text
                else:
                    part = text
                st.session_state.parts.append(part)
                st.rerun()

    with c2:
        if st.button("Give Me Choices", use_container_width=True):
            with st.spinner("Thinking..."):
                raw, err = get_choices(
                    st.session_state.title,
                    st.session_state.genre,
                    story,
                    st.session_state.temp,
                )
            if err:
                st.error(err)
            else:
                st.session_state.choices = parse_choices(raw)
                st.session_state.show_choices = True
                st.rerun()

    with c3:
        can_undo = len(st.session_state.parts) > 1
        if st.button("Undo Last Turn", disabled=not can_undo, use_container_width=True):
            st.session_state.parts.pop()
            st.session_state.show_choices = False
            st.session_state.choices = []
            st.rerun()

    if st.session_state.show_choices and st.session_state.choices:
        st.markdown("### Choose a direction")
        for i, choice in enumerate(st.session_state.choices):
            label = f"Option {i + 1}: {choice}"
            if st.button(label, key=f"c{i}", use_container_width=True):
                with st.spinner("Continuing..."):
                    text, err = pick_choice(
                        st.session_state.title,
                        st.session_state.genre,
                        story,
                        choice,
                        st.session_state.temp,
                    )
                if err:
                    st.error(err)
                else:
                    st.session_state.parts.append("[Chosen path] " + choice)
                    st.session_state.parts.append(text)
                    st.session_state.show_choices = False
                    st.session_state.choices = []
                    st.rerun()

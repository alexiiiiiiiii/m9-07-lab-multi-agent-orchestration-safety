import asyncio
import os
import json
from google.adk.agents.llm_agent import LlmAgent
from google.adk.agents.sequential_agent import SequentialAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

def load_notes():
    with open("notes.json", "r") as f:
        return json.load(f)

def screen_text(text):
    parts = text.split("\n\n")
    clean_parts = []
    for p in parts:
        lower_p = p.lower()
        if "ignore all" in lower_p or "attention system" in lower_p or "system compromised" in lower_p:
            continue
        clean_parts.append(p)
    return "\n\n".join(clean_parts).strip()

def format_notes(notes, screen=False):
    parts = []
    for n in notes:
        text = n["text"]
        if screen:
            text = screen_text(text)
        parts.append(f"Note ID: {n['id']}\nText: {text}")
    return "\n\n".join(parts)

async def run_pipeline(notes, screen=False):
    formatted = format_notes(notes, screen)
    summary_agent = LlmAgent(
        name="summary_agent",
        model="gemini-2.0-flash",
        instruction="Summarize the input business notes into a single paragraph of update.",
        output_key="summary"
    )
    headline_agent = LlmAgent(
        name="headline_agent",
        model="gemini-2.0-flash",
        instruction="Take the summary stored in the session state under 'summary' and turn it into a single punchy headline."
    )
    pipeline = SequentialAgent(
        name="pipeline",
        sub_agents=[summary_agent, headline_agent]
    )
    session_service = InMemorySessionService()
    runner = Runner(agent=pipeline, session_service=session_service, app_name="business_pipeline")
    events = await runner.run_debug(formatted)
    summary_text = ""
    headline_text = ""
    for event in events:
        if getattr(event, "author", None) == "summary_agent":
            if event.content and event.content.parts:
                summary_text = event.content.parts[0].text
        elif getattr(event, "author", None) == "headline_agent":
            if event.content and event.content.parts:
                headline_text = event.content.parts[0].text
    return summary_text, headline_text

async def main():
    notes = load_notes()
    summary, headline = await run_pipeline(notes, screen=True)
    print("Summary:", summary)
    print("Headline:", headline)

if __name__ == "__main__":
    asyncio.run(main())

# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
import json
from pathlib import Path
from zoneinfo import ZoneInfo

from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.code_executors import AgentEngineSandboxCodeExecutor
from google.adk.memory.vertex_ai_memory_bank_service import VertexAiMemoryBankService
from google.adk.models import Gemini
from google.adk.tools import load_memory, preload_memory
from google.genai import types

from a2ui.schema.manager import A2uiSchemaManager
from a2ui.basic_catalog.provider import BasicCatalog
from app.a2ui_utils import a2ui_callback
from app.tools import (
    add_recipe,
    check_missing_ingredients,
    fetch_online_recipe,
    find_nearby_places,
    generate_dish_image,
    generate_dish_video,
    geocode_address,
    get_pantry_items,
    search_recipes,
    update_pantry_item,
)

FIRESTORE_PROJECT = "qwiklabs-gcp-02-851ad8720399"

# Load Agent Engine resource name and ID from deployment_metadata.json
metadata_path = Path(__file__).parent.parent / "deployment_metadata.json"
agent_engine_resource_name = None
agent_engine_id = None

if metadata_path.exists():
    try:
        with open(metadata_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)
            agent_engine_resource_name = metadata.get("remote_agent_runtime_id")
            if agent_engine_resource_name:
                agent_engine_id = agent_engine_resource_name.split("/")[-1]
    except Exception:
        pass

code_executor = AgentEngineSandboxCodeExecutor(
    agent_engine_resource_name=agent_engine_resource_name
)

# Configure Memory Service for deployment
if agent_engine_id:
    memory_service = VertexAiMemoryBankService(
        project=FIRESTORE_PROJECT,
        location="us-east1",
        agent_engine_id=agent_engine_id,
    )
else:
    memory_service = None


def save_user_memory(fact: str) -> str:
    """Saves an important user preference, dietary restriction, or favorite dish into long-term memory across sessions.

    Args:
        fact: The statement or preference to remember (e.g. 'User is allergic to peanuts', 'User prefers vegetarian recipes').

    Returns:
        A confirmation message.
    """
    if memory_service:
        import asyncio
        from google.adk.memory.base_memory_service import MemoryEntry

        content = types.Content(parts=[types.Part.from_text(text=fact)])
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(
                memory_service.add_memory(
                    app_name="app",
                    user_id="user",
                    memories=[MemoryEntry(content=content)],
                )
            )
        except RuntimeError:
            asyncio.run(
                memory_service.add_memory(
                    app_name="app",
                    user_id="user",
                    memories=[MemoryEntry(content=content)],
                )
            )
        return f"Successfully saved to long-term memory: '{fact}'"
    return "Memory service is not configured."


def get_weather(query: str) -> str:
    """Simulates a web search. Use it get information on weather.

    Args:
        query: A string containing the location to get weather information for.

    Returns:
        A string with the simulated weather information for the queried location.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        return "It's 60 degrees and foggy."
    return "It's 90 degrees and sunny."


def get_current_time(query: str) -> str:
    """Simulates getting the current time for a city.

    Args:
        city: The name of the city to get the current time for.

    Returns:
        A string with the current time information.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        tz_identifier = "America/Los_Angeles"
    else:
        return f"Sorry, I don't have timezone information for query: {query}."

    tz = ZoneInfo(tz_identifier)
    now = datetime.datetime.now(tz)
    return f"The current time for query {query} is {now.strftime('%Y-%m-%d %H:%M:%S %Z%z')}"


schema_manager = A2uiSchemaManager(
    version="0.8",
    catalogs=[BasicCatalog.get_config("0.8")],
)

instruction = schema_manager.generate_system_prompt(
    role_description=(
        "You are Chef Gemini, a friendly and expert culinary AI assistant. "
        "Your goal is to help users discover recipes, manage their pantry inventory, "
        "plan delicious meals, find nearby grocery stores, generate photos of dishes, "
        "execute Python code safely in a sandbox environment, and remember user preferences across sessions."
    ),
    workflow_description="Analyze the request and return structured UI when appropriate.",
    ui_description=(
        "Keep every surface tiny and flat: ONE Card > ONE Column > a few Text rows. "
        "Never nest a Card inside a Card. "
        "Use ONLY these components: Card, Column, Row, Text, and Image. Do not use "
        "Table or Heading (unsupported), or Buttons, actions, or forms (they do "
        "nothing in adk web). "
        "You may include one Image component, but only when you have a public https "
        "URL for the image (for example the URL an image tool returns after uploading "
        "to a public bucket). Set the Image url to that exact https link, for example "
        '{"Image": {"url": {"literalString": "https://..."}}}. Never point an '
        "Image at a bare filename, an artifact name, or a non-http(s) path. If you do "
        "not have a public URL, add a short Text line noting the image instead. "
        "No markdown in text; use the usageHint property ('h1', 'h2', 'body') for "
        "headings and emphasis. "
        "Output ONLY the raw A2UI JSON array — no prose, and never wrap it in "
        "<a2a_datapart_json> tags or 'kind'/'data'/'metadata' objects. "
        "Whenever a user tells you an important preference, dietary restriction, allergy, or favorite food, call save_user_memory to save it to long-term memory. "
        "Whenever a user asks what you remember about them, or asks about their allergies/preferences/history across sessions, ALWAYS call load_memory to search long-term memory."
    ),
    include_schema=True,
    include_examples=True,
)

root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model="gemini-flash-latest",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=instruction,
    tools=[
        get_weather,
        get_current_time,
        search_recipes,
        add_recipe,
        get_pantry_items,
        update_pantry_item,
        check_missing_ingredients,
        fetch_online_recipe,
        geocode_address,
        find_nearby_places,
        generate_dish_image,
        generate_dish_video,
        load_memory,
        preload_memory,
        save_user_memory,
    ],
    code_executor=code_executor,
    after_model_callback=a2ui_callback,
)

app = App(
    root_agent=root_agent,
    name="app",
)


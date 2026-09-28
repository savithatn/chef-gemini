# 🍳 Chef Gemini — AI Culinary Assistant & Meal Planner

![Chef Gemini Demo](./demo.gif)

**Chef Gemini** is an intelligent conversational culinary assistant built with the **Google Agent Development Kit (ADK)**. It empowers home cooks to discover personalized recipes based on pantry inventory, plan balanced meals, generate appetizing food photography and short dish videos, execute Python code for unit & nutritional conversions, locate nearby grocery stores, and maintain dietary preferences across sessions using long-term memory.

---

## 🌟 Key Features & Capabilities

- **🧠 Persistent Memory Bank**: Automatically remembers user dietary restrictions (allergies, vegetarian/vegan preferences), favorite cuisines, and household preferences across chat sessions using Vertex AI Memory Bank (`VertexAiMemoryBankService`).
- **🥫 Firestore Pantry & Recipe Database**: Connects directly to Google Cloud Firestore (`pantry_items` and `recipes` collections) to manage pantry inventory, check missing ingredients, and retrieve custom recipes.
- **🖼️ Multimodal Food Photography Generation**: Uses Google's Imagen/Gemini image generation models (`gemini-3.1-flash-lite-image`) to generate high-resolution plated food photography, saving artifacts and uploading directly to Google Cloud Storage.
- **📹 AI Video Generation**: Uses Google's Omni model (`gemini-omni-flash-preview` in location `global`) to generate short food preparation and cooking videos on demand.
- **🎨 Interactive A2UI Surfaces**: Formats recipe cards, pantry lists, and dish visuals using **A2UI (v0.8)** schema components (`A2uiSchemaManager`) rendered seamlessly in the web interface.
- **📍 Nearby Grocery Location Services**: Uses Google Maps Places and Geocoding APIs to locate nearby supermarkets and specialty ingredient markets based on user address or location.
- **🐍 Python Code Execution Sandbox**: Safely executes Python code inside an isolated Agent Engine sandbox (`AgentEngineSandboxCodeExecutor`) to perform precise unit conversions and nutritional calculations.

---

## 🛠️ Google Cloud Services & Tech Stack

| Service / Tool | Implementation Details |
| :--- | :--- |
| **Agent Framework** | Google Agent Development Kit (ADK) using `Gemini` (`gemini-flash-latest`) |
| **Memory Service** | **Vertex AI Memory Bank** (`VertexAiMemoryBankService`) |
| **Database** | **Google Cloud Firestore** (`pantry_items` & `recipes` collections) |
| **Media Storage** | **Google Cloud Storage** (public media bucket for generated images & videos) |
| **Image Generation** | `gemini-3.1-flash-lite-image` via Vertex AI `genai.Client` |
| **Video Generation** | `gemini-omni-flash-preview` via Vertex AI `Client.interactions` (`global` region) |
| **Location Services** | Google Maps Places API & Geocoding API |
| **Code Execution** | `AgentEngineSandboxCodeExecutor` running on Agent Engine |
| **User Interface** | FastAPI backend proxy with custom modern web UI and A2UI client renderer |

---

## 📂 Project Structure

```
.
├── app/
│   ├── __init__.py
│   ├── agent.py            # Main ADK Agent, Memory Bank, and A2UI callback setup
│   ├── tools.py            # Firestore, GCS, Image/Video generation, & Maps tool definitions
│   └── a2ui_utils.py       # A2UI after_model_callback response transformation logic
├── frontend/
│   ├── main.py             # FastAPI proxy server interfacing with Agent Engine
│   ├── static/
│   │   └── index.html      # Modern culinary chat UI & A2UI client renderer
│   └── requirements.txt
├── agents-cli-manifest.yaml # Agent Deployment Manifest
├── demo.gif                # Looping animation of live agent interactions
└── pyproject.toml
```

---

## 🚀 How to Run Locally

### Prerequisites
- Python 3.10+
- Google Cloud Project with Vertex AI, Firestore, Cloud Storage, and Google Maps APIs enabled.
- Authenticated GCP Credentials (`gcloud auth application-default login`).

### 1. Install Dependencies
```bash
uv pip install -e .
```

### 2. Verify Agent Loading
```bash
uv run python3 -c "import app.agent; print('Agent loaded successfully!')"
```

### 3. Run Frontend Server Locally
Navigate to the `frontend/` directory, set required environment variables, and start FastAPI:
```bash
cd frontend
pip install -r requirements.txt
export AGENT_ENGINE_RESOURCE_NAME="projects/<PROJECT_ID>/locations/<LOCATION>/reasoningEngines/<ENGINE_ID>"
export AGENT_DIRECTORY="app"
uvicorn main:app --host 0.0.0.0 --port 8080
```
Access the application by navigating to localhost on port 8080 in your web browser.

---

## ☁️ Deployment

### 1. Deploy Agent to Agent Engine
```bash
agents-cli deploy --update-env-vars GOOGLE_MAPS_API_KEY=<YOUR_API_KEY>
```

### 2. Deploy Frontend to Cloud Run
```bash
gcloud run deploy chef-gemini-frontend \
  --source ./frontend \
  --region us-east1 \
  --set-env-vars AGENT_ENGINE_RESOURCE_NAME="<AGENT_ENGINE_RESOURCE_NAME>",AGENT_DIRECTORY="app" \
  --allow-unauthenticated
```

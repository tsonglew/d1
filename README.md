## Desktop Pet Agent

This PyQt6 desktop companion keeps a LangChain-driven pet named **Pixel** on your screen. Pixel chats with you, reacts to simple cues, and (optionally) taps into OpenAI models for richer banter. The codebase now targets Python 3.14+ and leans on its modern typing + dataclass ergonomics.

### Getting started

1. **Install dependencies**

   ```bash
   uv pip install -r <(uv pip compile pyproject.toml)
   ```

   or with regular pip:

   ```bash
   pip install -e .
   ```

2. **Configure your Grok credentials**

   Create a `.env` file (or export env vars) with the deployment you want the agent to call:

   ```ini
   GROK_BASE_URL=https://example.com
   GROK_AUTH_TOKEN=sk-your-token
   ```

   The PyQt agent and the CLI tester both load these values automatically via `python-dotenv`.

3. **Run the pet**

   ```bash
   python main.py
   ```

### Testing the Grok API

Populate `.env` with your deployment details:

```ini
GROK_BASE_URL=https://example.com
GROK_AUTH_TOKEN=sk-your-token
```

Then exercise the endpoint:

```bash
python scripts/test_grok_api.py "Tell me a cat fact" --model grok-beta
```

Add `--raw` to inspect the full JSON response, or adjust the `--endpoint`, `--temperature`, and timeout flags as needed.

### Modular layout

- `d1.prompts.SYSTEM_PROMPT` centralizes the pet tone so both local and remote LLMs stay in sync.
- `d1.models.ChatModelSettings` + `d1.models.create_chat_model()` decide between `langchain-openai` and the offline `LocalPetChatModel`.
- `d1.agents.PetAgent` is a dataclass that wires prompts, history, and the runnable chain. `PetAgent.reset()` now returns `Self` for fluent usage.
- `d1.ui.DesktopPetWindow` and `d1.ui.AgentWorker` isolate all PyQt concerns, while `d1.app.run_app()` simply boots the UI.

Feel free to remix the prompt, drop in another LangChain-compatible model, or customize the PyQt widgets to make Pixel your own.

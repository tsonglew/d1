## Desktop Pet Agent

This PySide6 desktop companion keeps a LangChain-driven duck named **Pixel** floating on your desktop. The translucent duck glides left and right with a looping GIF, and a click on the pet pops open the chat window where you can trade messages powered by LangChain. The codebase targets Python 3.14+ and leans on its modern typing + dataclass ergonomics.

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

   The PySide agent and the CLI tester both load these values automatically via `python-dotenv`.

3. **Run the pet**

   ```bash
   python main.py
   ```

   A frameless duck overlay will appear immediately. Click the duck any time you want to summon or re-focus the chat window.

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
- `d1.ui.DuckOverlayWindow` renders the animated desktop pet, while `d1.ui.DesktopPetWindow` and `d1.ui.AgentWorker` own the chat experience. `d1.app.run_app()` wires the overlay click signal to the chat window.

Feel free to remix the prompt, drop in another LangChain-compatible model, or customize the PySide widgets to make Pixel your own.

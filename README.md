 TalentScout – Hiring Assistant Chatbot

Streamlit chatbot for initial candidate screening. Powered by Ollama running locally (no API costs).

Features
- Greeting and clear purpose.
- Conversational info collection: name, email, phone, years of experience, desired positions, location, tech stack.
- Generates 3 questions per declared technology using Ollama model (e.g. `llama3.2`).
- Context maintained across turns.
- Fallbacks for unexpected input and graceful exit on keywords.
- Local JSONL storage with masking for email and phone.

 Quickstart
 1) Python env
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

 2) Install Ollama
Download and install: https://ollama.com/download  
Then pull a model (example llama3.2):  
```bash
ollama pull llama3.2
```

 3) Configure
create a `.env`:
```
USE_OLLAMA=true
OLLAMA_MODEL=llama3.2
```

 4) Run
```bash
streamlit run app.py
```
App opens at http://localhost:8501

 End keywords
`bye`, `goodbye`, `exit`, `quit`, `stop`, `thanks`, `thank you`

 Files
```
app.py
core/llm.py
core/prompts.py
core/logic.py
core/storage.py
core/privacy.py
requirements.txt
.env
```

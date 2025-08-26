import os, json, re
from typing import List, Dict
import ollama
from .prompts import SYSTEM_PROMPT, QUESTION_JSON_PROMPT

class LLMClient:
    def __init__(self, model=None):
        self.model = model or os.getenv("OLLAMA_MODEL", "llama3.2")

    def chat(self, messages: List[Dict[str,str]]) -> str:
        # flatten chat into a single prompt
        prompt = ""
        for m in messages:
            prompt += f"{m['role'].upper()}: {m['content']}\n"
        prompt += "ASSISTANT:"
        r = ollama.generate(model=self.model, prompt=prompt, options={"temperature":0.2})
        return r["response"].strip()

    def greeting(self) -> str:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": "Greet the candidate and explain your purpose in two short sentences."}
        ]
        return self.chat(messages)

    def question_json(self, tech_list: List[str], cap_total: int = 15) -> Dict[str,List[str]]:
        tech_csv = ", ".join([t.strip() for t in tech_list if t.strip()])
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": QUESTION_JSON_PROMPT.format(tech_csv=tech_csv, cap_total=cap_total)}
        ]
        raw = self.chat(messages)
        try:
            data = json.loads(raw)
        except:
            m = re.search(r"\{.*\}", raw, flags=re.S)
            data = json.loads(m.group(0)) if m else {}
        return {k: v[:3] for k,v in data.items()}

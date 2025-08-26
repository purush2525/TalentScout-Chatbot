from typing import List, Tuple, Dict, Optional
import re
from .llm import LLMClient
from .prompts import SYSTEM_PROMPT

END_WORDS = {"bye","goodbye","exit","quit","stop","thanks","thank you"}

FIELDS = [
    ("full_name", "What is your full name?"),
    ("email", "Please share your email address."),
    ("phone", "Please share your phone number."),
    ("experience_years", "How many years of professional experience do you have?"),
    ("desired_positions", "Which position(s) are you interested in?"),
    ("location", "What is your current location (city, country)?"),
]

def is_email(x: str) -> bool:
    return re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", x or "") is not None

def is_phone(x: str) -> bool:
    return re.match(r"^[\d\-\+\(\)\s]{7,}$", x or "") is not None

class HiringAssistant:
    def __init__(self, store):
        self.llm = LLMClient()
        self.history: List[Tuple[str,str]] = []
        self.done = False
        self.store = store
        self.state = {
            "info": {k: None for k,_ in FIELDS},
            "techs": [],
            "questions": {},  # tech -> [q1,q2,q3]
            "answers": {},    # (tech, idx) -> answer
            "phase": "info",  # info | stack | qna | end
            "cursor": {"tech": None, "q_index": 0},
        }

    def append(self, role: str, content: str):
        self.history.append((role, content))

    def greet(self) -> str:
        return self.llm.greeting()

    def step(self, user_text: str) -> str:
        if self.done:
            return "Session already ended. Please start a new conversation."

        if any(w in user_text.lower() for w in END_WORDS):
            self.done = True
            self.state["phase"] = "end"
            return "Thanks for your time. We will review and email you next steps."

        phase = self.state["phase"]
        if phase == "info":
            return self._handle_info(user_text)
        if phase == "stack":
            return self._handle_stack(user_text)
        if phase == "qna":
            return self._handle_qna(user_text)

        return "I did not understand. Please continue or type 'exit' to finish."

    def _handle_info(self, user_text: str) -> str:
        # Find first missing field
        info = self.state["info"]
        key_to_ask = next((k for k,v in info.items() if not v), None)

        # If just starting, ask first
        if key_to_ask is None:
            # Done all info
            self.state["phase"] = "stack"
            return "List your tech stack: languages, frameworks, databases, and tools."

        # Validate input for previous question if exists
        # Determine which question was asked last from history
        # For simplicity assume user's latest message answers the current question
        value = user_text.strip()

        # Validate based on field
        if key_to_ask == "email" and not is_email(value):
            return "That does not look like a valid email. Please provide a valid email address."
        if key_to_ask == "phone" and not is_phone(value):
            return "That does not look like a valid phone number. Please provide a valid phone number."

        info[key_to_ask] = value

        # Ask next or move on
        next_key = next((k for k,v in info.items() if not v), None)
        if next_key is None:
            self.state["phase"] = "stack"
            return "Thanks. Now, list your tech stack: languages, frameworks, databases, and tools."
        else:
            # Ask next question
            prompt = dict(FIELDS)[next_key]
            return prompt

    def _handle_stack(self, user_text: str) -> str:
        # Extract techs as comma-separated
        parts = [p.strip() for p in re.split(r"[,\n;/]", user_text) if p.strip()]
        self.state["techs"] = parts[:10]  # guardrail
        if not self.state["techs"]:
            return "Please list at least one technology."
        # Generate questions via LLM
        self.state["questions"] = self.llm.question_json(self.state["techs"], cap_total=15)
        # Seed cursor
        tech = next(iter(self.state["questions"].keys()), None)
        self.state["cursor"] = {"tech": tech, "q_index": 0}
        self.state["phase"] = "qna"
        return self._present_next_question()

    def _present_next_question(self) -> str:
        cur = self.state["cursor"]
        tech = cur["tech"]
        idx = cur["q_index"]
        if tech is None:
            # No questions generated
            self.state["phase"] = "end"
            self.done = True
            return "Thanks. We will review your information and follow up by email."
        qs = self.state["questions"].get(tech, [])
        if idx >= len(qs):
            # Move to next tech
            techs = list(self.state["questions"].keys())
            try:
                next_tech = techs[techs.index(tech)+1]
                cur["tech"] = next_tech
                cur["q_index"] = 0
                return self._present_next_question()
            except Exception:
                # Done all
                self.state["phase"] = "end"
                self.done = True
                return "This concludes the screening. Thank you. We will reach out with next steps."
        question = qs[idx]
        return f"**{tech} – Q{idx+1}:** {question}"

    def _handle_qna(self, user_text: str) -> str:
        # Record answer
        cur = self.state["cursor"]
        tech = cur["tech"]
        idx = cur["q_index"]
        self.state["answers"][(tech, idx)] = user_text.strip()
        # Advance
        self.state["cursor"]["q_index"] += 1
        return self._present_next_question()

    def current_record(self) -> Dict:
        rec = {}
        rec.update(self.state["info"])
        rec["techs"] = self.state["techs"]
        rec["answers"] = {f"{k[0]}_q{k[1]+1}": v for k,v in self.state["answers"].items()}
        return rec

"""LangChain agent that extracts MITRE ATT&CK techniques from CTI reports.

The agent reads a CTI report, identifies adversary behaviors, queries the
ATT&CK vector store via the `search_attack_techniques` tool, and returns a
structured JSON list of techniques with supporting evidence quotes.
"""

from __future__ import annotations

import json
import os
import re

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent

from src.tools import search_attack_techniques

load_dotenv()

MODEL_NAME = "gemini-2.5-flash"
MAX_REPORT_CHARS = 32000  # ~8k tokens; truncate longer reports for cost control

RETRY_WAIT_SECONDS = 20
MAX_RETRIES = 6

SYSTEM_PROMPT = """\
You are a senior threat intelligence analyst. Your job is to read a CTI report
and extract the MITRE ATT&CK techniques the adversary actually used.

PROCESS
1. Read the entire report.
2. Identify discrete adversary behaviors (initial access vectors, execution
   methods, persistence mechanisms, lateral movement, C2 patterns, exfiltration,
   etc.).
3. For each behavior, call `search_attack_techniques` with a NATURAL-LANGUAGE
   description of what the adversary did. Describe the behavior in your own
   words — do not pass technique IDs or names.
4. Review the candidates returned by the tool. Pick the technique that most
   precisely matches the described behavior, if any. The retrieval is fuzzy:
   some candidates will not actually match. You must decide.
5. Record an evidence quote (verbatim text from the report) that supports
   each chosen technique.

RULES
- Only include techniques where the report clearly DESCRIBES the behavior.
  Do not include techniques that are merely mentioned in passing, listed in
  a summary table, or implied without supporting narrative.
- Prefer sub-techniques (e.g., T1059.001) over parent techniques (e.g., T1059)
  when the report gives enough detail to disambiguate.
- Each technique should appear at most once.
- Be conservative. False positives are worse than misses.

OUTPUT FORMAT
Return ONLY a single JSON object, no markdown fences, no commentary. Schema:

{
  "techniques": [
    {
      "id": "T1059.001",
      "name": "Command and Scripting Interpreter: PowerShell",
      "evidence": "<verbatim quote from the report>"
    }
  ]
}

If no techniques are clearly described, return {"techniques": []}.
"""


def _build_agent():
    if not os.environ.get("GOOGLE_API_KEY"):
        raise RuntimeError(
            "GOOGLE_API_KEY environment variable not set"
        )
    llm = ChatGoogleGenerativeAI(model=MODEL_NAME, temperature=0.0)
    return create_react_agent(
        model=llm,
        tools=[search_attack_techniques],
        prompt=SystemMessage(content=SYSTEM_PROMPT),
    )

def _extract_json(text: str) -> dict:
    "Pull the JSON object out of the model's final message"
    text = re.sub(r"```json\s*", "", text)  
    text = text.replace("```", "").strip()
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("No JSON object found in the text")
    return json.loads(text[start : end + 1])

def _is_rate_limit_error(exc: Exception) -> bool:
    return "429" in str(exc) or "RESOURCE_EXHAUSTED" in str(exc)

def extract_techniques(report_text: str) -> dict:
    "Run the agent over a CTI report, retrying on 429 rate-limit errors."

    if len(report_text) > MAX_REPORT_CHARS:
        report_text = report_text[:MAX_REPORT_CHARS] + "\n\n[REPORT TRUNCATED]"
        agent = _build_agent()
        user_msg = HumanMessage(content=f"Extract MITRE ATT&CK techniques from the following CTI report:\n\n{report_text}")

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                result = agent.invoke({"messages": [user_msg]})
                final_text = result["messages"][-1].content
                return _extract_json(final_text)
            
            except Exception as exc:
                if _is_rate_limit_error(exc) and attempt < MAX_RETRIES:
                    wait = RETRY_WAIT_SECONDS * attempt  # 20s, 40s, 60s, ...
                    print(
                        f"  [rate limit] hit 429 on attempt {attempt}/{MAX_RETRIES}. "
                        f"Waiting {wait}s before retry...",
                        flush=True,
                    )
                    time.sleep(wait)
                else:
                    raise
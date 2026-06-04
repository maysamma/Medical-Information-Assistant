import streamlit as st
import os
import re
import time
from collections import deque
import requests
from bs4 import BeautifulSoup

# ─── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Medical Information Assistant",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  /* ── Fonts & base ── */
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
  html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

  /* ── Main background ── */
  .stApp { background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); }

  /* ── Hide Streamlit branding ── */
  #MainMenu, footer, header { visibility: hidden; }

  /* ── Hero header ── */
  .hero {
    background: linear-gradient(135deg, #1e3a5f 0%, #0d2137 100%);
    border: 1px solid rgba(56,189,248,0.25);
    border-radius: 16px;
    padding: 2rem 2.5rem;
    margin-bottom: 1.5rem;
    position: relative;
    overflow: hidden;
  }
  .hero::before {
    content: "";
    position: absolute; top: -60px; right: -60px;
    width: 220px; height: 220px;
    background: radial-gradient(circle, rgba(56,189,248,0.12) 0%, transparent 70%);
    border-radius: 50%;
  }
  .hero-title { color: #f0f9ff; font-size: 2rem; font-weight: 700; margin: 0; }
  .hero-sub   { color: #94a3b8; font-size: 0.95rem; margin-top: 0.4rem; }
  .hero-badge {
    display: inline-block;
    background: rgba(56,189,248,0.15);
    color: #38bdf8;
    border: 1px solid rgba(56,189,248,0.35);
    border-radius: 20px;
    padding: 2px 12px;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    margin-bottom: 0.75rem;
  }

  /* ── Cards ── */
  .card {
    background: rgba(30,41,59,0.8);
    border: 1px solid rgba(71,85,105,0.5);
    border-radius: 12px;
    padding: 1.25rem 1.5rem;
    margin-bottom: 1rem;
  }
  .card-blue  { border-left: 3px solid #38bdf8; }
  .card-green { border-left: 3px solid #34d399; }
  .card-amber { border-left: 3px solid #fbbf24; }
  .card-red   { border-left: 3px solid #f87171; }

  /* ── Stat pill ── */
  .stat-pill {
    display: inline-flex; align-items: center; gap: 6px;
    background: rgba(56,189,248,0.1);
    border: 1px solid rgba(56,189,248,0.25);
    border-radius: 20px;
    padding: 4px 14px;
    font-size: 0.8rem;
    color: #7dd3fc;
    margin: 2px;
  }

  /* ── Sidebar ── */
  [data-testid="stSidebar"] {
    background: #0f172a !important;
    border-right: 1px solid rgba(71,85,105,0.4);
  }
  [data-testid="stSidebar"] * { color: #cbd5e1 !important; }
  [data-testid="stSidebar"] h1,
  [data-testid="stSidebar"] h2,
  [data-testid="stSidebar"] h3 { color: #f0f9ff !important; }

  /* ── Input styling ── */
  .stTextArea textarea {
    background: #1e293b !important;
    border: 1px solid rgba(71,85,105,0.6) !important;
    border-radius: 10px !important;
    color: #e2e8f0 !important;
    font-size: 0.95rem !important;
  }
  .stTextArea textarea:focus {
    border-color: #38bdf8 !important;
    box-shadow: 0 0 0 2px rgba(56,189,248,0.15) !important;
  }

  /* ── Buttons ── */
  .stButton > button {
    width: 100%;
    background: linear-gradient(135deg, #0ea5e9, #0284c7) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 0.6rem 1.5rem !important;
    font-weight: 600 !important;
    font-size: 0.95rem !important;
    transition: all 0.2s !important;
  }
  .stButton > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 6px 20px rgba(14,165,233,0.35) !important;
  }

  /* ── Reasoning step ── */
  .step-block {
    background: rgba(15,23,42,0.7);
    border: 1px solid rgba(71,85,105,0.4);
    border-radius: 10px;
    padding: 0.85rem 1.1rem;
    margin-bottom: 0.6rem;
    position: relative;
  }
  .step-label {
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    margin-bottom: 0.25rem;
  }
  .step-thought { color: #a78bfa; }
  .step-action  { color: #38bdf8; }
  .step-obs     { color: #34d399; }
  .step-final   { color: #fbbf24; }
  .step-content { color: #cbd5e1; font-size: 0.9rem; line-height: 1.6; }

  /* ── History entry ── */
  .history-q {
    color: #7dd3fc; font-weight: 600; font-size: 0.88rem;
    margin-bottom: 0.2rem;
  }
  .history-a {
    color: #94a3b8; font-size: 0.83rem;
    display: -webkit-box; -webkit-line-clamp: 2;
    -webkit-box-orient: vertical; overflow: hidden;
  }

  /* ── Warning banner ── */
  .warn-banner {
    background: rgba(245,158,11,0.1);
    border: 1px solid rgba(245,158,11,0.3);
    border-radius: 10px;
    padding: 0.75rem 1rem;
    color: #fcd34d;
    font-size: 0.85rem;
  }

  /* ── Disclaimer box ── */
  .disclaimer {
    background: rgba(239,68,68,0.07);
    border: 1px solid rgba(239,68,68,0.25);
    border-radius: 10px;
    padding: 0.9rem 1.1rem;
    color: #fca5a5;
    font-size: 0.83rem;
    line-height: 1.6;
    margin-top: 1rem;
  }

  /* ── Tool tag ── */
  .tool-tag {
    display: inline-block;
    background: rgba(56,189,248,0.1);
    color: #38bdf8;
    border: 1px solid rgba(56,189,248,0.3);
    border-radius: 6px;
    padding: 1px 8px;
    font-size: 0.75rem;
    font-family: monospace;
    margin: 2px;
  }

  /* ── Divider ── */
  hr { border-color: rgba(71,85,105,0.35) !important; }

  /* ── Scrollbar ── */
  ::-webkit-scrollbar { width: 6px; }
  ::-webkit-scrollbar-track { background: #0f172a; }
  ::-webkit-scrollbar-thumb { background: #334155; border-radius: 3px; }
</style>
""", unsafe_allow_html=True)


# ─── Tools ─────────────────────────────────────────────────────────────────────
def _get_medical_info(condition: str) -> str:
    try:
        url = f"https://en.wikipedia.org/wiki/{condition.replace(' ', '_')}"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        response = requests.get(url, timeout=10, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        paragraphs = soup.find_all("p")
        summary = ""
        for p in paragraphs:
            text = p.get_text().strip()
            if text and len(text) > 50:
                summary += text + "\n\n"
            if len(summary) >= 800:
                break
        if not summary:
            return f"Could not find reliable information for '{condition}'."
        return f"Information about '{condition}':\n\n" + summary[:800] + "...\n\n(Source: Wikipedia)"
    except Exception as e:
        return f"Could not find reliable information for '{condition}'. Error: {str(e)}"


def _get_drug_info(drug_name: str) -> str:
    drug_db = {
        "paracetamol": "Used for pain relief and fever reduction. Common brand: Panadol/Tylenol. Max adult dose: 1g per dose, 4g/day.",
        "ibuprofen": "NSAID used for pain, fever, and inflammation. Common brand: Advil, Nurofen. Take with food.",
        "aspirin": "Used for pain, fever, inflammation, and blood thinning. Avoid in children under 16.",
        "amoxicillin": "Antibiotic used for bacterial infections. Requires a prescription.",
        "cetirizine": "Antihistamine used for allergies and hay fever. Common brand: Zyrtec.",
        "omeprazole": "Proton pump inhibitor used for acid reflux and stomach ulcers. Common brand: Prilosec.",
        "metformin": "Used to treat type 2 diabetes. Helps control blood sugar levels.",
        "atorvastatin": "Statin used to lower cholesterol. Common brand: Lipitor.",
    }
    info = drug_db.get(drug_name.lower(), f"Basic information about '{drug_name}' is not available in the demo database.")
    return f"Drug Information for '{drug_name}':\n{info}"


def _calculate_bmi(weight_kg: float, height_cm: float) -> str:
    try:
        bmi = float(weight_kg) / ((float(height_cm) / 100) ** 2)
    except Exception:
        return "Invalid BMI inputs. Please provide numeric values."
    if bmi < 18.5:
        category, advice = "Underweight", "Consider consulting a doctor or dietitian."
    elif bmi < 25.0:
        category, advice = "Normal weight", "You are in a healthy weight range."
    elif bmi < 30.0:
        category, advice = "Overweight", "Consider increased physical activity and a balanced diet."
    else:
        category, advice = "Obese", "Consult a healthcare provider for a personalised plan."
    return (
        f"BMI Calculation:\n"
        f"  Weight: {weight_kg} kg | Height: {height_cm} cm\n"
        f"  BMI: {bmi:.1f} ({category})\n"
        f"  Advice: {advice}"
    )


def _medical_disclaimer() -> str:
    return (
        "MEDICAL DISCLAIMER: This information is for educational purposes only and "
        "does not constitute professional medical advice, diagnosis, or treatment. "
        "Always seek the advice of your physician or other qualified health provider "
        "with any questions you may have regarding a medical condition."
    )


TOOL_REGISTRY = {
    "get_medical_info": _get_medical_info,
    "get_drug_info": _get_drug_info,
    "calculate_bmi": _calculate_bmi,
    "medical_disclaimer": _medical_disclaimer,
}

TOOL_DESCRIPTIONS = {
    "get_medical_info": "Fetches reliable medical information about a condition or symptom from Wikipedia.",
    "get_drug_info": "Returns basic information about common medications from an internal database.",
    "calculate_bmi": "Calculates Body Mass Index (BMI) and interprets the result.",
    "medical_disclaimer": "Returns the standard medical disclaimer. Always invoked in final responses.",
}

TOOL_PARAMS = {
    "get_medical_info": ["condition (str)"],
    "get_drug_info": ["drug_name (str)"],
    "calculate_bmi": ["weight_kg (float)", "height_cm (float)"],
    "medical_disclaimer": [],
}


# ─── Guardrails ────────────────────────────────────────────────────────────────
UNSAFE_PATTERNS = [
    (r"take\s+\d+\s*(mg|ml|tablets?|capsules?)", "[DOSAGE REDACTED — consult a pharmacist]"),
    (r"you (have|are suffering from|definitely have)", "[DIAGNOSIS REDACTED — see a doctor]"),
    (r"(you should|you must|you need to)\s+(stop|start|take|avoid)\s+\w+",
     "[ADVICE REDACTED — consult a healthcare professional]"),
]


def filter_output(text: str) -> tuple[str, bool]:
    redacted = False
    for pattern, replacement in UNSAFE_PATTERNS:
        new_text, n = re.subn(pattern, replacement, text, flags=re.IGNORECASE)
        if n:
            text = new_text
            redacted = True
    if redacted:
        text += (
            "\n\n⚠️ [GUARDRAIL] One or more sections were redacted because they "
            "resembled direct medical advice. Please consult a qualified healthcare "
            "professional for personalised guidance."
        )
    return text, redacted


# ─── OpenAI function schemas ───────────────────────────────────────────────────
OPENAI_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_medical_info",
            "description": "Fetch reliable medical information about a condition or symptom from Wikipedia.",
            "parameters": {
                "type": "object",
                "properties": {
                    "condition": {"type": "string", "description": "The medical condition or symptom to look up."}
                },
                "required": ["condition"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_drug_info",
            "description": "Get basic information about a common medication.",
            "parameters": {
                "type": "object",
                "properties": {
                    "drug_name": {"type": "string", "description": "Name of the drug or medication."}
                },
                "required": ["drug_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_bmi",
            "description": "Calculate Body Mass Index (BMI) from weight and height.",
            "parameters": {
                "type": "object",
                "properties": {
                    "weight_kg": {"type": "number", "description": "Weight in kilograms."},
                    "height_cm": {"type": "number", "description": "Height in centimetres."},
                },
                "required": ["weight_kg", "height_cm"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "medical_disclaimer",
            "description": "Return the standard medical disclaimer. ALWAYS call this before giving the final answer.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
]

SYSTEM_PROMPT = (
    "You are a responsible Medical Information Assistant. "
    "Use the available tools to answer the user's health-related question. "
    "Always call medical_disclaimer before giving your final answer. "
    "Never give direct medical advice, diagnose conditions, or prescribe treatments."
)


# ─── Proper ReAct loop using OpenAI function calling ──────────────────────────
def parse_query_and_dispatch(query: str, api_key: str, model: str, max_iterations: int) -> dict:
    """
    Multi-turn ReAct loop:
      1. Send messages to OpenAI with function definitions.
      2. If the model returns tool_calls, execute each tool and append observations.
      3. Repeat until the model returns a plain text answer or max_iterations hit.
    """
    import json
    from openai import OpenAI, AuthenticationError, APIConnectionError

    try:
        client = OpenAI(api_key=api_key)
    except Exception as e:
        return {"error": f"OpenAI client init failed: {e}", "steps": [], "final_answer": "", "action_count": 0, "was_redacted": False}

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": query},
    ]

    executed_steps = []
    action_count   = 0

    for _ in range(max_iterations + 1):
        try:
            resp = client.chat.completions.create(
                model=model,
                temperature=0,
                tools=OPENAI_TOOLS,
                tool_choice="auto",
                messages=messages,
                max_tokens=1500,
            )
        except AuthenticationError:
            return {"error": "Invalid OpenAI API key. Please check your key in the sidebar.", "steps": executed_steps, "final_answer": "", "action_count": action_count, "was_redacted": False}
        except APIConnectionError as e:
            return {"error": f"Connection error: {e}", "steps": executed_steps, "final_answer": "", "action_count": action_count, "was_redacted": False}
        except Exception as e:
            return {"error": str(e), "steps": executed_steps, "final_answer": "", "action_count": action_count, "was_redacted": False}

        msg = resp.choices[0].message

        # ── Model finished — plain text answer ──
        if not msg.tool_calls:
            final_raw   = msg.content or "No answer generated."
            final_clean, was_redacted = filter_output(final_raw)
            return {
                "steps":        executed_steps,
                "final_answer": final_clean,
                "was_redacted": was_redacted,
                "action_count": action_count,
            }

        # ── Guardrail: too many tool calls ──
        if action_count >= max_iterations:
            executed_steps.append({
                "type":      "observation",
                "content":   "[GUARDRAIL] Maximum tool calls reached. Stopping early.",
                "guardrail": True,
            })
            final_clean, was_redacted = filter_output(
                "I've reached the maximum number of tool calls. Based on what I've gathered so far, "
                "please consult a qualified healthcare professional for personalised advice."
            )
            return {
                "steps":        executed_steps,
                "final_answer": final_clean,
                "was_redacted": was_redacted,
                "action_count": action_count,
            }

        # ── Append assistant message with tool_calls ──
        messages.append(msg)

        # ── Execute each tool call ──
        for tc in msg.tool_calls:
            tool_name = tc.function.name
            try:
                args = json.loads(tc.function.arguments)
            except Exception:
                args = {}

            # Log thought from any reasoning content
            if msg.content:
                executed_steps.append({"type": "thought", "content": msg.content})

            executed_steps.append({"type": "action", "tool": tool_name, "args": args})

            fn = TOOL_REGISTRY.get(tool_name)
            if fn:
                try:
                    observation = fn(**args) if args else fn()
                except Exception as ex:
                    observation = f"Tool error: {ex}"
            else:
                observation = f"Unknown tool: {tool_name}"

            executed_steps.append({"type": "observation", "content": observation})
            action_count += 1

            # Feed observation back to model
            messages.append({
                "role":         "tool",
                "tool_call_id": tc.id,
                "content":      observation,
            })

    # Fallback if loop exhausted
    final_clean, was_redacted = filter_output("Unable to generate a complete answer. Please consult a healthcare professional.")
    return {
        "steps":        executed_steps,
        "final_answer": final_clean,
        "was_redacted": was_redacted,
        "action_count": action_count,
    }


# ─── Session State ──────────────────────────────────────────────────────────────
if "history" not in st.session_state:
    st.session_state.history = []
if "request_times" not in st.session_state:
    st.session_state.request_times = deque()
if "total_queries" not in st.session_state:
    st.session_state.total_queries = 0
if "total_redactions" not in st.session_state:
    st.session_state.total_redactions = 0
if "api_key" not in st.session_state:
    st.session_state.api_key = ""
if "model" not in st.session_state:
    st.session_state.model = "gpt-4o-mini"
if "max_tool_calls" not in st.session_state:
    st.session_state.max_tool_calls = 8
if "rpm_limit" not in st.session_state:
    st.session_state.rpm_limit = 5
if "last_result" not in st.session_state:
    st.session_state.last_result = None
if "last_query" not in st.session_state:
    st.session_state.last_query = ""


# ─── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Configuration")

    # Key: use session_state key= so value persists across rerenders
    st.text_input(
        "OpenAI API Key",
        type="password",
        placeholder="sk-…",
        help="Your OpenAI API key. Never stored beyond this session.",
        key="api_key",
    )
    st.selectbox("Model", ["gpt-4o-mini", "gpt-3.5-turbo", "gpt-4o"], key="model")
    st.slider("Max Tool Calls per Request", 3, 15, key="max_tool_calls")
    st.slider("Rate Limit (requests/min)", 1, 20, key="rpm_limit")

    # Convenience aliases read from session_state
    api_key       = st.session_state.api_key
    model         = st.session_state.model
    max_tool_calls = st.session_state.max_tool_calls
    rpm_limit     = st.session_state.rpm_limit

    st.divider()
    st.markdown("### 🛠️ Available Tools")
    for tname, tdesc in TOOL_DESCRIPTIONS.items():
        params = TOOL_PARAMS[tname]
        param_str = ", ".join(params) if params else "no args"
        st.markdown(f"""
<div class="card card-blue" style="padding:0.7rem 0.9rem; margin-bottom:0.5rem;">
  <div style="color:#38bdf8; font-weight:600; font-size:0.82rem; font-family:monospace;">{tname}({param_str})</div>
  <div style="color:#94a3b8; font-size:0.78rem; margin-top:3px;">{tdesc}</div>
</div>""", unsafe_allow_html=True)

    st.divider()
    st.markdown("### 📊 Session Stats")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Queries", st.session_state.total_queries)
    with col2:
        st.metric("Redactions", st.session_state.total_redactions)

    if st.session_state.history:
        st.divider()
        st.markdown("### 🕑 History")
        for i, h in enumerate(reversed(st.session_state.history[-6:])):
            st.markdown(f"""
<div class="card" style="padding:0.6rem 0.8rem; margin-bottom:0.4rem; cursor:pointer;">
  <div class="history-q">#{st.session_state.total_queries - i}  {h['query'][:50]}{"…" if len(h['query'])>50 else ""}</div>
</div>""", unsafe_allow_html=True)

    if st.button("🗑️ Clear History"):
        st.session_state.history = []
        st.session_state.total_queries = 0
        st.session_state.total_redactions = 0
        st.rerun()


# ─── Main Layout ───────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
  <div class="hero-badge">🏥 AI Agent System</div>
  <div class="hero-title">Medical Information Assistant</div>
  <div class="hero-sub">ReAct Agent · Tool Dispatcher · Guardrails · Rate Limiting</div>
</div>
""", unsafe_allow_html=True)

# Architecture overview (collapsible)
with st.expander("📐 System Architecture", expanded=False):
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
<div class="card card-blue">
  <div style="color:#38bdf8; font-weight:600; margin-bottom:0.5rem;">🔄 Data Flow</div>
  <ol style="color:#cbd5e1; font-size:0.88rem; line-height:2;">
    <li>User submits a health query</li>
    <li>ReAct agent reasons step-by-step</li>
    <li>Tool Dispatcher routes to correct tool</li>
    <li>Observations feed back to the agent</li>
    <li>Output Filter scans the final answer</li>
    <li>Rate Limiter enforces per-minute budget</li>
  </ol>
</div>""", unsafe_allow_html=True)
    with col2:
        st.markdown("""
<div class="card card-green">
  <div style="color:#34d399; font-weight:600; margin-bottom:0.5rem;">🛡️ Guardrails Active</div>
  <ul style="color:#cbd5e1; font-size:0.88rem; line-height:2;">
    <li><b>Output Filter</b> — redacts dosage instructions, diagnosis claims, and directive advice</li>
    <li><b>Rate Limiter</b> — sliding-window cap on requests/minute</li>
    <li><b>Iteration Cap</b> — hard limit on LLM tool calls per request</li>
    <li><b>Mandatory Disclaimer</b> — always appended to final answers</li>
  </ul>
</div>""", unsafe_allow_html=True)

st.divider()

# ── Query input ──
st.markdown("#### 💬 Ask the Medical Assistant")

EXAMPLE_QUERIES = [
    "I have frequent headaches and mild fever for 3 days. What could be the causes?",
    "What is ibuprofen used for and are there any risks?",
    "Calculate my BMI: I weigh 75 kg and my height is 178 cm.",
    "Tell me about type 2 diabetes symptoms and management.",
    "What is the difference between paracetamol and aspirin?",
]

selected_example = st.selectbox(
    "💡 Try an example query", ["— select an example —"] + EXAMPLE_QUERIES, index=0
)

query_input = st.text_area(
    "Your question",
    value=selected_example if selected_example != "— select an example —" else "",
    height=110,
    placeholder="e.g. I have a headache and sore throat — what could it be?",
    label_visibility="collapsed",
)

run_col, clear_col = st.columns([4, 1])
with run_col:
    run_btn = st.button("🚀 Run Agent", use_container_width=True)
with clear_col:
    if st.button("Clear", use_container_width=True):
        st.rerun()

# ── Rate limit check ──
def check_rate_limit(rpm: int) -> tuple[bool, float]:
    now = time.time()
    window: deque = st.session_state.request_times
    while window and now - window[0] > 60:
        window.popleft()
    if len(window) >= rpm:
        wait = 60 - (now - window[0])
        return False, wait
    window.append(now)
    return True, 0.0


# ── Execution ──
if run_btn:
    # Always read fresh from session_state at click time
    _api_key       = st.session_state.api_key.strip()
    _model         = st.session_state.model
    _max_tool_calls = st.session_state.max_tool_calls
    _rpm_limit     = st.session_state.rpm_limit

    if not query_input.strip():
        st.warning("Please enter a question before running the agent.")
    elif not _api_key:
        st.error("🔑 Please enter your OpenAI API key in the sidebar.")
    else:
        allowed, wait_sec = check_rate_limit(_rpm_limit)
        if not allowed:
            st.markdown(f"""
<div class="warn-banner">
  ⚠️ <b>Rate Limit Reached</b> — You've sent {_rpm_limit} requests in the last minute.
  Please wait <b>{wait_sec:.0f} seconds</b> before retrying.
</div>""", unsafe_allow_html=True)
        else:
            st.session_state.total_queries += 1

            with st.spinner("🤔 Agent is reasoning…"):
                result = parse_query_and_dispatch(
                    query=query_input.strip(),
                    api_key=_api_key,
                    model=_model,
                    max_iterations=_max_tool_calls,
                )

            if "error" in result and result["error"]:
                st.error(f"Agent Error: {result['error']}")
            else:
                if result.get("was_redacted"):
                    st.session_state.total_redactions += 1
                # ── Persist result so it survives the next rerender ──
                st.session_state.last_result = result
                st.session_state.last_query = query_input.strip()
                st.session_state.history.append({
                    "query": query_input.strip(),
                    "answer": result["final_answer"],
                    "steps": len(result["steps"]),
                    "tools": result["action_count"],
                    "redacted": result.get("was_redacted", False),
                })
                st.rerun()  # rerun now so the persistent block below renders cleanly

# ── Show persisted last result (survives rerenders) ──
if not run_btn and st.session_state.last_result:
    result  = st.session_state.last_result
    _model  = st.session_state.model

    sc1, sc2, sc3, sc4 = st.columns(4)
    sc1.markdown(f'<span class="stat-pill">🔢 {result["action_count"]} tool calls</span>', unsafe_allow_html=True)
    sc2.markdown(f'<span class="stat-pill">📋 {len(result["steps"])} steps</span>', unsafe_allow_html=True)
    sc3.markdown(f'<span class="stat-pill">{"🛡️ Redacted" if result.get("was_redacted") else "✅ Clean"}</span>', unsafe_allow_html=True)
    sc4.markdown(f'<span class="stat-pill">🤖 {_model}</span>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["🧠 Reasoning Trace", "📝 Final Answer"])

    with tab1:
        if result["steps"]:
            for step in result["steps"]:
                stype = step["type"]
                if stype == "thought":
                    st.markdown(f"""
<div class="step-block">
  <div class="step-label step-thought">💭 Thought</div>
  <div class="step-content">{step['content']}</div>
</div>""", unsafe_allow_html=True)
                elif stype == "action":
                    args_str = ", ".join(f"{k}=<b>{v}</b>" for k, v in step.get("args", {}).items())
                    st.markdown(f"""
<div class="step-block">
  <div class="step-label step-action">⚡ Action</div>
  <div style="color:#38bdf8; font-family:monospace; font-size:0.9rem;">
    <span class="tool-tag">{step['tool']}</span>&nbsp; {args_str}
  </div>
</div>""", unsafe_allow_html=True)
                elif stype == "observation":
                    border = "card-red" if step.get("guardrail") else "card-green"
                    icon = "🛑" if step.get("guardrail") else "🔍"
                    st.markdown(f"""
<div class="step-block {border}">
  <div class="step-label step-obs">{icon} Observation</div>
  <div class="step-content" style="white-space:pre-wrap;">{step['content'][:600]}{"…" if len(step['content'])>600 else ""}</div>
</div>""", unsafe_allow_html=True)
        else:
            st.info("No reasoning steps captured.")

    with tab2:
        st.markdown(f"""
<div class="card card-amber">
  <div style="color:#fbbf24; font-weight:600; margin-bottom:0.6rem;">🏁 Final Answer</div>
  <div style="color:#e2e8f0; font-size:0.95rem; line-height:1.75; white-space:pre-wrap;">{result['final_answer']}</div>
</div>""", unsafe_allow_html=True)

        if result.get("was_redacted"):
            st.markdown("""
<div class="warn-banner" style="margin-top:0.75rem;">
  🛡️ <b>Guardrail Activated</b> — Parts of this response were redacted because they
  resembled direct medical advice. Always consult a qualified healthcare professional.
</div>""", unsafe_allow_html=True)

        st.markdown("""
<div class="disclaimer">
  ⚕️ <b>MEDICAL DISCLAIMER:</b> This information is for educational purposes only and does not
  constitute professional medical advice, diagnosis, or treatment. Always seek the advice of
  your physician or other qualified health provider. Never disregard professional medical
  advice or delay seeking it based on information seen here. If you have a medical emergency,
  call your doctor or emergency services immediately.
</div>""", unsafe_allow_html=True)

# ── Empty state ──
if not run_btn and not st.session_state.history:
    st.markdown("""
<div class="card" style="text-align:center; padding:3rem 2rem; margin-top:1rem;">
  <div style="font-size:3rem; margin-bottom:1rem;">🏥</div>
  <div style="color:#e2e8f0; font-size:1.1rem; font-weight:600;">Ready to assist</div>
  <div style="color:#64748b; font-size:0.9rem; margin-top:0.5rem;">
    Enter a health question above, or pick an example query.<br>
    Make sure your OpenAI API key is set in the sidebar.
  </div>
</div>""", unsafe_allow_html=True)
import streamlit as st
import anthropic
import json
import random
from datetime import date
from fpdf import FPDF

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Finax Compliance Training",
    page_icon="🛡️",
    layout="centered",
)

# ── CSS — explicit dark text in all colored boxes (dark mode fix) ─────────────
st.markdown("""
<style>
    .scenario-box {
        background: #1e2761;
        color: #ffffff !important;
        padding: 1.5rem 1.8rem;
        border-radius: 12px;
        font-size: 1.05rem;
        line-height: 1.7;
        margin-bottom: 1.5rem;
    }
    .feedback-correct {
        background: #c8f7d4;
        color: #0d3a1f !important;
        border-left: 5px solid #1a7f3c;
        padding: 1rem 1.5rem;
        border-radius: 8px;
        margin-top: 1rem;
    }
    .feedback-partial {
        background: #fff0cc;
        color: #3d2800 !important;
        border-left: 5px solid #e6a800;
        padding: 1rem 1.5rem;
        border-radius: 8px;
        margin-top: 1rem;
    }
    .feedback-wrong {
        background: #fad4d8;
        color: #3d0009 !important;
        border-left: 5px solid #c0001a;
        padding: 1rem 1.5rem;
        border-radius: 8px;
        margin-top: 1rem;
    }
    .consequence-box {
        background: #ffe8cc;
        color: #3d1a00 !important;
        border-left: 5px solid #e65c00;
        padding: 1rem 1.5rem;
        border-radius: 8px;
        margin-top: 0.75rem;
    }
    .correct-box {
        background: #dce8ff;
        color: #001440 !important;
        border-left: 5px solid #0040cc;
        padding: 1rem 1.5rem;
        border-radius: 8px;
        margin-top: 0.75rem;
    }
    .takeaway-box {
        background: #e8f0e0;
        color: #1a2e00 !important;
        border-left: 5px solid #3a7d00;
        padding: 1rem 1.5rem;
        border-radius: 8px;
        margin-top: 0.75rem;
        font-style: italic;
    }
    .score-pill-2 { color: #1a7f3c; font-weight: bold; font-size: 1.1rem; }
    .score-pill-1 { color: #b07a00; font-weight: bold; font-size: 1.1rem; }
    .score-pill-0 { color: #c0001a; font-weight: bold; font-size: 1.1rem; }
    .result-pass {
        background: #c8f7d4; color: #0d3a1f !important;
        padding: 1.5rem; border-radius: 12px; text-align: center;
        font-size: 1.3rem; font-weight: bold; margin-bottom: 1rem;
    }
    .result-fail {
        background: #fad4d8; color: #3d0009 !important;
        padding: 1.5rem; border-radius: 12px; text-align: center;
        font-size: 1.3rem; font-weight: bold; margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# QUESTION BANK — from Finax compliance materials
# ══════════════════════════════════════════════════════════════════════════════
QUESTION_BANK = [
    {
        "id": 1,
        "topic": "Data Protection & GDPR",
        "scenario": (
            "You are working in the office and have printed documents containing client personal data "
            "(names, emails, investment details). You need to leave your desk for lunch.\n\n"
            "Can you leave these documents visible on your desk in a shared workspace?"
        ),
        "correct_approach": (
            "No. You must follow the Clean Desk Policy and secure all sensitive documents before leaving. "
            "Ensure that only authorised persons have access to the data (need-to-know principle). "
            "Store the documents in a drawer, locked cabinet, or shred them if no longer needed."
        ),
        "takeaway": "Never leave personal data exposed — always secure it before stepping away from your desk.",
        "consequence": (
            "Leaving client documents exposed may allow unauthorised persons to access sensitive data. "
            "This constitutes a GDPR breach, which can result in fines of up to €20M or 4% of annual turnover for Finax, "
            "and disciplinary action against the employee."
        ),
    },
    {
        "id": 2,
        "topic": "Data Protection & GDPR",
        "scenario": (
            "A colleague from another department asks you to send them a file containing client personal data "
            "— they say they 'might need it later'.\n\n"
            "Can you share the data since they are also a Finax employee?"
        ),
        "correct_approach": (
            "No. Personal data may only be shared when there is a clear, legitimate business purpose. "
            "You must verify that the colleague is authorised to access the data. "
            "Apply the data minimisation principle — share only what is strictly necessary. "
            "Use anonymised or pseudonymised data where possible."
        ),
        "takeaway": "Internal access is not automatic — data sharing must always be justified by a specific purpose.",
        "consequence": (
            "Sharing personal data without a justified reason violates GDPR and Finax's internal policy. "
            "This can result in a data breach, regulatory sanctions, and disciplinary proceedings."
        ),
    },
    {
        "id": 3,
        "topic": "Fraud Prevention",
        "scenario": (
            "You receive an email that appears to be from a senior manager requesting an urgent transfer of funds "
            "to a new bank account. The message emphasises the transfer must be done immediately "
            "and asks you not to call due to 'confidentiality of the transaction'.\n\n"
            "What do you do?"
        ),
        "correct_approach": (
            "Do not execute the transfer. Independently verify the request through a different communication channel "
            "— call the manager directly on their verified phone number. "
            "Follow internal procedures for suspicious financial requests. "
            "Report the incident to the compliance or security team."
        ),
        "takeaway": "Urgency + no phone contact = classic CEO fraud red flag. Always verify through a second channel before acting.",
        "consequence": (
            "Executing the transfer without verification is a Business Email Compromise (CEO fraud). "
            "The company could lose significant funds and the employee may face disciplinary and legal liability. "
            "Such frauds cost companies millions of euros annually."
        ),
    },
    {
        "id": 4,
        "topic": "Fraud Prevention",
        "scenario": (
            "A person contacts you via email claiming to be a Finax client. They urgently request that you send "
            "updated personal and account information due to a 'system issue', "
            "insisting that email is the only available contact method at this time.\n\n"
            "What do you do?"
        ),
        "correct_approach": (
            "Do not share any client data. "
            "Verify the client's identity using Finax's established authentication procedures. "
            "Do not rely on a single communication channel — call the client on their registered phone number. "
            "Report the suspicious request to your team."
        ),
        "takeaway": "Never disclose sensitive information without proper identity verification, especially when only one channel is available.",
        "consequence": (
            "Sending client data without verification leads to a personal data breach and GDPR violation. "
            "The client may suffer financial harm and Finax faces regulatory sanctions and reputational damage."
        ),
    },
    {
        "id": 5,
        "topic": "Conflict of Interest",
        "scenario": (
            "You are responsible for managing a client relationship. During onboarding, you realise "
            "the client is a close personal friend. The client asks you to 'take extra care' of their portfolio "
            "and prioritise their requests over other clients.\n\n"
            "What do you do?"
        ),
        "correct_approach": (
            "Identify and declare the conflict of interest to the Compliance Department as soon as possible. "
            "Remove yourself from the decision-making process for this client if necessary. "
            "Document the situation in the conflicts of interest register."
        ),
        "takeaway": "Conflicts of interest must be reported to Compliance — not managed informally. Always disclose early.",
        "consequence": (
            "Unmanaged preferential treatment of a personal friend as a client can lead to biased investment decisions, "
            "harm to other clients, MiFID II violations, and disciplinary action."
        ),
    },
    {
        "id": 6,
        "topic": "Conflict of Interest",
        "scenario": (
            "You are choosing between two similar investment products for a client. "
            "One product offers your team a higher internal incentive (bonus), "
            "while the other may be slightly more suitable for the client.\n\n"
            "How do you proceed?"
        ),
        "correct_approach": (
            "Always act in the best interest of the client — select the product that is more suitable for them. "
            "Disregard any personal or company financial incentive when making the recommendation. "
            "If in doubt, consult the Compliance Department."
        ),
        "takeaway": "Client interest always prevails over personal or team financial benefit. If incentives affect your judgment, escalate to Compliance.",
        "consequence": (
            "Recommending a product due to a higher bonus rather than client suitability violates MiFID II. "
            "This can result in regulatory sanctions, client lawsuits, and loss of the investment services licence."
        ),
    },
    {
        "id": 7,
        "topic": "Anti-Corruption & Gifts",
        "scenario": (
            "A client with whom you have a very good working relationship asks for your home address "
            "because they want to send you a small year-end gift as a personal thank you. "
            "They emphasise that 'the company doesn't need to be involved' and it's just a private gesture.\n\n"
            "What do you do?"
        ),
        "correct_approach": (
            "Decline the request and do not provide your private address. "
            "Inform your manager and/or the Compliance Department about the situation. "
            "Gifts directed to a private address are always a red flag — "
            "all gifts must be handled transparently and reported."
        ),
        "takeaway": "A gift sent to your private address is a red flag — decline and report it. All gifts must be transparent.",
        "consequence": (
            "Accepting a gift at your private address without reporting it creates a conflict of interest "
            "and may be treated as a bribe. This can lead to disciplinary proceedings, criminal liability, "
            "and reputational damage to Finax."
        ),
    },
    {
        "id": 8,
        "topic": "Anti-Corruption & Gifts",
        "scenario": (
            "A business contact who is also a local mayor informally tells you that the municipality "
            "is deciding on matters relevant to Finax's activities. "
            "During the conversation, the mayor casually asks whether you or Finax could 'support' "
            "an upcoming political campaign — adding that 'good relationships are always remembered'.\n\n"
            "What do you do?"
        ),
        "correct_approach": (
            "Immediately refuse any form of support. "
            "Escalate the situation to your manager and the Compliance Department. "
            "Contributions to public officials, political entities, or for political purposes are prohibited."
        ),
        "takeaway": "Anything of value linked to a public official or political purpose must be refused and escalated immediately.",
        "consequence": (
            "Any support of a political campaign in the context of a business decision can be classified as bribery. "
            "This is a criminal offence with penalties including fines and imprisonment."
        ),
    },
    {
        "id": 9,
        "topic": "Client Communication (MiFID II)",
        "scenario": (
            "A client asks whether a portfolio strategy will 'deliver similar returns as last year', "
            "which had exceptionally strong performance. You respond by highlighting last year's returns "
            "and say that 'this strategy has been performing very well and should continue to do so', "
            "without any further clarification.\n\n"
            "Is this type of communication appropriate?"
        ),
        "correct_approach": (
            "No. You must clearly explain that past performance is not indicative of future results. "
            "Provide balanced scenarios including the possibility of negative outcomes. "
            "Any discussion of future performance should be presented only as an estimate based on assumptions."
        ),
        "takeaway": "Always present performance information in a balanced, non-misleading way. Risks and uncertainties must be explicitly communicated.",
        "consequence": (
            "Misleading performance communication violates MiFID II. "
            "This can lead to regulatory sanctions, client lawsuits for losses, and lasting reputational damage."
        ),
    },
    {
        "id": 10,
        "topic": "Client Communication (MiFID II)",
        "scenario": (
            "During a call, a client is interested in a new investment product. "
            "To keep the conversation simple, you explain the potential returns and general benefits "
            "but do not mention the possibility of capital loss or market volatility.\n\n"
            "Is this acceptable?"
        ),
        "correct_approach": (
            "No. You must provide clear, complete, and transparent information including all material risks "
            "such as capital loss and market volatility — even if it makes the explanation more complex. "
            "The client has the right to make a fully informed decision."
        ),
        "takeaway": "Full transparency means disclosing both benefits and risks. Omitting risks is not simplification — it is a MiFID II violation.",
        "consequence": (
            "Omitting key risk information from client communication violates MiFID II. "
            "This can result in client complaints, regulatory fines, and disciplinary action against the employee."
        ),
    },
    {
        "id": 11,
        "topic": "Market Abuse (MAR)",
        "scenario": (
            "You notice a colleague in the marketing team is preparing a client presentation "
            "showing the product's performance over the past 3 years. "
            "However, you know the product has existed for 7 years and the first 4 years were weak. "
            "The colleague says 'clients only want to see what looks good anyway'.\n\n"
            "What do you do?"
        ),
        "correct_approach": (
            "Point out to your colleague that the presentation must include the entire available performance period — "
            "not just the selected positive years. Selectively showing only good periods is misleading. "
            "If the colleague disagrees, contact Compliance before the material is sent out."
        ),
        "takeaway": "Performance presentations must be complete, truthful, and unbiased. Selecting only good periods is market manipulation.",
        "consequence": (
            "Selective performance presentation can be classified as market manipulation under MAR. "
            "Penalties include regulatory fines in the millions of euros and criminal prosecution."
        ),
    },
    {
        "id": 12,
        "topic": "Market Abuse (MAR)",
        "scenario": (
            "You work in the client services department. A client emails you saying their friend saw "
            "'leaked information' online that an energy company will report exceptionally good results "
            "before they are officially published. The client asks if they should quickly buy the stock.\n\n"
            "What do you tell them?"
        ),
        "correct_approach": (
            "Explain to the client that 'leaked' or unverified information may be unreliable, manipulated, "
            "or deliberately spread to influence the market. "
            "Advise them to make decisions solely based on public, verified information available to all investors. "
            "Do not confirm or deny any non-public information, and do not recommend trading based on it."
        ),
        "takeaway": "Unverified or leaked information must never be used in investment recommendations. Always direct clients to public, verified data.",
        "consequence": (
            "Trading on non-public information is insider trading under MAR — a criminal offence "
            "carrying penalties of up to 7 years imprisonment and unlimited fines for both individuals and the firm."
        ),
    },
]

# ── ABCD modules (available for future use) ───────────────────────────────────
ABCD_MODULES = {
    "🔍 MAR – Market Abuse": "market abuse regulation, insider trading, inside information, price manipulation",
    "⚖️ Conflict of Interest": "conflict of interest, personal investments, family relationships, decision making",
    "🎁 Anti-Corruption & Gifts": "bribery, corruption, gifts from clients, political donations",
    "💬 Client Communication (MiFID II)": "MiFID II, misleading information, guaranteed returns, suitability",
    "🔒 Data Protection & GDPR": "GDPR, clean desk policy, need to know principle, data minimisation",
    "📢 Whistleblowing & Fraud": "whistleblowing, CEO fraud, deepfake, suspicious requests",
}

ROLES = ["General Employee", "Sales / Advisor", "Manager", "IT / Operations"]

# ── Access control ────────────────────────────────────────────────────────────
_APP_PASSWORD = "finaxontop"
_API_KEY = st.secrets.get("ANTHROPIC_API_KEY", "")

ABCD_SYSTEM_PROMPT = """You are a compliance training system for Finax, an investment company regulated by the NBS.
You generate realistic compliance scenarios in A/B/C/D quiz format.

Respond ONLY with a valid JSON object — no other text, no markdown:
{
  "scenario": "2-3 sentence situation description, second person (You are..., Your client...)",
  "choices": {
    "A": "option A text",
    "B": "option B text",
    "C": "option C text",
    "D": "option D text"
  },
  "correct": "A or B or C or D",
  "consequences": {
    "A": "What happens if A is chosen — 1-2 sentences",
    "B": "What happens if B is chosen — 1-2 sentences",
    "C": "What happens if C is chosen — 1-2 sentences",
    "D": "What happens if D is chosen — 1-2 sentences"
  },
  "explanation": "Why the correct answer is correct — 2 sentences, reference the specific rule."
}"""

EVAL_SYSTEM_PROMPT = """You are a compliance answer evaluator for Finax.
You receive a scenario, the correct approach, and an employee's free-text answer.
Your job is to assess how well the employee's answer matches the correct compliance approach.

IMPORTANT SCORING RULES:
- Be FAIR and CHARITABLE. If the employee's answer captures the core idea correctly — even briefly or imperfectly worded — give them credit.
- Score 2 if the employee identified the main correct action(s), even if they didn't list every detail.
- Score 1 if the employee got part of it right but missed something important or included something wrong.
- Score 0 only if the answer is clearly wrong, irrelevant, or shows a fundamental misunderstanding.

Scoring scale:
- 2 points: The answer captures all key elements of the correct approach (does not need to be word-perfect)
- 1 point: The answer contains some correct elements but is missing something important OR includes something incorrect
- 0 points: The answer is mostly or completely wrong, irrelevant, or shows a serious misunderstanding

Respond ONLY with a valid JSON object — no other text:
{
  "score": 0 or 1 or 2,
  "feedback": "2-3 sentences of personalised feedback on the employee's specific answer — acknowledge what was right and explain what was missing or incorrect",
  "what_right": "What the employee got right (1 sentence, or 'Nothing' if score=0)",
  "what_missing": "What was missing or wrong (1 sentence, or 'Nothing' if score=2)"
}"""


# ── Session state ─────────────────────────────────────────────────────────────
def generate_certificate(first_name: str, last_name: str, earned: int, max_pts: int, pct: int) -> bytes:
    pdf = FPDF()
    pdf.add_page()

    # ── Navy header bar ────────────────────────────────────────────────────────
    pdf.set_fill_color(30, 39, 97)
    pdf.rect(0, 0, 210, 38, "F")
    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(255, 255, 255)
    pdf.set_y(10)
    pdf.cell(0, 10, "FINAX", align="C", ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 8, "Compliance Training Certificate", align="C", ln=True)

    # ── Body ───────────────────────────────────────────────────────────────────
    pdf.set_text_color(30, 39, 97)
    pdf.ln(14)
    pdf.set_font("Helvetica", "", 13)
    pdf.cell(0, 9, "This is to certify that", align="C", ln=True)

    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 26)
    pdf.set_text_color(30, 39, 97)
    pdf.cell(0, 14, f"{first_name} {last_name}", align="C", ln=True)

    # Decorative line under name
    pdf.set_draw_color(30, 39, 97)
    pdf.set_line_width(0.8)
    name_w = 100
    pdf.line((210 - name_w) / 2, pdf.get_y() + 2, (210 + name_w) / 2, pdf.get_y() + 2)
    pdf.ln(10)

    pdf.set_font("Helvetica", "", 13)
    pdf.set_text_color(60, 60, 60)
    pdf.cell(0, 9, "has successfully completed the", align="C", ln=True)

    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 15)
    pdf.set_text_color(30, 39, 97)
    pdf.cell(0, 10, "General Compliance Onboarding Training", align="C", ln=True)

    # ── Score box ──────────────────────────────────────────────────────────────
    pdf.ln(12)
    box_x, box_w, box_h = 55, 100, 28
    pdf.set_fill_color(220, 232, 255)
    pdf.set_draw_color(0, 64, 204)
    pdf.set_line_width(0.5)
    pdf.rect(box_x, pdf.get_y(), box_w, box_h, "FD")
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(0, 64, 204)
    pdf.set_y(pdf.get_y() + 5)
    pdf.cell(0, 8, f"Score: {earned} / {max_pts} points  ({pct}%)", align="C", ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(60, 60, 60)
    pdf.cell(0, 8, f"Result: PASSED  ✓", align="C", ln=True)

    # ── Date ───────────────────────────────────────────────────────────────────
    pdf.ln(10)
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(0, 8, f"Date of completion: {date.today().strftime('%B %d, %Y')}", align="C", ln=True)

    # ── Footer bar ─────────────────────────────────────────────────────────────
    pdf.set_y(-25)
    pdf.set_fill_color(30, 39, 97)
    pdf.rect(0, pdf.get_y(), 210, 25, "F")
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(200, 210, 255)
    pdf.cell(0, 25, "Finax, o.c.p., a.s.  |  compliance@finax.eu  |  www.finax.eu", align="C")

    return bytes(pdf.output())


def init_state():
    defaults = {
        "game_state": "setup",
        "test_type": "onboarding",
        "api_key": "",
        "first_name": "",
        "last_name": "",
        "role": ROLES[0],
        "module": list(ABCD_MODULES.keys())[0],
        "num_questions": 5,
        "questions": [],
        "q_idx": 0,
        "score": 0,
        "current_scenario": None,
        "answered": False,
        "selected_choice": None,
        "evaluation": None,
        "user_answer": "",
        "history": [],
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()


# ── AI: evaluate free-text answer ─────────────────────────────────────────────
def evaluate_answer(question: dict, user_answer: str) -> dict:
    client = anthropic.Anthropic(api_key=st.session_state.api_key)
    user_msg = (
        f"SCENARIO:\n{question['scenario']}\n\n"
        f"CORRECT APPROACH:\n{question['correct_approach']}\n\n"
        f"EMPLOYEE'S ANSWER:\n{user_answer}"
    )
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=600,
        system=EVAL_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_msg}],
    )
    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw)


# ── AI: generate ABCD scenario ────────────────────────────────────────────────
def generate_abcd_scenario(module_name: str, topics: str, role: str, difficulty: str) -> dict:
    client = anthropic.Anthropic(api_key=st.session_state.api_key)
    user_msg = (
        f"Module: {module_name}\nTopics: {topics}\n"
        f"Employee role: {role}\nDifficulty: {difficulty}\n\nGenerate one scenario."
    )
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        system=ABCD_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_msg}],
    )
    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw)


def difficulty_label(idx: int, total: int) -> str:
    pct = idx / max(total - 1, 1)
    if pct < 0.4: return "easy"
    elif pct < 0.75: return "medium"
    return "hard"


def reset_game():
    keys = ["game_state", "test_type", "first_name", "last_name", "num_questions", "questions",
            "q_idx", "score", "current_scenario", "answered", "selected_choice", "evaluation",
            "user_answer", "history"]
    for k in keys:
        if k in st.session_state:
            del st.session_state[k]
    init_state()


# ══════════════════════════════════════════════════════════════════════════════
# SETUP
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.game_state == "setup":
    st.title("🛡️ Finax Compliance Training")
    st.markdown("#### Interactive AI-powered compliance scenarios")
    st.divider()

    with st.form("setup_form"):
        password = st.text_input(
            "🔑 Access Password", type="password", placeholder="Enter password...",
        )
        c1, c2 = st.columns(2)
        with c1:
            first_name = st.text_input("First Name", placeholder="John")
        with c2:
            last_name = st.text_input("Last Name", placeholder="Smith")
        role = st.selectbox("👤 Your role", ROLES)

        test_choice = st.radio(
            "📚 Test type",
            ["🎓 Onboarding Test — General (recommended)", "⚙️ Thematic ABCD Test (experimental)"],
            index=0,
        )

        num_q = None
        abcd_module = None

        if "Onboarding" in test_choice:
            num_q = st.select_slider(
                "Number of questions", options=[5, 10], value=5,
                help="5 questions ≈ 10 min | 10 questions ≈ 20 min"
            )
        else:
            abcd_module = st.selectbox("Module", list(ABCD_MODULES.keys()))

        submitted = st.form_submit_button("🚀 Start Test", use_container_width=True)

    if submitted:
        if password.strip() != _APP_PASSWORD:
            st.error("Incorrect password. Please try again.")
        elif not first_name.strip() or not last_name.strip():
            st.error("Please enter your first and last name.")
        else:
            st.session_state.api_key = _API_KEY
            st.session_state.first_name = first_name.strip()
            st.session_state.last_name = last_name.strip()
            st.session_state.role = role
            if "Onboarding" in test_choice:
                st.session_state.test_type = "onboarding"
                st.session_state.num_questions = num_q
                st.session_state.questions = random.sample(QUESTION_BANK, num_q)
            else:
                st.session_state.test_type = "abcd"
                st.session_state.module = abcd_module
                st.session_state.num_questions = 5
            st.session_state.game_state = "playing"
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# PLAYING — ONBOARDING TEST (free-text + AI evaluation, 0–2 pts per question)
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.game_state == "playing" and st.session_state.test_type == "onboarding":

    questions = st.session_state.questions
    q_idx = st.session_state.q_idx
    total = st.session_state.num_questions

    if q_idx >= total:
        st.session_state.game_state = "results"
        st.rerun()

    q = questions[q_idx]

    # Header
    c1, c2, c3 = st.columns([3, 2, 2])
    with c1: st.markdown(f"**{q['topic']}**")
    with c2: st.markdown(f"Question **{q_idx + 1}** / {total}")
    with c3: st.markdown(f"✅ Points: **{st.session_state.score}** / {q_idx * 2}")

    st.progress(q_idx / total)
    st.divider()

    # Scenario box
    st.markdown(
        f'<div class="scenario-box">📋 <strong>Situation:</strong><br><br>{q["scenario"].replace(chr(10), "<br>")}</div>',
        unsafe_allow_html=True,
    )

    # ── Before answer ──────────────────────────────────────────────────────────
    if not st.session_state.answered:
        st.markdown("**Describe how you would handle this situation:**")
        user_ans = st.text_area(
            label="Your answer",
            placeholder="Write in your own words what you would do in this situation...",
            height=130,
            label_visibility="collapsed",
        )
        if st.button("✅ Submit Answer", use_container_width=True, type="primary"):
            if not user_ans.strip():
                st.warning("Please write an answer before submitting.")
            else:
                with st.spinner("🤖 AI is evaluating your answer..."):
                    try:
                        ev = evaluate_answer(q, user_ans)
                        st.session_state.evaluation = ev
                        st.session_state.user_answer = user_ans
                        st.session_state.score += ev["score"]
                        st.session_state.answered = True
                        st.session_state.history.append({
                            "q_num": q_idx + 1,
                            "topic": q["topic"],
                            "scenario_short": q["scenario"][:90] + "...",
                            "user_answer": user_ans,
                            "score": ev["score"],
                            "feedback": ev["feedback"],
                            "what_right": ev.get("what_right", ""),
                            "what_missing": ev.get("what_missing", ""),
                            "consequence": q["consequence"],
                            "correct_approach": q["correct_approach"],
                            "takeaway": q["takeaway"],
                        })
                        st.rerun()
                    except Exception as e:
                        st.error(f"Evaluation error: {e}")

    # ── After answer — feedback ────────────────────────────────────────────────
    else:
        ev = st.session_state.evaluation
        score = ev["score"]
        user_ans = st.session_state.user_answer

        st.markdown("**Your answer:**")
        st.info(user_ans)

        # Score badge
        score_css   = {2: "score-pill-2", 1: "score-pill-1", 0: "score-pill-0"}
        score_label = {
            2: "✅ 2 / 2 points — Correct",
            1: "⚠️ 1 / 2 points — Partially correct",
            0: "❌ 0 / 2 points — Incorrect",
        }
        st.markdown(
            f'<p class="{score_css[score]}">{score_label[score]}</p>',
            unsafe_allow_html=True,
        )

        # AI feedback box
        box_class = {2: "feedback-correct", 1: "feedback-partial", 0: "feedback-wrong"}[score]
        icon       = {2: "🎉", 1: "⚠️", 0: "❌"}[score]
        title      = {2: "Well done!", 1: "Evaluation:", 0: "Evaluation:"}[score]

        right_line   = f'<br><br><strong>✓ What you got right:</strong> {ev["what_right"]}' if ev.get("what_right") and ev["what_right"] not in ("Nothing", "") else ""
        missing_line = f'<br><strong>✗ What was missing:</strong> {ev["what_missing"]}' if score < 2 and ev.get("what_missing") and ev["what_missing"] not in ("Nothing", "") else ""

        st.markdown(
            f'<div class="{box_class}"><strong>{icon} {title}</strong><br>{ev["feedback"]}{right_line}{missing_line}</div>',
            unsafe_allow_html=True,
        )

        # Consequence (shown when answer is wrong or partial)
        if score < 2:
            st.markdown(
                f'<div class="consequence-box">⚡ <strong>Consequence of incorrect behaviour:</strong><br>{q["consequence"]}</div>',
                unsafe_allow_html=True,
            )

        # Correct approach
        st.markdown(
            f'<div class="correct-box">📖 <strong>Correct approach:</strong><br>{q["correct_approach"]}</div>',
            unsafe_allow_html=True,
        )

        # Takeaway
        st.markdown(
            f'<div class="takeaway-box">💡 <strong>Compliance takeaway:</strong><br>{q["takeaway"]}</div>',
            unsafe_allow_html=True,
        )

        st.markdown("")
        next_label = "➡️ Next Question" if q_idx + 1 < total else "🏁 View Results"
        if st.button(next_label, use_container_width=True, type="primary"):
            st.session_state.q_idx += 1
            st.session_state.answered = False
            st.session_state.evaluation = None
            st.session_state.user_answer = ""
            if st.session_state.q_idx >= total:
                st.session_state.game_state = "results"
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# PLAYING — ABCD TEST
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.game_state == "playing" and st.session_state.test_type == "abcd":

    total = st.session_state.num_questions
    round_num = len(st.session_state.history)

    if round_num >= total:
        st.session_state.game_state = "results"
        st.rerun()

    c1, c2, c3 = st.columns([3, 2, 2])
    with c1: st.markdown(f"**{st.session_state.module}**")
    with c2: st.markdown(f"Scenario **{round_num + 1}** / {total}")
    with c3:
        correct_count = sum(1 for h in st.session_state.history if h.get("right"))
        st.markdown(f"✅ Score: **{correct_count}** / {round_num}")

    st.progress(round_num / total)
    st.divider()

    if st.session_state.current_scenario is None:
        diff = difficulty_label(round_num, total)
        with st.spinner(f"🤖 AI is generating a scenario ({diff} difficulty)..."):
            try:
                topics = ABCD_MODULES[st.session_state.module]
                sc = generate_abcd_scenario(
                    st.session_state.module, topics,
                    st.session_state.role, diff
                )
                st.session_state.current_scenario = sc
                st.session_state.answered = False
                st.session_state.selected_choice = None
            except Exception as e:
                st.error(f"Error generating scenario: {e}")
                st.stop()

    sc = st.session_state.current_scenario

    st.markdown(
        f'<div class="scenario-box">📋 <strong>Situation:</strong><br><br>{sc["scenario"]}</div>',
        unsafe_allow_html=True,
    )

    if not st.session_state.answered:
        st.markdown("**What do you do?**")
        cols = st.columns(2)
        chosen = None
        for i, (key, text) in enumerate(sc["choices"].items()):
            with cols[i % 2]:
                if st.button(f"**{key})** {text}", key=f"ch_{key}", use_container_width=True):
                    chosen = key
        if chosen:
            st.session_state.selected_choice = chosen
            st.session_state.answered = True
            is_correct = chosen == sc["correct"]
            st.session_state.history.append({
                "round": round_num + 1,
                "topic": st.session_state.module,
                "scenario_short": sc["scenario"][:80] + "...",
                "chosen": chosen,
                "chosen_text": sc["choices"][chosen],
                "correct": sc["correct"],
                "correct_text": sc["choices"][sc["correct"]],
                "right": is_correct,
            })
            st.rerun()
    else:
        chosen = st.session_state.selected_choice
        is_correct = chosen == sc["correct"]

        for key, text in sc["choices"].items():
            if key == sc["correct"]:
                st.success(f"✅ **{key})** {text}")
            elif key == chosen and not is_correct:
                st.error(f"❌ **{key})** {text} ← your choice")
            else:
                st.write(f"&nbsp;&nbsp;**{key})** {text}")

        st.markdown("---")
        consequence = sc["consequences"][chosen]
        box = "feedback-correct" if is_correct else "feedback-wrong"
        icon = "🎉 Correct!" if is_correct else "⚠️ Incorrect."
        st.markdown(f'<div class="{box}"><strong>{icon}</strong><br>{consequence}</div>', unsafe_allow_html=True)

        if not is_correct:
            correct_consequence = sc["consequences"][sc["correct"]]
            st.markdown(
                f'<div class="consequence-box">⚡ <strong>The correct approach would mean:</strong><br>{correct_consequence}</div>',
                unsafe_allow_html=True,
            )

        st.markdown(
            f'<div class="correct-box">📖 <strong>Explanation:</strong><br>{sc["explanation"]}</div>',
            unsafe_allow_html=True,
        )

        st.markdown("")
        next_label = "➡️ Next Scenario" if round_num + 1 < total else "🏁 Results"
        if st.button(next_label, use_container_width=True, type="primary"):
            st.session_state.current_scenario = None
            st.session_state.answered = False
            if len(st.session_state.history) >= total:
                st.session_state.game_state = "results"
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# RESULTS
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.game_state == "results":
    st.title("🏁 Test Results")
    st.divider()

    history = st.session_state.history
    test_type = st.session_state.test_type

    if test_type == "onboarding":
        total_q = st.session_state.num_questions
        max_pts = total_q * 2
        earned = st.session_state.score
        pct = round(earned / max_pts * 100) if max_pts > 0 else 0
        passed = pct >= 60
        full_name = f"{st.session_state.first_name} {st.session_state.last_name}"

        if passed:
            st.markdown(
                f'<div class="result-pass">✅ TEST PASSED — {pct}%<br>({earned} / {max_pts} points)</div>',
                unsafe_allow_html=True,
            )

            if pct >= 80:
                badge, msg = "🥇 Compliance Expert", "Excellent result! You demonstrate a strong understanding of compliance rules."
            else:
                badge, msg = "🥈 Compliance Associate", "Good foundation. We recommend reviewing the areas where you made mistakes."

            st.markdown(f"### Congratulations, {st.session_state.first_name}! {badge}")
            st.success(msg)

            c1, c2, c3 = st.columns(3)
            c1.metric("Points scored", f"{earned} / {max_pts}")
            c2.metric("Score", f"{pct}%")
            c3.metric("Result", "✅ Passed")

            # ── PDF Certificate download ───────────────────────────────────────
            st.divider()
            st.markdown("#### 🎓 Download your certificate")
            try:
                pdf_bytes = generate_certificate(
                    st.session_state.first_name,
                    st.session_state.last_name,
                    earned, max_pts, pct
                )
                st.download_button(
                    label="⬇️ Download Certificate (PDF)",
                    data=pdf_bytes,
                    file_name=f"compliance_certificate_{st.session_state.first_name}_{st.session_state.last_name}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                    type="primary",
                )
            except Exception as e:
                st.warning(f"Could not generate certificate: {e}")

        else:
            # ── Failed — simple message, no certificate ────────────────────────
            st.markdown(
                f'<div class="result-fail">❌ TEST FAILED — {pct}%<br>({earned} / {max_pts} points)</div>',
                unsafe_allow_html=True,
            )
            st.error(
                f"**Insufficient score.** You scored **{pct}%** — the minimum required is **60%**.\n\n"
                "Please review the training materials and retake the test."
            )

            c1, c2, c3 = st.columns(3)
            c1.metric("Points scored", f"{earned} / {max_pts}")
            c2.metric("Score", f"{pct}%")
            c3.metric("Result", "❌ Failed")

        st.divider()
        st.markdown("#### Question Review")
        for h in history:
            s = h["score"]
            icon = "✅" if s == 2 else ("⚠️" if s == 1 else "❌")
            with st.expander(f"{icon} Q{h['q_num']} — {h['topic']} ({s}/2 pts)"):
                st.markdown(f"**Scenario:** {h['scenario_short']}")
                st.markdown(f"**Your answer:** {h['user_answer']}")
                st.markdown(f"**Feedback:** {h['feedback']}")
                if s < 2:
                    st.markdown(
                        f'<div class="consequence-box">⚡ <strong>Consequence:</strong><br>{h["consequence"]}</div>',
                        unsafe_allow_html=True,
                    )
                st.markdown(
                    f'<div class="takeaway-box">💡 {h["takeaway"]}</div>',
                    unsafe_allow_html=True,
                )

    else:
        correct = sum(1 for h in history if h.get("right"))
        total_q = len(history)
        pct = round(correct / total_q * 100) if total_q else 0
        passed = pct >= 60

        if passed:
            st.markdown(f'<div class="result-pass">✅ TEST PASSED — {pct}% ({correct}/{total_q})</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="result-fail">❌ TEST FAILED — {pct}% ({correct}/{total_q})</div>', unsafe_allow_html=True)

        st.divider()
        st.markdown("#### Scenario Review")
        for h in history:
            icon = "✅" if h["right"] else "❌"
            with st.expander(f"{icon} Scenario {h['round']}: {h['scenario_short']}"):
                if h["right"]:
                    st.success(f"Correct: **{h['correct']})** {h['correct_text']}")
                else:
                    st.error(f"Your choice: **{h['chosen']})** {h['chosen_text']}")
                    st.success(f"Correct answer: **{h['correct']})** {h['correct_text']}")

    st.divider()
    if st.button("🔄 Start New Test", use_container_width=True, type="primary"):
        reset_game()
        st.rerun()

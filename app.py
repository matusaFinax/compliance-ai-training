import streamlit as st
import anthropic
import json

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Finax Compliance Training",
    page_icon="🛡️",
    layout="centered",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .scenario-box {
        background: #1e2761;
        color: white;
        padding: 1.5rem;
        border-radius: 12px;
        font-size: 1.05rem;
        line-height: 1.6;
        margin-bottom: 1.5rem;
    }
    .feedback-correct {
        background: #d4edda;
        border-left: 5px solid #28a745;
        padding: 1rem 1.5rem;
        border-radius: 8px;
        margin-top: 1rem;
    }
    .feedback-wrong {
        background: #f8d7da;
        border-left: 5px solid #dc3545;
        padding: 1rem 1.5rem;
        border-radius: 8px;
        margin-top: 1rem;
    }
    .explanation-box {
        background: #fff3cd;
        border-left: 5px solid #ffc107;
        padding: 1rem 1.5rem;
        border-radius: 8px;
        margin-top: 0.5rem;
    }
    .score-badge {
        font-size: 2rem;
        font-weight: bold;
        text-align: center;
        padding: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# ── Moduly z Finax materiálov ─────────────────────────────────────────────────
MODULES = {
    "🔍 MAR – Market Abuse": (
        "market abuse regulation, insider trading, inside information, price manipulation, "
        "pump and dump, market manipulation, osobné obchody, obchodovanie na základe neverejných informácií"
    ),
    "⚖️ Konflikt záujmov": (
        "conflict of interest, osobné investície, rodinné vzťahy s dodávateľmi, "
        "rozhodovanie pri konflikte záujmov, actual vs perceived vs potential conflict"
    ),
    "🎁 Anti-korupcia & Dary": (
        "bribery, corruption, gifts from clients, dary od klientov, "
        "politické príspevky, úplatkárstvo, nízkohodnotné dary, firemná politika darov"
    ),
    "💬 Klientská komunikácia (MiFID II)": (
        "client communication, MiFID II, misleading information, guaranteed returns, "
        "vhodnosť produktu, suitability test, transparentnosť poplatkov, rizikový profil klienta"
    ),
    "🔒 Ochrana dát & GDPR": (
        "personal data protection, GDPR, clean desk policy, need to know principle, "
        "pseudonymizácia, zdieľanie dát s tretími stranami, súhlas so spracovaním"
    ),
    "📢 Whistleblowing & Podvody": (
        "reporting violations, anonymous reporting, whistleblowing, CEO fraud, "
        "podvody cez email, zmena platobných údajov, časový tlak, deepfake"
    ),
}

ROLES = ["Všeobecný zamestnanec", "Sales / Poradca", "Manažér", "IT / Operácie"]

SYSTEM_PROMPT = """Si compliance tréningový systém pre Finax — investičnú spoločnosť regulovanú NBS na Slovensku.
Generuješ realistické compliance scenáre pre zamestnancov vo forme interaktívneho tréningu.

Pravidlá:
- Scenár musí byť konkrétny, uveriteľný a z reálneho pracovného prostredia finančnej firmy
- Vždy musí existovať JEDNA jasne správna odpoveď podľa compliance pravidiel
- Nesprávne odpovede musia byť uveriteľné (nie absurdné) — typické chyby, ktoré ľudia naozaj robia
- Konzekvencia nesprávnej odpovede musí byť dramatická a realistická (pokuta, vyšetrovanie, strata klienta...)
- Píš v slovenčine, 2. osoba ("Ste...", "Váš klient...", "Vám volá...")

Odpovedaj VÝHRADNE validným JSON objektom — žiadny iný text, žiadne markdown bloky:
{
  "scenario": "Popis situácie v 2-3 vetách",
  "choices": {
    "A": "text možnosti A",
    "B": "text možnosti B",
    "C": "text možnosti C",
    "D": "text možnosti D"
  },
  "correct": "písmeno správnej odpovede (A/B/C/D)",
  "consequences": {
    "A": "Čo sa stane — 1-2 vety. Ak nesprávne: začni dramatickou konzekvenciou.",
    "B": "...",
    "C": "...",
    "D": "..."
  },
  "explanation": "Prečo je správna odpoveď správna — 2-3 vety, odvolaj sa na konkrétne pravidlo alebo reguláciu."
}"""


# ── Session state init ────────────────────────────────────────────────────────
def init_state():
    defaults = {
        "game_state": "setup",   # setup | playing | results
        "api_key": "",
        "role": ROLES[0],
        "module": list(MODULES.keys())[0],
        "total_rounds": 5,
        "round": 0,
        "score": 0,
        "current_scenario": None,
        "answered": False,
        "selected_choice": None,
        "history": [],           # list of {scenario, chosen, correct, right}
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()


# ── AI: generovanie scenára ───────────────────────────────────────────────────
def generate_scenario(module_name: str, topics: str, role: str, difficulty: str) -> dict:
    client = anthropic.Anthropic(api_key=st.session_state.api_key)
    user_msg = (
        f"Modul: {module_name}\n"
        f"Témy: {topics}\n"
        f"Rola zamestnanca: {role}\n"
        f"Obtiažnosť: {difficulty}\n\n"
        "Vygeneruj jeden nový scenár."
    )
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_msg}],
    )
    raw = response.content[0].text.strip()
    # Odstráni prípadné markdown bloky ak ich model pridá
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw)


# ── Helpers ───────────────────────────────────────────────────────────────────
def difficulty_for_round(r: int, total: int) -> str:
    pct = r / total
    if pct < 0.4:
        return "ľahká"
    elif pct < 0.75:
        return "stredná"
    else:
        return "ťažká"

def score_pct() -> int:
    if st.session_state.round == 0:
        return 0
    return round(st.session_state.score / st.session_state.round * 100)

def reset_game():
    for k in ["game_state","round","score","current_scenario","answered",
              "selected_choice","history"]:
        del st.session_state[k]
    init_state()


# ══════════════════════════════════════════════════════════════════════════════
# OBRAZOVKA 1 — SETUP
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.game_state == "setup":
    st.title("🛡️ Finax Compliance Training")
    st.markdown("#### Interaktívne scenáre generované umelou inteligenciou")
    st.divider()

    with st.form("setup_form"):
        api_key = st.text_input(
            "🔑 Anthropic API kľúč",
            type="password",
            placeholder="sk-ant-...",
            help="Nájdeš ho na console.anthropic.com",
        )
        role = st.selectbox("👤 Tvoja rola", ROLES)
        module = st.selectbox("📚 Compliance modul", list(MODULES.keys()))
        rounds = st.slider("Počet scenárov", min_value=3, max_value=8, value=5)

        submitted = st.form_submit_button("🚀 Spustiť tréning", use_container_width=True)

    if submitted:
        if not api_key.strip():
            st.error("Zadaj API kľúč.")
        else:
            st.session_state.api_key = api_key.strip()
            st.session_state.role = role
            st.session_state.module = module
            st.session_state.total_rounds = rounds
            st.session_state.game_state = "playing"
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# OBRAZOVKA 2 — HRA
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.game_state == "playing":

    # ── Header ────────────────────────────────────────────────────────────────
    col1, col2, col3 = st.columns([3, 2, 2])
    with col1:
        st.markdown(f"**{st.session_state.module}**")
    with col2:
        st.markdown(f"Scenár **{st.session_state.round + 1}** / {st.session_state.total_rounds}")
    with col3:
        st.markdown(f"✅ Skóre: **{st.session_state.score}** / {st.session_state.round}")

    progress = st.session_state.round / st.session_state.total_rounds
    st.progress(progress)
    st.divider()

    # ── Generovanie scenára ───────────────────────────────────────────────────
    if st.session_state.current_scenario is None:
        difficulty = difficulty_for_round(
            st.session_state.round, st.session_state.total_rounds
        )
        with st.spinner(f"🤖 AI generuje scenár ({difficulty} obtiažnosť)..."):
            try:
                topics = MODULES[st.session_state.module]
                scenario = generate_scenario(
                    st.session_state.module, topics,
                    st.session_state.role, difficulty
                )
                st.session_state.current_scenario = scenario
                st.session_state.answered = False
                st.session_state.selected_choice = None
            except Exception as e:
                st.error(f"Chyba pri generovaní scenára: {e}")
                st.stop()

    scenario = st.session_state.current_scenario

    # ── Zobrazenie scenára ────────────────────────────────────────────────────
    st.markdown(
        f'<div class="scenario-box">📋 <strong>Situácia:</strong><br><br>{scenario["scenario"]}</div>',
        unsafe_allow_html=True,
    )

    # ── Odpovede ──────────────────────────────────────────────────────────────
    if not st.session_state.answered:
        st.markdown("**Čo urobíte?**")
        cols = st.columns(2)
        choices = scenario["choices"]
        choice_keys = list(choices.keys())

        chosen = None
        for i, key in enumerate(choice_keys):
            with cols[i % 2]:
                if st.button(
                    f"**{key})** {choices[key]}",
                    key=f"choice_{key}",
                    use_container_width=True,
                ):
                    chosen = key

        if chosen:
            st.session_state.selected_choice = chosen
            st.session_state.answered = True
            is_correct = chosen == scenario["correct"]
            if is_correct:
                st.session_state.score += 1
            st.session_state.history.append({
                "round": st.session_state.round + 1,
                "scenario": scenario["scenario"][:80] + "...",
                "chosen": chosen,
                "chosen_text": choices[chosen],
                "correct": scenario["correct"],
                "correct_text": choices[scenario["correct"]],
                "right": is_correct,
            })
            st.rerun()

    # ── Spätná väzba po odpovedi ──────────────────────────────────────────────
    else:
        chosen = st.session_state.selected_choice
        is_correct = chosen == scenario["correct"]
        choices = scenario["choices"]

        # Zobraziť všetky možnosti (zvýraznené)
        st.markdown("**Vaša odpoveď:**")
        for key, text in choices.items():
            if key == scenario["correct"]:
                st.success(f"✅ **{key})** {text}")
            elif key == chosen and not is_correct:
                st.error(f"❌ **{key})** {text} ← vaša voľba")
            else:
                st.write(f"&nbsp;&nbsp;**{key})** {text}")

        st.markdown("---")

        # Konzekvencia
        consequence = scenario["consequences"][chosen]
        if is_correct:
            st.markdown(
                f'<div class="feedback-correct">🎉 <strong>Správne!</strong><br>{consequence}</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div class="feedback-wrong">⚠️ <strong>Nesprávne.</strong><br>{consequence}</div>',
                unsafe_allow_html=True,
            )

        # Vysvetlenie pravidla
        st.markdown(
            f'<div class="explanation-box">📖 <strong>Prečo?</strong><br>{scenario["explanation"]}</div>',
            unsafe_allow_html=True,
        )

        st.markdown("")

        # Tlačidlo ďalej
        next_label = (
            "➡️ Ďalší scenár"
            if st.session_state.round + 1 < st.session_state.total_rounds
            else "🏁 Zobraziť výsledky"
        )
        if st.button(next_label, use_container_width=True, type="primary"):
            st.session_state.round += 1
            st.session_state.current_scenario = None
            if st.session_state.round >= st.session_state.total_rounds:
                st.session_state.game_state = "results"
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# OBRAZOVKA 3 — VÝSLEDKY
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.game_state == "results":
    st.title("🏁 Výsledky tréningu")
    st.divider()

    pct = score_pct()
    total = st.session_state.total_rounds
    score = st.session_state.score

    # Hodnotenie
    if pct >= 80:
        badge = "🥇 Compliance Expert"
        color = "#28a745"
        msg = "Výborný výsledok! Pravidlá ovládaš na vysokej úrovni."
    elif pct >= 60:
        badge = "🥈 Compliance Associate"
        color = "#ffc107"
        msg = "Dobrý základ. Odporúčame zopakovať slabšie témy."
    else:
        badge = "🥉 Compliance Rookie"
        color = "#dc3545"
        msg = "Treba zapracovať. Zopakuj modul a skús znova."

    st.markdown(
        f'<div class="score-badge" style="color:{color}">{badge}</div>',
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)
    col1.metric("Správne", f"{score} / {total}")
    col2.metric("Úspešnosť", f"{pct} %")
    col3.metric("Modul", st.session_state.module.split(" ", 1)[1][:20])

    st.info(msg)
    st.divider()

    # Prehľad odpovedí
    st.markdown("#### Prehľad scenárov")
    for h in st.session_state.history:
        icon = "✅" if h["right"] else "❌"
        with st.expander(f"{icon} Scenár {h['round']}: {h['scenario']}"):
            if h["right"]:
                st.success(f"Správne: **{h['correct']})** {h['correct_text']}")
            else:
                st.error(f"Vaša odpoveď: **{h['chosen']})** {h['chosen_text']}")
                st.success(f"Správna odpoveď: **{h['correct']})** {h['correct_text']}")

    st.divider()
    if st.button("🔄 Nový tréning", use_container_width=True, type="primary"):
        reset_game()
        st.rerun()

import streamlit as st
import anthropic
import json
import random

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Finax Compliance Training",
    page_icon="🛡️",
    layout="centered",
)

# ── CSS — explicitný tmavý text vo všetkých farebných boxoch ─────────────────
st.markdown("""
<style>
    /* Všetky farebné boxy musia mať tmavý text — oprava pre dark mode */
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
    .score-pill-3 { color: #1a7f3c; font-weight: bold; font-size: 1.1rem; }
    .score-pill-2 { color: #b07a00; font-weight: bold; font-size: 1.1rem; }
    .score-pill-1 { color: #c0001a; font-weight: bold; font-size: 1.1rem; }
    /* Výsledková obrazovka */
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
# BANKA OTÁZOK — z Finax compliance materiálov
# ══════════════════════════════════════════════════════════════════════════════
QUESTION_BANK = [
    {
        "id": 1,
        "topic": "Ochrana dát & GDPR",
        "scenario": (
            "Pracujete v kancelárii a vytlačili ste dokumenty s osobnými údajmi klientov "
            "(mená, emaily, investičné detaily). Musíte odísť na obed.\n\n"
            "Môžete tieto dokumenty nechať viditeľné na stole v zdieľanom priestore?"
        ),
        "correct_approach": (
            "Nie. Musíte dodržať Clean Desk Policy a zabezpečiť všetky citlivé dokumenty pred odchodom. "
            "Zabezpečiť, aby mal prístup k údajom iba oprávnený personál (princíp need-to-know). "
            "Chrániť osobné údaje pred neoprávneným prístupom — uložiť do šuplíka, skartovačky alebo uzamknutej skrinky."
        ),
        "takeaway": "Nikdy nenechávajte osobné údaje odkryté — pred odchodom ich vždy zabezpečte.",
        "consequence": (
            "Ak necháte dokumenty s osobnými údajmi klientov odkryté, hrozí neoprávnený prístup tretích osôb. "
            "Porušenie GDPR môže znamenať pokutu pre Finax až 20 mil. € alebo 4 % ročného obratu. "
            "Zamestnanec môže čeliť disciplinárnemu konaniu."
        ),
    },
    {
        "id": 2,
        "topic": "Ochrana dát & GDPR",
        "scenario": (
            "Kolega z iného oddelenia vás žiada, aby ste mu poslali súbor s osobnými údajmi klientov "
            "— tvrdí, že 'ich možno neskôr bude potrebovať'.\n\n"
            "Môžete mu dáta zdieľať, keďže je tiež zamestnancom Finax?"
        ),
        "correct_approach": (
            "Nie. Osobné údaje možno zdieľať len keď existuje konkrétny, legitímny obchodný dôvod. "
            "Treba overiť, či je kolega oprávnený na prístup k týmto dátam. "
            "Aplikovať princíp minimalizácie dát — posielať len to, čo je nevyhnutné. "
            "Kde je to možné, použiť anonymizované alebo pseudonymizované dáta."
        ),
        "takeaway": "Interný prístup nie je automatický — zdieľanie dát musí byť vždy odôvodnené konkrétnym účelom.",
        "consequence": (
            "Zdieľanie osobných údajov bez oprávneného dôvodu porušuje GDPR a internú politiku Finax. "
            "Môže dôjsť k úniku citlivých klientských informácií, disciplinárnemu konaniu a regulatorným sankciám."
        ),
    },
    {
        "id": 3,
        "topic": "Podvody (Fraud)",
        "scenario": (
            "Dostanete email zdanlivo od senior manažéra. Žiada urgentný prevod finančných prostriedkov "
            "na nový bankový účet, zdôrazňuje, že to musí byť urobené okamžite, a žiada vás, "
            "aby ste nevolali kvôli 'dôvernosti transakcie'.\n\n"
            "Čo urobíte?"
        ),
        "correct_approach": (
            "Nevykonajte prevod. Nezávisle overte požiadavku cez iný komunikačný kanál — "
            "zavolajte manažérovi priamo na jeho overené číslo. "
            "Postupujte podľa interných procedúr pre podozrivé finančné požiadavky. "
            "Nahláste incident compliance alebo bezpečnostnému tímu."
        ),
        "takeaway": "Časový tlak + zákaz telefonátu = varovný signál CEO fraud. Vždy overte cez druhý kanál.",
        "consequence": (
            "Vykonanie prevodu bez overenia je klasický CEO fraud / Business Email Compromise. "
            "Spoločnosť môže prísť o finančné prostriedky a zamestnanec môže niesť "
            "disciplinárnu zodpovednosť. Takéto podvody ročne stoja firmy milióny eur."
        ),
    },
    {
        "id": 4,
        "topic": "Podvody (Fraud)",
        "scenario": (
            "Osoba vám napíše email a tvrdí, že je klientom Finax. Urgentne žiada, "
            "aby ste jej poslali aktualizované osobné a účtové informácie kvôli 'systémovej chybe', "
            "pričom trvá na tom, že email je momentálne jediný dostupný spôsob kontaktu.\n\n"
            "Čo urobíte?"
        ),
        "correct_approach": (
            "Nezdieľajte žiadne klientské údaje. "
            "Overte totožnosť klienta prostredníctvom zavedených autentifikačných postupov Finax. "
            "Nespoliehajte sa na jediný komunikačný kanál — zavolajte klientovi na registrované číslo. "
            "Nahláste podozrivú požiadavku."
        ),
        "takeaway": "Nikdy neposielajte citlivé údaje bez riadneho overenia totožnosti, najmä cez jediný kanál.",
        "consequence": (
            "Odoslanie klientských údajov bez overenia vedie k úniku osobných dát a porušeniu GDPR. "
            "Klient môže byť finančne poškodený, Finax čelí sankciám a strate dôvery klientov."
        ),
    },
    {
        "id": 5,
        "topic": "Konflikt záujmov",
        "scenario": (
            "Ste zodpovedný za správu vzťahu s novým klientom. Počas onboardingu zistíte, "
            "že klient je váš blízky osobný priateľ. Priateľ vás žiada, "
            "aby ste 'extra starostlivo' spravovali jeho portfólio a uprednostnili jeho požiadavky pred ostatnými.\n\n"
            "Čo urobíte?"
        ),
        "correct_approach": (
            "Identifikovať a nahlásiť konflikt záujmov compliance oddeleniu čo najskôr. "
            "V prípade potreby sa vylúčiť z rozhodovacieho procesu pri tomto klientovi. "
            "Zdokumentovať situáciu v registri konfliktov záujmov."
        ),
        "takeaway": "Konflikty záujmov musia byť nahlásené Compliance, nie riešené neformálne. Vždy informujte včas.",
        "consequence": (
            "Neriadené uprednostňovanie blízkeho klienta môže viesť k neobjektívnym investičným rozhodnutiam, "
            "poškodeniu ostatných klientov, porušeniu MiFID II a disciplinárnemu konaniu."
        ),
    },
    {
        "id": 6,
        "topic": "Konflikt záujmov",
        "scenario": (
            "Vyberáte medzi dvoma podobnými investičnými produktmi pre klienta. "
            "Jeden produkt prináša vášmu tímu vyšší interný stimul (bonus), "
            "zatiaľ čo druhý môže byť pre klienta mierne vhodnejší.\n\n"
            "Ako postupujete?"
        ),
        "correct_approach": (
            "Konať vždy v najlepšom záujme klienta — vyberte produkt vhodnejší pre neho. "
            "Ignorovať akýkoľvek osobný alebo firemný finančný stimul pri výbere. "
            "V prípade pochybností konzultovať s compliance oddelením."
        ),
        "takeaway": "Záujem klienta prevažuje nad osobným prospechom. Ak stimuly ovplyvňujú váš úsudok, eskalujte na Compliance.",
        "consequence": (
            "Odporúčanie produktu kvôli vyššiemu bonusu namiesto záujmu klienta porušuje MiFID II. "
            "Hrozia regulatorné sankcie, žaloby od klientov a strata povolenia na poskytovanie investičných služieb."
        ),
    },
    {
        "id": 7,
        "topic": "Anti-korupcia & Dary",
        "scenario": (
            "Klient, s ktorým máte dlhodobý dobrý vzťah, vás žiada o vašu domácu adresu. "
            "Chce vám poslať malý darček na koniec roka ako osobné poďakovanie. "
            "Zdôrazňuje, že 'firma nemusí byť zapojená' a že je to len súkromná záležitosť.\n\n"
            "Čo urobíte?"
        ),
        "correct_approach": (
            "Odmietnuť žiadosť a neposkytnúť súkromnú adresu. "
            "Informovať manažéra a/alebo compliance oddelenie o tejto situácii. "
            "Darčeky smerované na súkromnú adresu sú vždy červenou vlajkou — "
            "všetky dary musia byť transparentne nahlásené."
        ),
        "takeaway": "Darček na súkromnú adresu = červená vlajka. Odmietni a nahláš. Dary musia byť vždy transparentné.",
        "consequence": (
            "Prijatie darčeka na súkromnú adresu bez nahlásenia vytvára konflikt záujmov "
            "a môže byť kvalifikované ako úplatok. Hrozí disciplinárne konanie, "
            "trestné stíhanie a poškodenie reputácie Finax."
        ),
    },
    {
        "id": 8,
        "topic": "Anti-korupcia & Dary",
        "scenario": (
            "Obchodný kontakt, ktorý je zároveň miestnym primátorom, vám neformálne hovorí, "
            "že obec rozhoduje o veciach relevantných pre Finax. "
            "Potom neformálne naznačí, či by ste vy alebo Finax mohli 'podporiť' nadchádzajúcu politickú kampaň "
            "— s poznámkou, že 'dobré vzťahy sa pamätajú'.\n\n"
            "Čo urobíte?"
        ),
        "correct_approach": (
            "Okamžite odmietnuť akúkoľvek formu podpory. "
            "Eskalovať situáciu na manažéra a compliance oddelenie. "
            "Príspevky verejným funkcionárom alebo na politické účely sú zakázané."
        ),
        "takeaway": "Čokoľvek hodnotné spojené s verejným funkcionárom alebo politickým účelom musí byť odmietnuté a nahlásené.",
        "consequence": (
            "Akákoľvek podpora politickej kampane v kontexte obchodného rozhodovania môže byť kvalifikovaná "
            "ako úplatkárstvo. Ide o trestný čin s pokutami aj trestom odňatia slobody pre fyzickú osobu."
        ),
    },
    {
        "id": 9,
        "topic": "Klientská komunikácia (MiFID II)",
        "scenario": (
            "Klient sa pýta, či portfóliová stratégia 'dosiahne podobné výnosy ako minulý rok', "
            "ktorý bol výnimočne silný. Reagujete zdôraznením minuloročných výnosov "
            "a poviete, že 'stratégia funguje veľmi dobre a mala by tak pokračovať', "
            "bez akéhokoľvek ďalšieho vysvetlenia.\n\n"
            "Je takáto komunikácia v poriadku?"
        ),
        "correct_approach": (
            "Nie. Treba jasne vysvetliť, že minulá výkonnosť nie je zárukou budúcich výsledkov. "
            "Poskytnúť vyvážené scenáre vrátane možnosti negatívnych výsledkov. "
            "Akúkoľvek diskusiu o budúcej výkonnosti prezentovať len ako odhad na základe predpokladov."
        ),
        "takeaway": "Vždy prezentujte výkonnosť vyváženým spôsobom — nikdy nie selektívne. Riziká musia byť explicitne komunikované.",
        "consequence": (
            "Zavádzajúca komunikácia o výkonnosti porušuje MiFID II. "
            "Hrozia regulatorné sankcie, žaloby od klientov za stratu a trvalé poškodenie dôvery."
        ),
    },
    {
        "id": 10,
        "topic": "Klientská komunikácia (MiFID II)",
        "scenario": (
            "Počas hovoru sa klient zaujíma o nový investičný produkt. "
            "Aby ste konverzáciu zjednodušili, vysvetlíte potenciálne výnosy a výhody produktu, "
            "ale vynecháte informáciu o možnosti straty kapitálu a volatilite trhu.\n\n"
            "Je to v poriadku?"
        ),
        "correct_approach": (
            "Nie. Klientovi musíte poskytnúť úplné a transparentné informácie vrátane všetkých podstatných rizík: "
            "strata kapitálu, volatilita trhu, likviditné riziko. "
            "Aj keď to konverzáciu skomplikuje — klient má právo na úplné informácie."
        ),
        "takeaway": "Plná transparentnosť = výhody aj riziká. Zamlčanie rizík nie je zjednodušenie, je to porušenie MiFID II.",
        "consequence": (
            "Zamlčanie kľúčových rizík porušuje MiFID II a povinnosť informovať klienta. "
            "Hrozia sťažnosti klientov, regulatorné pokuty a disciplinárne konanie."
        ),
    },
    {
        "id": 11,
        "topic": "Market Abuse (MAR)",
        "scenario": (
            "Spozorujete, že kolega v marketingovom tíme pripravuje prezentáciu pre klientov, "
            "kde ukazuje výkonnosť produktu za posledné 3 roky. "
            "Viete však, že produkt existuje 7 rokov a prvé 4 roky boli slabé. "
            "Kolega tvrdí, že 'klienti aj tak chcú vidieť len to pekné'.\n\n"
            "Čo urobíte?"
        ),
        "correct_approach": (
            "Upozorniť kolegu, že prezentácia musí zahŕňať celé dostupné obdobie výkonnosti — nie len vybrané roky. "
            "Selektívne zobrazovanie je zavádzajúce a porušuje pravidlá. "
            "Ak kolega nesúhlasí, kontaktovať compliance oddelenie pred odoslaním materiálu."
        ),
        "takeaway": "Prezentácia výkonnosti musí byť úplná, pravdivá a nestranná. Selekcia 'dobrých' rokov je manipulácia.",
        "consequence": (
            "Selektívna prezentácia výkonnosti môže byť kvalifikovaná ako manipulácia s trhom podľa MAR. "
            "Hrozia regulatorné sankcie v miliónoch eur aj trestné stíhanie."
        ),
    },
    {
        "id": 12,
        "topic": "Market Abuse (MAR)",
        "scenario": (
            "Pracujete v oddelení klientského servisu. Klient vám napíše, "
            "že jeho priateľ videl online 'uniknuté informácie', "
            "že energetická spoločnosť bude mať výnimočne dobré výsledky — ešte pred zverejnením. "
            "Klient sa pýta, či by si mal rýchlo kúpiť akcie.\n\n"
            "Čo mu poviete?"
        ),
        "correct_approach": (
            "Vysvetliť klientovi, že 'uniknuté' informácie môžu byť nespoľahlivé, manipulované alebo úmyselne šírené. "
            "Poradiť mu rozhodovať sa výhradne na základe verejných, overených informácií dostupných pre všetkých. "
            "Nepotvrdzo, neodmietať neverejné informácie a neodporúčať obchodovanie na ich základe."
        ),
        "takeaway": "Obchodovanie na základe neverejných informácií je insider trading. Vždy len verejné, overené dáta.",
        "consequence": (
            "Odporúčanie obchodovania na základe neverejných informácií je insider trading podľa MAR. "
            "Trest: až 7 rokov odňatia slobody a neobmedzené pokuty pre fyzickú aj právnickú osobu."
        ),
    },
]

# ── ABCD moduly (pre budúce rozšírenie) ───────────────────────────────────────
ABCD_MODULES = {
    "🔍 MAR – Market Abuse": (
        "market abuse regulation, insider trading, inside information, price manipulation"
    ),
    "⚖️ Konflikt záujmov": (
        "conflict of interest, osobné investície, rodinné vzťahy s dodávateľmi"
    ),
    "🎁 Anti-korupcia & Dary": (
        "bribery, corruption, gifts from clients, dary, úplatkárstvo"
    ),
    "💬 Klientská komunikácia (MiFID II)": (
        "MiFID II, misleading information, guaranteed returns, suitability"
    ),
    "🔒 Ochrana dát & GDPR": (
        "GDPR, clean desk policy, need to know principle"
    ),
    "📢 Whistleblowing & Podvody": (
        "whistleblowing, CEO fraud, podvody, deepfake"
    ),
}

ROLES = ["Všeobecný zamestnanec", "Sales / Poradca", "Manažér", "IT / Operácie"]

ABCD_SYSTEM_PROMPT = """Si compliance tréningový systém pre Finax — investičnú spoločnosť regulovanú NBS.
Generuješ realistické compliance scenáre vo formáte ABCD kvízu.

Odpovedaj VÝHRADNE validným JSON objektom bez akéhokoľvek iného textu:
{
  "scenario": "Popis situácie v 2-3 vetách, 2. osoba (Ste..., Váš klient...)",
  "choices": {
    "A": "text možnosti A",
    "B": "text možnosti B",
    "C": "text možnosti C",
    "D": "text možnosti D"
  },
  "correct": "A alebo B alebo C alebo D",
  "consequences": {
    "A": "Čo sa stane — 1-2 vety",
    "B": "Čo sa stane — 1-2 vety",
    "C": "Čo sa stane — 1-2 vety",
    "D": "Čo sa stane — 1-2 vety"
  },
  "explanation": "Prečo je správna odpoveď správna — 2 vety, odvolaj sa na pravidlo."
}"""

EVAL_SYSTEM_PROMPT = """Si compliance hodnotiteľ pre Finax. Dostaneš otázku, správnu odpoveď a odpoveď zamestnanca.
Ohodnoť odpoveď a odpovedaj VÝHRADNE validným JSON bez iného textu:
{
  "score": 1 alebo 2 alebo 3,
  "feedback": "Personalizovaný komentár k odpovedi zamestnanca — čo bolo správne a čo chýbalo (2-3 vety)",
  "what_right": "Čo zamestnanec uviedol správne (1 veta, alebo 'Nič' ak skóre=1)",
  "what_missing": "Čo chýbalo alebo bolo nesprávne (1 veta, alebo 'Nič' ak skóre=3)"
}

Bodovanie:
- 3: Odpoveď obsahuje všetky kľúčové prvky správneho prístupu
- 2: Odpoveď obsahuje niektoré správne prvky ale niečo dôležité chýba alebo je nesprávne
- 1: Odpoveď je prevažne nesprávna alebo úplne chýba pochopenie compliance pravidla"""


# ── Session state ─────────────────────────────────────────────────────────────
def init_state():
    defaults = {
        "game_state": "setup",
        "test_type": "onboarding",
        "api_key": "",
        "role": ROLES[0],
        "module": list(ABCD_MODULES.keys())[0],
        "num_questions": 5,
        "questions": [],        # vybrané otázky pre onboarding test
        "q_idx": 0,             # aktuálny index otázky
        "score": 0,             # suma bodov (onboarding: 1-3 per q)
        "current_scenario": None,  # pre ABCD
        "answered": False,
        "selected_choice": None,   # ABCD
        "evaluation": None,        # onboarding eval dict
        "user_answer": "",
        "history": [],
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()


# ── AI: hodnotenie voľnej odpovede ────────────────────────────────────────────
def evaluate_answer(question: dict, user_answer: str) -> dict:
    client = anthropic.Anthropic(api_key=st.session_state.api_key)
    user_msg = (
        f"OTÁZKA / SCENÁR:\n{question['scenario']}\n\n"
        f"SPRÁVNY PRÍSTUP:\n{question['correct_approach']}\n\n"
        f"ODPOVEĎ ZAMESTNANCA:\n{user_answer}"
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


# ── AI: generovanie ABCD scenára ──────────────────────────────────────────────
def generate_abcd_scenario(module_name: str, topics: str, role: str, difficulty: str) -> dict:
    client = anthropic.Anthropic(api_key=st.session_state.api_key)
    user_msg = (
        f"Modul: {module_name}\nTémy: {topics}\n"
        f"Rola: {role}\nObtiažnosť: {difficulty}\n\nVygeneruj jeden scenár."
    )
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,   # zvýšené — predchádza skráteniu JSON
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
    if pct < 0.4: return "ľahká"
    elif pct < 0.75: return "stredná"
    return "ťažká"


def reset_game():
    keys = ["game_state","test_type","num_questions","questions","q_idx","score",
            "current_scenario","answered","selected_choice","evaluation","user_answer","history"]
    for k in keys:
        if k in st.session_state:
            del st.session_state[k]
    init_state()


# ══════════════════════════════════════════════════════════════════════════════
# SETUP
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.game_state == "setup":
    st.title("🛡️ Finax Compliance Training")
    st.markdown("#### Interaktívne compliance vzdelávanie")
    st.divider()

    with st.form("setup_form"):
        api_key = st.text_input(
            "🔑 Anthropic API kľúč", type="password", placeholder="sk-ant-...",
        )
        role = st.selectbox("👤 Vaša rola", ROLES)

        test_choice = st.radio(
            "📚 Typ testu",
            ["🎓 Onboarding Test — Všeobecný (odporúčané)", "⚙️ Tematický ABCD test (experimentálne)"],
            index=0,
        )

        num_q = None
        abcd_module = None

        if "Onboarding" in test_choice:
            num_q = st.select_slider(
                "Počet otázok", options=[5, 10], value=5,
                help="5 otázok ≈ 10 min | 10 otázok ≈ 20 min"
            )
        else:
            abcd_module = st.selectbox("Modul", list(ABCD_MODULES.keys()))

        submitted = st.form_submit_button("🚀 Spustiť test", use_container_width=True)

    if submitted:
        if not api_key.strip():
            st.error("Zadaj API kľúč.")
        else:
            st.session_state.api_key = api_key.strip()
            st.session_state.role = role
            if "Onboarding" in test_choice:
                st.session_state.test_type = "onboarding"
                st.session_state.num_questions = num_q
                # Náhodný výber otázok bez opakovania
                st.session_state.questions = random.sample(QUESTION_BANK, num_q)
            else:
                st.session_state.test_type = "abcd"
                st.session_state.module = abcd_module
                st.session_state.num_questions = 5
            st.session_state.game_state = "playing"
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# HRA — ONBOARDING TEST (voľná odpoveď + AI hodnotenie)
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
    with c2: st.markdown(f"Otázka **{q_idx + 1}** / {total}")
    with c3: st.markdown(f"✅ Body: **{st.session_state.score}** / {q_idx * 3}")

    st.progress(q_idx / total)
    st.divider()

    # Scenár
    st.markdown(
        f'<div class="scenario-box">📋 <strong>Situácia:</strong><br><br>{q["scenario"].replace(chr(10), "<br>")}</div>',
        unsafe_allow_html=True,
    )

    # ── Pred odpoveďou ─────────────────────────────────────────────────────────
    if not st.session_state.answered:
        st.markdown("**Popíšte, ako by ste postupovali:**")
        user_ans = st.text_area(
            label="Vaša odpoveď",
            placeholder="Napíšte vlastnými slovami, čo by ste v tejto situácii urobili...",
            height=130,
            label_visibility="collapsed",
        )
        if st.button("✅ Odovzdať odpoveď", use_container_width=True, type="primary"):
            if not user_ans.strip():
                st.warning("Napíšte odpoveď pred odovzdaním.")
            else:
                with st.spinner("🤖 AI hodnotí vašu odpoveď..."):
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
                        st.error(f"Chyba hodnotenia: {e}")

    # ── Po odpovedi — spätná väzba ─────────────────────────────────────────────
    else:
        ev = st.session_state.evaluation
        score = ev["score"]
        user_ans = st.session_state.user_answer

        # Vaša odpoveď
        st.markdown("**Vaša odpoveď:**")
        st.info(user_ans)

        # Skóre badge
        score_colors = {3: "score-pill-3", 2: "score-pill-2", 1: "score-pill-1"}
        score_labels = {3: "✅ 3 / 3 bodov — Správne", 2: "⚠️ 2 / 3 bodov — Čiastočne správne", 1: "❌ 1 / 3 bodov — Nesprávne"}
        st.markdown(
            f'<p class="{score_colors[score]}">{score_labels[score]}</p>',
            unsafe_allow_html=True,
        )

        # Feedback AI
        if score == 3:
            box_class = "feedback-correct"
            icon = "🎉"
        elif score == 2:
            box_class = "feedback-partial"
            icon = "⚠️"
        else:
            box_class = "feedback-wrong"
            icon = "❌"

        st.markdown(
            f'<div class="{box_class}"><strong>{icon} Hodnotenie:</strong><br>{ev["feedback"]}'
            + (f'<br><br><strong>✓ Správne:</strong> {ev["what_right"]}' if ev.get("what_right") and ev["what_right"] != "Nič" else "")
            + (f'<br><strong>✗ Chýbalo:</strong> {ev["what_missing"]}' if ev.get("what_missing") and ev["what_missing"] != "Nič" and score < 3 else "")
            + "</div>",
            unsafe_allow_html=True,
        )

        # Konzekvencia (ak nesprávne alebo čiastočné)
        if score < 3:
            st.markdown(
                f'<div class="consequence-box">⚡ <strong>Dôsledok nesprávneho postupu:</strong><br>{q["consequence"]}</div>',
                unsafe_allow_html=True,
            )

        # Správny postup
        st.markdown(
            f'<div class="correct-box">📖 <strong>Správny postup:</strong><br>{q["correct_approach"]}</div>',
            unsafe_allow_html=True,
        )

        # Takeaway
        st.markdown(
            f'<div class="takeaway-box">💡 <strong>Compliance takeaway:</strong><br>{q["takeaway"]}</div>',
            unsafe_allow_html=True,
        )

        st.markdown("")
        next_label = "➡️ Ďalšia otázka" if q_idx + 1 < total else "🏁 Zobraziť výsledky"
        if st.button(next_label, use_container_width=True, type="primary"):
            st.session_state.q_idx += 1
            st.session_state.answered = False
            st.session_state.evaluation = None
            st.session_state.user_answer = ""
            if st.session_state.q_idx >= total:
                st.session_state.game_state = "results"
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# HRA — ABCD TEST (pôvodný formát, opravené max_tokens)
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.game_state == "playing" and st.session_state.test_type == "abcd":

    total = st.session_state.num_questions
    round_num = len(st.session_state.history)

    if round_num >= total:
        st.session_state.game_state = "results"
        st.rerun()

    c1, c2, c3 = st.columns([3, 2, 2])
    with c1: st.markdown(f"**{st.session_state.module}**")
    with c2: st.markdown(f"Scenár **{round_num + 1}** / {total}")
    with c3:
        correct_count = sum(1 for h in st.session_state.history if h.get("right"))
        st.markdown(f"✅ Skóre: **{correct_count}** / {round_num}")

    st.progress(round_num / total)
    st.divider()

    if st.session_state.current_scenario is None:
        diff = difficulty_label(round_num, total)
        with st.spinner(f"🤖 AI generuje scenár ({diff} obtiažnosť)..."):
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
                st.error(f"Chyba pri generovaní scenára: {e}")
                st.stop()

    sc = st.session_state.current_scenario

    st.markdown(
        f'<div class="scenario-box">📋 <strong>Situácia:</strong><br><br>{sc["scenario"]}</div>',
        unsafe_allow_html=True,
    )

    if not st.session_state.answered:
        st.markdown("**Čo urobíte?**")
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
                st.error(f"❌ **{key})** {text} ← vaša voľba")
            else:
                st.write(f"&nbsp;&nbsp;**{key})** {text}")

        st.markdown("---")
        consequence = sc["consequences"][chosen]
        box = "feedback-correct" if is_correct else "feedback-wrong"
        icon = "🎉 Správne!" if is_correct else "⚠️ Nesprávne."
        st.markdown(f'<div class="{box}"><strong>{icon}</strong><br>{consequence}</div>', unsafe_allow_html=True)

        if not is_correct:
            # konzekvencia správnej odpovede
            correct_consequence = sc["consequences"][sc["correct"]]
            st.markdown(
                f'<div class="consequence-box">⚡ <strong>Správny postup by znamenal:</strong><br>{correct_consequence}</div>',
                unsafe_allow_html=True,
            )

        st.markdown(
            f'<div class="correct-box">📖 <strong>Vysvetlenie:</strong><br>{sc["explanation"]}</div>',
            unsafe_allow_html=True,
        )

        st.markdown("")
        next_label = "➡️ Ďalší scenár" if round_num + 1 < total else "🏁 Výsledky"
        if st.button(next_label, use_container_width=True, type="primary"):
            st.session_state.current_scenario = None
            st.session_state.answered = False
            if len(st.session_state.history) >= total:
                st.session_state.game_state = "results"
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# VÝSLEDKY
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.game_state == "results":
    st.title("🏁 Výsledky testu")
    st.divider()

    history = st.session_state.history
    test_type = st.session_state.test_type

    if test_type == "onboarding":
        total_q = st.session_state.num_questions
        max_pts = total_q * 3
        earned = st.session_state.score
        pct = round(earned / max_pts * 100) if max_pts > 0 else 0
        passed = pct >= 60

        if passed:
            st.markdown(
                f'<div class="result-pass">✅ TEST ÚSPEŠNÝ — {pct} %<br>({earned} / {max_pts} bodov)</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div class="result-fail">❌ TEST NEÚSPEŠNÝ — {pct} %<br>({earned} / {max_pts} bodov) — Potrebných min. 60 %</div>',
                unsafe_allow_html=True,
            )

        # Badge
        if pct >= 80:
            badge, msg = "🥇 Compliance Expert", "Výborný výsledok! Pravidlá ovládaš na vysokej úrovni."
        elif pct >= 60:
            badge, msg = "🥈 Compliance Associate", "Dobrý základ. Odporúčame zopakovať oblasti kde boli chyby."
        else:
            badge, msg = "🥉 Compliance Rookie", "Treba zapracovať. Zopakuj si materiály a skús znova."

        st.markdown(f"### {badge}")
        st.info(msg)

        c1, c2, c3 = st.columns(3)
        c1.metric("Správne body", f"{earned} / {max_pts}")
        c2.metric("Úspešnosť", f"{pct} %")
        c3.metric("Výsledok", "✅ Úspešný" if passed else "❌ Neúspešný")

        st.divider()
        st.markdown("#### Prehľad otázok")
        for h in history:
            s = h["score"]
            icon = "✅" if s == 3 else ("⚠️" if s == 2 else "❌")
            with st.expander(f"{icon} Otázka {h['q_num']} — {h['topic']} ({s}/3 b.)"):
                st.markdown(f"**Scenár:** {h['scenario_short']}")
                st.markdown(f"**Vaša odpoveď:** {h['user_answer']}")
                st.markdown(f"**Hodnotenie:** {h['feedback']}")
                if s < 3:
                    st.markdown(
                        f'<div class="consequence-box">⚡ <strong>Dôsledok:</strong><br>{h["consequence"]}</div>',
                        unsafe_allow_html=True,
                    )
                st.markdown(
                    f'<div class="takeaway-box">💡 {h["takeaway"]}</div>',
                    unsafe_allow_html=True,
                )

    else:
        # ABCD výsledky
        correct = sum(1 for h in history if h.get("right"))
        total_q = len(history)
        pct = round(correct / total_q * 100) if total_q else 0
        passed = pct >= 60

        if passed:
            st.markdown(f'<div class="result-pass">✅ TEST ÚSPEŠNÝ — {pct} % ({correct}/{total_q})</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="result-fail">❌ TEST NEÚSPEŠNÝ — {pct} % ({correct}/{total_q})</div>', unsafe_allow_html=True)

        st.divider()
        st.markdown("#### Prehľad scenárov")
        for h in history:
            icon = "✅" if h["right"] else "❌"
            with st.expander(f"{icon} Scenár {h['round']}: {h['scenario_short']}"):
                if h["right"]:
                    st.success(f"Správne: **{h['correct']})** {h['correct_text']}")
                else:
                    st.error(f"Vaša voľba: **{h['chosen']})** {h['chosen_text']}")
                    st.success(f"Správna odpoveď: **{h['correct']})** {h['correct_text']}")

    st.divider()
    if st.button("🔄 Nový test", use_container_width=True, type="primary"):
        reset_game()
        st.rerun()

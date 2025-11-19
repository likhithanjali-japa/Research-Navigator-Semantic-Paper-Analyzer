# frontend/app.py
import streamlit as st
import requests
import pandas as pd
from urllib.parse import urlencode

# ------------------ CONFIG ------------------
st.set_page_config(page_title="AI PaperIQ — Research Insight Analyzer", layout="wide")
DEFAULT_BACKEND = "http://127.0.0.1:8000"

# safe secrets access
try:
    BACKEND = st.secrets.get("backend_url", DEFAULT_BACKEND)
except Exception:
    # fallback if st.secrets not configured or missing
    BACKEND = DEFAULT_BACKEND

# Dark theme palette
NAVY = "#0b1220"
ACCENT = "#6EE7B7"   # soft mint
CARD = "#0f1724"
MUTED = "#9CA3AF"
TEXT = "#0F74B3"
GLOW = "rgba(110,231,183,0.12)"

# ------------------ SESSION & QUERY PARAMS HANDLING ------------------
if "page" not in st.session_state:
    st.session_state.page = "home"
if "user" not in st.session_state:
    st.session_state.user = None
if "chosen_api" not in st.session_state:
    st.session_state.chosen_api = "arxiv"
if "uploaded_file" not in st.session_state:
    st.session_state.uploaded_file = None
if "papers_cache" not in st.session_state:
    st.session_state.papers_cache = None
if "show_profile" not in st.session_state:
    st.session_state.show_profile = False

# handle legacy query param "action=back" -> keep in-app navigation
qparams = st.query_params
if "action" in qparams:
    try:
        action = qparams.get("action", "")
        if isinstance(action, list):
            action = action[0] if action else ""
    except Exception:
        action = ""
    if action == "back":
        st.session_state.page = "dashboard"
        # clear query params (best-effort)
        try:
            st.experimental_set_query_params()
        except Exception:
            pass
        st.rerun()

# ------------------ HELPERS ------------------
def api_post(path, payload=None, files=None, timeout=120):
    """POST helper with increased default timeout (seconds)."""
    url = BACKEND.rstrip("/") + path
    try:
        if files:
            r = requests.post(url, files=files, data=payload, timeout=timeout)
        else:
            r = requests.post(url, json=payload, timeout=timeout)
        r.raise_for_status()
        try:
            return {"ok": True, "data": r.json()}
        except Exception:
            return {"ok": True, "data": None}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def api_get(path, params=None, timeout=60):
    """GET helper with sensible timeout (seconds)."""
    url = BACKEND.rstrip("/") + path
    try:
        r = requests.get(url, params=params, timeout=timeout)
        r.raise_for_status()
        try:
            return {"ok": True, "data": r.json()}
        except Exception:
            return {"ok": True, "data": None}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def extract_list(maybe):
    if maybe is None:
        return []
    if isinstance(maybe, list):
        return maybe
    if isinstance(maybe, dict):
        if "data" in maybe and isinstance(maybe["data"], list):
            return maybe["data"]
        if "results" in maybe and isinstance(maybe["results"], list):
            return maybe["results"]
    return []

def extract_data_obj(payload):
    if payload is None:
        return {}
    if isinstance(payload, dict):
        if "data" in payload and isinstance(payload["data"], dict):
            return payload["data"]
        return payload
    return {}

def show_error(e):
    st.error(f"⚠ {e}")

def top_keywords_from_text(text, topk=8):
    if not text:
        return []
    import re
    words = re.findall(r"\b[a-zA-Z]{3,}\b", text.lower())
    stop = set([
        "the","and","for","with","that","this","from","are","not","have","has","was",
        "were","also","using","use","used","a","an","in","on","of","to","is","by","as"
    ])
    f = {}
    for w in words:
        if w in stop:
            continue
        f[w] = f.get(w, 0) + 1
    items = sorted(f.items(), key=lambda x: x[1], reverse=True)[:topk]
    return [{"word": w, "count": c} for w, c in items]

# ------------------ CSS & STYLING (DARK THEME) ------------------
st.markdown(f"""
<style>
/* Body */
body {{
    background: linear-gradient(180deg, #071023 0%, #0b1320 100%);
    color: {TEXT};
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial;
}}

/* topbar */
.topbar {{
    background: linear-gradient(90deg, #071425, #081b2b);
    color: {TEXT};
    padding: 12px 18px;
    border-radius: 10px;
    margin-bottom: 14px;
    box-shadow: 0 10px 30px rgba(2,6,23,0.6);
    display:flex;
    align-items:center;
    justify-content:space-between;
}}

/* brand */
.brand-title {{
    font-size:18px;
    color: {TEXT};
    font-weight:700;
}}
.brand-sub {{
    font-size:12px;
    color: {MUTED};
}}

/* card */
.card {{
    background: {CARD};
    border-radius: 12px;
    padding: 14px;
    box-shadow: 0 8px 30px rgba(2,6,23,0.6);
    border: 1px solid rgba(255,255,255,0.03);
}}

/* button defaults */
div.stButton > button:first-child {{
    background: linear-gradient(180deg, #0f1724 0%, #08111a 100%);
    color: {TEXT};
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 13px;
    font-weight: 600;
    border: 1px solid rgba(255,255,255,0.03);
    box-shadow: 0 6px 18px rgba(2,6,23,0.6);
}}
div.stButton > button:first-child:hover {{
    background: linear-gradient(180deg, {ACCENT} 0%, #38b37a 100%);
    color: #041018;
}}

/* profile circle */
.profile-circle {{
    width:44px;
    height:44px;
    border-radius:50%;
    background: linear-gradient(180deg, rgba(255,255,255,0.03), rgba(255,255,255,0.01));
    border: 1px solid rgba(255,255,255,0.06);
    display:inline-flex;
    align-items:center;
    justify-content:center;
    font-weight:700;
    color: {ACCENT};
    cursor:pointer;
    box-shadow: 0 6px 20px {GLOW};
}}
.profile-circle:hover {{
    transform: translateY(-3px);
    box-shadow: 0 10px 30px rgba(110,231,183,0.18);
}}

/* dropdown */
.profile-dropdown {{
    background: #071826;
    border-radius: 10px;
    padding: 12px;
    box-shadow: 0 12px 36px rgba(2,6,23,0.75);
    border: 1px solid rgba(255,255,255,0.03);
    width: 260px;
}}
.profile-row {{
    font-size:13px;
    color: {TEXT};
    margin-bottom:6px;
}}
.small-muted {{
    font-size:12px;
    color: {MUTED};
    margin-bottom:6px;
}}

/* small buttons (home/logout inside dropdown) */
.small-action {{
    background: transparent;
    color: {ACCENT};
    border: 1px solid rgba(110,231,183,0.12);
    padding: 6px 10px;
    font-size:13px;
    border-radius:8px;
    width:110px;
    height:36px;
}}
.small-action:hover {{
    background: rgba(110,231,183,0.06);
    color: #001414;
}}

/* nav next/back */
.nav-next {{
    background: linear-gradient(90deg, rgba(110,231,183,0.08), rgba(110,231,183,0.02));
    color: {TEXT};
}}

/* subtle spacers */
.small-space {{ height:10px; }}
</style>
""", unsafe_allow_html=True)

# ------------------ TOPBAR (rendered as markup + controls) ------------------
user_display = st.session_state.user or {}
topbar_html = f"""
<div class="topbar">
  <div style="display:flex;align-items:center;gap:12px">
    <div style="font-size:20px">📘</div>
    <div>
      <div class="brand-title">AI PaperIQ — Research Insight Analyzer</div>
      <div class="brand-sub"></div>
    </div>
  </div>
  <div id="profile_render_area"></div>
</div>
"""
st.markdown(topbar_html, unsafe_allow_html=True)

# render profile circle (right side) using columns to position
cleft, cright = st.columns([9, 1])
with cright:
    # compute initial char
    if st.session_state.user and st.session_state.user.get("name"):
        initial = (st.session_state.user.get("name")[0] or "?").upper()
    else:
        initial = "?"
    # profile circle button (unique key)
    if st.button(initial, key="profile_circle_btn"):
        st.session_state.show_profile = not st.session_state.show_profile

# show dropdown when toggled
if st.session_state.show_profile:
    # use a container to hold dropdown just under topbar
    st.markdown('<div class="small-space"></div>', unsafe_allow_html=True)
    st.markdown('<div class="profile-dropdown">', unsafe_allow_html=True)
    if st.session_state.user:
        u = st.session_state.user
        st.markdown(f"<div class='profile-row'><b>{u.get('name','-')}</b></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='small-muted'>📧 {u.get('email','-')}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='small-muted'>🏫 {u.get('institution','-')}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='small-muted'>🔬 {u.get('research','-')}</div>", unsafe_allow_html=True)
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

        col_a, col_b = st.columns([1,1])
        with col_a:
            if st.button("Home", key="profile_home_btn"):
                st.session_state.page = "home"
                st.session_state.show_profile = False
                st.rerun()
        with col_b:
            if st.button("Logout", key="profile_logout_btn"):
                st.session_state.user = None
                st.session_state.page = "auth"
                st.session_state.show_profile = False
                st.rerun()
    else:
        # not logged-in quick actions
        if st.button("Sign In", key="profile_signin_btn"):
            st.session_state.page = "auth"
            st.session_state.show_profile = False
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# ------------------ NAV HELPERS ------------------
def nav_buttons(next_page=None):
    col_left, col_gap, col_right = st.columns([3, 1, 3])
    with col_left:
        if next_page:
            label = f"Next → {next_page.title()}"
            if st.button(label, key=f"next_{next_page}", use_container_width=False):
                st.session_state.page = next_page
                st.rerun()
    with col_right:
        if st.button("← Back to Dashboard", key="back_dashboard_btn", use_container_width=False):
            st.session_state.page = "dashboard"
            st.rerun()

# ------------------ PAGES ------------------

# HOME
if st.session_state.page == "home":
    st.markdown('<div class="card" style="max-width:1100px;margin:auto">', unsafe_allow_html=True)
    st.markdown("<h2 style='margin-bottom:6px;color: #0f1724;'>Welcome to <b>AI PaperIQ</b></h2>", unsafe_allow_html=True)
    st.markdown("<p style='margin-top:0.2rem;color: #0b1220;'>Ingest research papers, analyze with NER, explore insights, and visualize your academic impact — all in one place.</p>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    c1, c2, c3 = st.columns([1, 1, 1])
    with c2:
        if st.button("🚀 Get Started", key="btn_get_started_home"):
            st.session_state.page = "auth"
            st.rerun()

# AUTH (Login / Register)
elif st.session_state.page == "auth":
    st.markdown('<div class="card" style="max-width:1000px;margin:auto">', unsafe_allow_html=True)
    st.markdown("<h2 style='font-size:20px;margin-bottom:6px;color:#E6EEF3;'>Sign In or Create Account</h2>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    # Login form
    with col1:
        st.subheader("Sign In")
        with st.form("login_form"):
            email = st.text_input("Email", key="login_email")
            pwd = st.text_input("Password", type="password", key="login_pwd")
            submitted_login = st.form_submit_button("Sign In")
        if submitted_login:
            if not email or not pwd:
                show_error("Enter both fields.")
            else:
                res = api_post("/login", {"email": email, "password": pwd})
                if res["ok"] and res.get("data"):
                    st.success("Signed in successfully.")
                    st.session_state.user = extract_data_obj(res["data"])
                    st.session_state.page = "dashboard"
                    st.rerun()
                else:
                    show_error(res.get("error", "Invalid credentials or server issue."))

    # Register form
    with col2:
        st.subheader("Create Account")
        with st.form("register_form"):
            name = st.text_input("Full Name", key="reg_name")
            r_email = st.text_input("Email", key="reg_email")
            r_pwd = st.text_input("Password", type="password", key="reg_pwd")
            inst = st.text_input("Institution / University", key="reg_inst")
            research = st.text_input("Research Area", key="reg_research")
            submitted_register = st.form_submit_button("Create Account")
        if submitted_register:
            if not name or not r_email or not r_pwd:
                show_error("Name, email and password are required.")
            else:
                payload = {
                    "name": name,
                    "email": r_email,
                    "password": r_pwd,
                    "institution": inst,
                    "research": research,
                }
                r = api_post("/register", payload)
                if r["ok"]:
                    st.success("Account created — please sign in.")
                else:
                    show_error(r.get("error", "Registration failed."))

    st.markdown("</div>", unsafe_allow_html=True)

# DASHBOARD
elif st.session_state.page == "dashboard":
    user = st.session_state.get("user")
    if not user:
        st.warning("Session expired. Please sign in again.")
        st.session_state.page = "auth"
        st.rerun()

    # Dashboard action grid - 2x2 cards (clean)
    # First row
    c1, c2 = st.columns([1, 1])
    with c1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("<h4 style='margin:0;color:#0f1724'>Ingest Papers</h4>", unsafe_allow_html=True)
        st.markdown("<p style='color:#0f1724;margin-top:6px'>Upload or fetch papers from ArXiv / PubMed</p>", unsafe_allow_html=True)
        if st.button("Open Ingest", key="dash_open_ingest"):
            st.session_state.page = "ingest"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    with c2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("<h4 style='margin:0;color:#0f1724'>Analyze (NER)</h4>", unsafe_allow_html=True)
        st.markdown("<p style='color:#0f1724;margin-top:6px'>Extract entities and summaries from papers</p>", unsafe_allow_html=True)
        if st.button("Open Analyze", key="dash_open_analyze"):
            st.session_state.page = "analyze"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # Second row
    c3, c4 = st.columns([1, 1])
    with c3:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("<h4 style='margin:0;color:#0f1724'>Semantic & Recs</h4>", unsafe_allow_html=True)
        st.markdown("<p style='color:#0f1724;margin-top:6px'>Search semantically and get recommendations</p>", unsafe_allow_html=True)
        if st.button("Open Semantic", key="dash_open_semantic"):
            st.session_state.page = "semantic"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    with c4:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("<h4 style='margin:0;color:#0f1724'>Analytics</h4>", unsafe_allow_html=True)
        st.markdown("<p style='color:#0f1724;margin-top:6px'>View user & global analytics</p>", unsafe_allow_html=True)
        if st.button("Open Analytics", key="dash_open_analytics"):
            st.session_state.page = "analytics"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div style="height:18px"></div>', unsafe_allow_html=True)

# INGEST PAGE
elif st.session_state.page == "ingest":
    st.title("Paper Ingestion")
    st.write("Choose a source and ingest papers from ArXiv or PubMed.")
    colA, colB = st.columns([1, 1])
    with colA:
        if st.button("ArXiv", key="arxiv_btn_ingest"):
            st.session_state.chosen_api = "arxiv"
            st.rerun()
    with colB:
        if st.button("PubMed", key="pubmed_btn_ingest"):
            st.session_state.chosen_api = "pubmed"
            st.rerun()
    st.write(f"Selected source: *{st.session_state.chosen_api}*")
    keyword = st.text_input("Keyword to search", value="machine learning", key="ingest_keyword")
    num = st.number_input("How many papers to ingest", min_value=1, max_value=50, value=5, step=1, key="ingest_num")
    if st.button("Ingest Now", key="ingest_now_btn"):
        path = "/ingest/arxiv" if st.session_state.chosen_api == "arxiv" else "/ingest/pubmed"
        payload = {"keyword": keyword, "max_results": int(num), "email": (st.session_state.user or {}).get("email")}
        # ingestion can take longer, use a longer timeout
        with st.spinner("Ingesting..."):
            resp = api_post(path, payload, timeout=300)
        if resp["ok"]:
            st.success(f"Ingested: {resp.get('data')}")
            fetch = api_get("/papers", params={"email": (st.session_state.user or {}).get("email"), "limit": 200}, timeout=120)
            if fetch["ok"]:
                st.session_state.papers_cache = extract_list(fetch.get("data"))
        else:
            show_error(resp.get("error", "Ingestion failed."))

    st.markdown("---")
    st.markdown("### Upload a PDF (for local analysis)")
    uploaded = st.file_uploader("Upload PDF", type=["pdf"], key="upload_pdf_ingest")
    if uploaded:
        st.session_state.uploaded_file = uploaded
        st.success(f"Selected: {uploaded.name}")

    nav_buttons(next_page="analyze")

# ANALYZE (NER)
elif st.session_state.page == "analyze":
    st.title("NER & Preprocessing")
    st.write("Analyze ingested papers, uploaded PDFs, or paste text to extract entities, keywords and a short summary.")

    papers_resp = api_get("/papers", params={"email": (st.session_state.user or {}).get("email"), "limit":200})
    papers = st.session_state.papers_cache or (papers_resp.get("data") if (papers_resp.get("ok") and isinstance(papers_resp.get("data"), list)) else [])
    titles = ["-- Select an ingested paper --"] + [p.get("title","Untitled") for p in papers]
    selected_title = st.selectbox("Select an ingested paper to analyze", titles, key="analyze_selectbox")
    st.markdown("Or paste a snippet / abstract below:")
    text_input = st.text_area("Text to analyze", height=160, key="analyze_paste")

    # Uploaded PDF analysis
    if st.session_state.uploaded_file:
        st.info(f"Uploaded file ready: {st.session_state.uploaded_file.name}")
        if st.button("Analyze uploaded PDF", key="analyze_uploaded_btn"):
            file_obj = st.session_state.uploaded_file
            file_bytes = file_obj.read()
            files = {"file": (file_obj.name, file_bytes, "application/pdf")}
            with st.spinner("Uploading and analyzing..."):
                resp = api_post("/ner/upload", files=files, timeout=180)
            if resp["ok"]:
                data = extract_data_obj(resp.get("data"))
                st.success("Uploaded PDF analyzed.")
                clean = data.get("clean_text","")
                ents = data.get("entities") or []
                summary = data.get("summary", "")
                if not ents:
                    k = top_keywords_from_text(clean, topk=8)
                else:
                    k = [{"word": e.get("text"), "count": 1} for e in ents[:8]]
                st.markdown("#### Summary")
                st.write(summary or (clean[:500] + "..." if clean else "No summary available."))
                st.markdown("#### Important keywords / entities")
                for kw in k:
                    st.markdown(f"- {kw.get('word')} ({kw.get('count',0)})")
            else:
                show_error(resp.get("error", "Upload analysis failed."))

    # Analyze ingested paper
    if st.button("Analyze selected ingested paper", key="analyze_ingested_btn"):
        if selected_title == "-- Select an ingested paper --":
            show_error("Please select an ingested paper or upload/paste text.")
        else:
            chosen = next((p for p in papers if p.get("title")==selected_title), None)
            if not chosen:
                show_error("Selected paper not found (try refreshing).")
            else:
                payload_text = (chosen.get("title") or "") + " " + (chosen.get("summary") or chosen.get("abstract") or "")
                with st.spinner("Sending text to backend for NER..."):
                    resp = api_post("/ner/ingested", {"email": (st.session_state.user or {}).get("email"), "title": chosen.get("title")}, timeout=60)
                    if not resp["ok"]:
                        # fallback to direct processing
                        resp = api_post("/ner/process", {"text": payload_text, "email": (st.session_state.user or {}).get("email")}, timeout=60)
                if resp["ok"]:
                    data = extract_data_obj(resp.get("data"))
                    clean = data.get("clean_text","")
                    ents = data.get("entities") or []
                    summary = data.get("summary", "")
                    st.markdown("#### Short Summary")
                    st.write(summary or (clean[:500]+"..." if clean else "No summary available."))
                    st.markdown("#### Important items count")
                    st.write(f"Entities found: **{len(ents)}**")
                    if ents:
                        st.markdown("#### Top Entities")
                        for e in ents[:12]:
                            text = e.get("text") if isinstance(e, dict) else str(e)
                            lbl = e.get("label") or e.get("type") or ""
                            st.markdown(f"- {text} — {lbl}")
                    else:
                        st.markdown("#### Top Keywords (auto)")
                        kws = top_keywords_from_text(clean, topk=12)
                        for k in kws:
                            st.markdown(f"- {k['word']} ({k['count']})")
                else:
                    show_error(resp.get("error", "NER processing failed."))

    # Analyze pasted text
    if st.button("Analyze pasted text", key="analyze_pasted_btn"):
        if not text_input.strip():
            show_error("Paste some text first.")
        else:
            with st.spinner("Analyzing pasted text..."):
                resp = api_post("/ner/process", {"text": text_input, "email": (st.session_state.user or {}).get("email")}, timeout=60)
            if resp["ok"]:
                data = extract_data_obj(resp.get("data"))
                clean = data.get("clean_text","")
                ents = data.get("entities") or []
                summary = data.get("summary", "")
                st.markdown("#### Short Summary")
                st.write(summary or (clean[:400] + "..."))
                st.markdown("#### Important items count")
                st.write(f"Entities found: **{len(ents)}**")
                if ents:
                    st.markdown("#### Top Entities")
                    for e in ents[:12]:
                        text = e.get("text") if isinstance(e, dict) else str(e)
                        lbl = e.get("label") or e.get("type") or ""
                        st.markdown(f"- {text} — {lbl}")
                else:
                    st.markdown("#### Top Keywords (auto)")
                    kws = top_keywords_from_text(clean, topk=12)
                    for k in kws:
                        st.markdown(f"- {k['word']} ({k['count']})")
            else:
                show_error(resp.get("error", "NER processing failed."))

    nav_buttons(next_page="semantic")

# SEMANTIC SEARCH & RECOMMENDATIONS
elif st.session_state.page == "semantic":
    st.title("Semantic Search & Recommendations")
    st.write("Search your library in natural language and open individual papers.")

    q = st.text_input("Search query (natural language)", key="semantic_query")
    if st.button("Run Semantic Search", key="semantic_run_btn"):
        if not q.strip():
            show_error("Enter a search query.")
        else:
            with st.spinner("Searching..."):
                resp = api_post("/semantic/search", {"query": q, "email": (st.session_state.user or {}).get("email")}, timeout=90)
            if resp["ok"]:
                results = extract_list(resp.get("data")) or extract_list(resp.get("results"))
                if not results:
                    st.info("No results found.")
                else:
                    st.markdown(f"#### Top {min(len(results),20)} results")
                    for r in results[:20]:
                        pid = r.get("_id") or r.get("id") or r.get("paper_id")
                        title = r.get("title") or r.get("name") or "Untitled"
                        authors = r.get("authors") or r.get("authors_list") or ""
                        score = r.get("score") or r.get("sim") or 0
                        st.markdown(f"**{title}** — {authors} (score: {score:.3f})")
                        if pid:
                            url = BACKEND.rstrip("/") + f"/export/{pid}"
                            st.markdown(f"[Open paper]({url})", unsafe_allow_html=True)
            else:
                show_error(resp.get("error", "Semantic search failed."))

    # Recommendations
    rp = api_get("/papers", params={"email": (st.session_state.user or {}).get("email"), "limit": 200}, timeout=120)
    all_papers = rp.get("data") if (rp.get("ok") and isinstance(rp.get("data"), list)) else []
    sel = st.selectbox("Select a paper for recommendations", ["-- select --"] + [p.get("title","Untitled") for p in (all_papers or [])], key="rec_select")
    if sel != "-- select --":
        chosen = next((p for p in (all_papers or []) if p.get("title")==sel), None)
        if chosen and st.button("Get Recommendations", key="get_recs_btn"):
            pid = chosen.get("_id") or chosen.get("id") or chosen.get("paper_id")
            with st.spinner("Fetching recommendations..."):
                rec = api_get("/semantic/recommendations", params={"paper_id": pid, "limit": 6}, timeout=60)
            if rec.get("ok"):
                items = extract_list(rec.get("data")) or extract_list(rec.get("results"))
                if items:
                    for it in items:
                        st.markdown(f"- {it.get('title','Untitled')} — {it.get('authors','')} (score: {it.get('score',0):.3f})")
                        if it.get("_id"):
                            st.markdown(f"[Open paper]({BACKEND.rstrip('/')}/export/{it.get('_id')})")
                else:
                    st.info("No recommendations found.")
            else:
                show_error(rec.get("error", "Recommendation failed."))

    nav_buttons(next_page="analytics")

# ANALYTICS
elif st.session_state.page == "analytics":
    st.title("Analytics Dashboard")

    u = api_get("/analytics/user", params={"email": (st.session_state.user or {}).get("email")})
    if u.get("ok") and isinstance(u.get("data"), dict):
        d = u.get("data")
        st.markdown("#### Your Activity")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Searches", d.get("total_searches", 0))
            st.metric("Total Papers", d.get("total_papers", 0))
        with col2:
            top_q = d.get("top_queries") or []
            if isinstance(top_q, list) and top_q:
                try:
                    dfq = pd.DataFrame(top_q)
                    if "query" in dfq.columns and "count" in dfq.columns:
                        st.bar_chart(dfq.set_index("query"))
                    else:
                        if isinstance(top_q[0], list) and len(top_q[0]) == 2:
                            df2 = pd.DataFrame(top_q, columns=["query", "count"])
                            st.bar_chart(df2.set_index("query"))
                        else:
                            st.write(top_q)
                except Exception:
                    st.write(top_q)
            else:
                st.info("No per-user query data yet.")
    else:
        st.info("User analytics unavailable.")

    st.markdown("---")

    g = api_get("/analytics/global")
    if g.get("ok") and isinstance(g.get("data"), dict):
        gd = g.get("data")
        st.markdown("#### Global Metrics")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Users", gd.get("total_users", 0))
        with col2:
            st.metric("Total Papers", gd.get("total_papers", 0))
        with col3:
            st.metric("Total Searches", gd.get("total_searches", 0))

        top_topics = gd.get("top_topics") or []
        if top_topics:
            try:
                dft = pd.DataFrame(top_topics)
                if "topic" in dft.columns and "count" in dft.columns:
                    st.bar_chart(dft.set_index("topic"))
                else:
                    if isinstance(top_topics[0], list) and len(top_topics[0]) == 2:
                        df2 = pd.DataFrame(top_topics, columns=["topic", "count"])
                        st.bar_chart(df2.set_index("topic"))
                    else:
                        st.write(top_topics)
            except Exception:
                st.write(top_topics)
    else:
        st.info("Global analytics unavailable.")

    st.markdown("---")
    nav_buttons(next_page=None)

# End of file

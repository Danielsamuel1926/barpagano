import streamlit as st
import pandas as pd
import os
import time
from datetime import datetime
import streamlit.components.v1 as components
from streamlit_autorefresh import st_autorefresh

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="BAR PAGANO", page_icon="☕", layout="wide")

# --- CSS PERSONALIZZATO (Stile, Colori e Forme) ---
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #FFFFFF; }
    
    /* Forza i bottoni dei tavoli a essere quadrati e grandi */
    div[data-testid="column"] button {
        width: 100% !important;
        aspect-ratio: 1 / 1 !important;
        font-weight: bold !important;
        font-size: 22px !important;
        border-radius: 12px !important;
        margin-bottom: 10px !important;
        color: white !important;
    }

    /* TAVOLO LIBERO (Verde Pagano) */
    div[data-testid="column"] button[kind="secondary"] {
        background-color: #2E7D32 !important; 
        border: 2px solid #4CAF50 !important;
    }

    /* TAVOLO OCCUPATO (Rosso Notifica) */
    div[data-testid="column"] button[kind="primary"] {
        background-color: #D32F2F !important;
        border: 2px solid #FF5252 !important;
    }

    .servito { color: #555555 !important; text-decoration: line-through; opacity: 0.6; font-style: italic; }
    .da-servire { color: #FFFFFF !important; font-weight: bold; font-size: 18px; }
    
    .selected-tavolo { 
        background-color: #D32F2F; color: white; padding: 15px; 
        border-radius: 15px; text-align: center; font-size: 24px; 
        font-weight: bold; margin-bottom: 15px; 
    }
    </style>
    """, unsafe_allow_html=True)

# --- FUNZIONI DI SERVIZIO ---
def suona_notifica():
    audio_html = '<audio autoplay style="display:none;"><source src="https://raw.githubusercontent.com/rafaelreis-hotmart/Audio-Files/main/notification.mp3" type="audio/mp3"></audio>'
    components.html(audio_html, height=0)

def mostra_logo():
    if os.path.exists("logo.png"):
        st.image("logo.png", use_container_width=True)
    else:
        st.title("☕ BAR PAGANO")

# --- GESTIONE DATABASE (CSV) ---
DB_FILE = "ordini_bar_pagano.csv"
STOCK_FILE = "stock_bar_pagano.csv"
MENU_FILE = "menu_personalizzato.csv"
COLONNE_ORDINI = ["id_univoco", "tavolo", "prodotto", "prezzo", "stato", "orario"]

def inizializza_file(file, colonne):
    if not os.path.exists(file) or os.stat(file).st_size <= 2:
        pd.DataFrame(columns=colonne).to_csv(file, index=False)

inizializza_file(DB_FILE, COLONNE_ORDINI)
inizializza_file(MENU_FILE, ["categoria", "prodotto", "prezzo"])
inizializza_file(STOCK_FILE, ["prodotto", "quantita"])

def carica_menu(): return pd.read_csv(MENU_FILE)
def carica_ordini(): 
    try: return pd.read_csv(DB_FILE).to_dict('records')
    except: return []
def salva_ordini(lista): pd.DataFrame(lista if lista else [], columns=COLONNE_ORDINI).to_csv(DB_FILE, index=False)
def carica_stock(): 
    df = pd.read_csv(STOCK_FILE)
    return df.set_index('prodotto')['quantita'].to_dict() if not df.empty else {}
def salva_stock(d): pd.DataFrame(list(d.items()), columns=['prodotto', 'quantita']).to_csv(STOCK_FILE, index=False)

# --- LOGICA DI NAVIGAZIONE ---
ruolo = st.query_params.get("ruolo", "tavolo")
menu_df = carica_menu()

# ---------------------------------------------------------
# INTERFACCIA BANCONE
# ---------------------------------------------------------
if ruolo == "banco":
    st_autorefresh(interval=5000, key="banco_refresh")
    
    col_header1, col_header2 = st.columns([0.5, 5])
    with col_header1:
        mostra_logo()
    with col_header2:
        st.markdown("<h2 style='margin-top: 18px;'>CONSOLE BANCONE</h2>", unsafe_allow_html=True)
    
    ordini_attuali = carica_ordini()
    if "ultimo_count" not in st.session_state: st.session_state.ultimo_count = len(ordini_attuali)
    if len(ordini_attuali) > st.session_state.ultimo_count:
        suona_notifica()
        st.session_state.ultimo_count = len(ordini_attuali)
    st.session_state.ultimo_count = len(ordini_attuali)

    tab1, tab2, tab3, tab4 = st.tabs(["📋 ORDINI", "⚡ VENDITA RAPIDA", "📦 STOCK", "⚙️ GESTIONE LISTINO"])
    
    with tab1: # ORDINI DA SERVIRE
        if not ordini_attuali: st.info("In attesa di ordini...")
        else:
            tavoli_attivi = sorted(list(set(str(o['tavolo']) for o in ordini_attuali)))
            cols_ordini = st.columns(3)
            for idx, t in enumerate(tavoli_attivi):
                with cols_ordini[idx % 3]:
                    with st.container(border=True):
                        st.subheader(f"🪑 Tavolo {t}")
                        items = [o for o in ordini_attuali if str(o['tavolo']) == str(t)]
                        tot = 0.0
                        for r in items:
                            c1, c2, c3 = st.columns([0.6, 3, 1])
                            if c1.button("❌", key=f"del_{r['id_univoco']}"):
                                salva_ordini([o for o in ordini_attuali if o['id_univoco'] != r['id_univoco']]); st.rerun()
                            cl = "servito" if r['stato'] == "SI" else "da-servire"
                            c2.markdown(f"<span class='{cl}'>[{r.get('orario','')}] {r['prodotto']}</span>", unsafe_allow_html=True)
                            tot += float(r['prezzo'])
                            if r['stato'] == "NO" and c3.button("Ok", key=f"ok_{r['id_univoco']}"):
                                for o in ordini_attuali: 
                                    if o['id_univoco'] == r['id_univoco']: o['stato'] = "SI"
                                salva_ordini(ordini_attuali); st.rerun()
                        if st.button(f"PAGATO €{tot:.2f}", key=f"pay_{t}", type="primary", use_container_width=True, disabled=not all(o['stato']=="SI" for o in items)):
                            salva_ordini([o for o in ordini_attuali if str(o['tavolo']) != str(t)]); st.rerun()

    with tab2: # VENDITA RAPIDA
        stk = carica_stock()
        st.write("### ⚡ Vendita al banco")
        cv = st.columns(4)
        for i, (p, q) in enumerate(stk.items()):
            if cv[i % 4].button(f"{p}\n({q})", key=f"vr_{p}", disabled=(q <= 0)):
                stk[p] = max(0, q - 1); salva_stock(stk); st.rerun()

    with tab3: # STOCK
        st.write("### 📦 Stock")
        stk = carica_stock()
        if not menu_df.empty:
            c1, c2 = st.columns(2)
            cat_stk = c1.selectbox("Filtra Categoria", sorted(menu_df['categoria'].unique()))
            prod_filtrati = menu_df[menu_df['categoria'] == cat_stk]['prodotto'].unique()
            nuovo_s = c2.selectbox("Prodotto da monitorare", prod_filtrati)
            if st.button("AGGIUNGI ALLO STOCK ✅", use_container_width=True):
                if nuovo_s not in stk: stk[nuovo_s] = 0; salva_stock(stk); st.rerun()
        st.divider()
        for p, q in stk.items():
            cx, cm, cq, cp, cd = st.columns([3, 1, 1, 1, 1])
            cx.write(f"**{p}**")
            if cm.button("➖", key=f"sm_{p}"): stk[p] = max(0, q-1); salva_stock(stk); st.rerun()
            cq.write(f"**{q}**")
            if cp.button("➕", key=f"sp_{p}"): stk[p] = q+1; salva_stock(stk); st.rerun()
            if cd.button("🗑️", key=f"sdel_{p}"): del stk[p]; salva_stock(stk); st.rerun()

    with tab4: # LISTINO
        st.subheader("⚙️ Modifica Listino")
        with st.form("add_new"):
            c1, c2 = st.columns(2)
            cat_e = c1.selectbox("Categoria", ["---"] + sorted(list(menu_df['categoria'].unique())) if not menu_df.empty else ["---"])
            cat_n = c2.text_input("O nuova categoria")
            nome_n = st.text_input("Prodotto")
            prez_n = st.number_input("Prezzo €", min_value=0.0, step=0.1)
            if st.form_submit_button("AGGIUNGI"):
                cat_f = cat_n if cat_n.strip() != "" else cat_e
                if cat_f != "---" and nome_n:
                    nuovo = pd.DataFrame([{"categoria": cat_f, "prodotto": nome_n, "prezzo": prez_n}])
                    pd.concat([menu_df, nuovo], ignore_index=True).to_csv(MENU_FILE, index=False); st.rerun()
        st.divider()
        for cat in sorted(menu_df['categoria'].unique()):
            with st.expander(f"📂 {cat.upper()}"):
                for i, r in menu_df[menu_df['categoria'] == cat].iterrows():
                    with st.form(key=f"edit_{i}"):
                        cn, cp, cs, cd = st.columns([3, 1.5, 1, 1])
                        nn = cn.text_input("Nome", r['prodotto'], label_visibility="collapsed")
                        np = cp.number_input("€", value=float(r['prezzo']), step=0.1, label_visibility="collapsed")
                        if cs.form_submit_button("💾"):
                            menu_df.at[i, 'prodotto'], menu_df.at[i, 'prezzo'] = nn, np
                            menu_df.to_csv(MENU_FILE, index=False); st.rerun()
                        if cd.form_submit_button("🗑️"):
                            menu_df.drop(i).to_csv(MENU_FILE, index=False); st.rerun()

# ---------------------------------------------------------
# INTERFACCIA CLIENTE
# ---------------------------------------------------------
else:
    c_logo1, c_logo2, c_logo3 = st.columns([1, 2, 1])
    with c_logo2:
        mostra_logo()

    if 'tavolo' not in st.session_state: st.session_state.tavolo = None
    if 'carrello' not in st.session_state: st.session_state.carrello = []
    
    if st.session_state.tavolo is None:
        st.write("### 🪑 Seleziona il tuo tavolo:")
        
        # LOGICA COLORI TAVOLI
        ordini_attivi = carica_ordini()
        tavoli_occupati = [str(o['tavolo']) for o in ordini_attivi]
        
        # Griglia 5 colonne x 3 righe = 15 Tavoli
        numero_tavoli = 15
        colonne_per_fila = 5
        
        for i in range(0, numero_tavoli, colonne_per_fila):
            cols = st.columns(colonne_per_fila)
            for j in range(colonne_per_fila):
                n_t = i + j + 1
                if n_t <= numero_tavoli:
                    t_str = str(n_t)
                    # SE OCCUPATO: Rosso (primary), SE LIBERO: Verde (secondary)
                    tipo_bottone = "primary" if t_str in tavoli_occupati else "secondary"
                    if cols[j].button(f"{n_t}", key=f"btn_t_{n_t}", type=tipo_bottone, use_container_width=True):
                        st.session_state.tavolo = t_str
                        st.rerun()
    else:
        st.markdown(f"<div class='selected-tavolo'>TAVOLO {st.session_state.tavolo}</div>", unsafe_allow_html=True)
        if st.button("⬅️ CAMBIA TAVOLO", use_container_width=True): 
            st.session_state.tavolo = None; st.rerun()
        
        stk = carica_stock()
        if not menu_df.empty:
            cat_scelta = st.radio("Scegli Categoria:", sorted(menu_df['categoria'].unique()), horizontal=True)
            for i, r in menu_df[menu_df['categoria'] == cat_scelta].iterrows():
                q = stk.get(r['prodotto'], None)
                label = f"➕ {r['prodotto']} | €{r['prezzo']:.2f}" + (f" (Disp: {q})" if q is not None else "")
                if st.button(label, key=f"prod_{i}", use_container_width=True, disabled=(q is not None and q <= 0)):
                    st.session_state.carrello.append({"prodotto": r['prodotto'], "prezzo": r['prezzo']})
                    st.toast(f"Aggiunto: {r['prodotto']}")

        if st.session_state.carrello:
            st.divider(); st.write("### 🛒 Il tuo Carrello:")
            for idx, c in enumerate(st.session_state.carrello):
                col1, col2 = st.columns([4, 1])
                col1.write(f"**{c['prodotto']}** - €{c['prezzo']:.2f}")
                if col2.button("🗑️", key=f"rc_{idx}"): st.session_state.carrello.pop(idx); st.rerun()
            
            if st.button(f"🚀 INVIA ORDINE (€{sum(x['prezzo'] for x in st.session_state.carrello):.2f})", type="primary", use_container_width=True):
                ords = carica_ordini()
                ora = datetime.now().strftime("%H:%M")
                for c in st.session_state.carrello:
                    if c['prodotto'] in stk: 
                        stk[c['prodotto']] = max(0, stk[c['prodotto']] - 1)
                        salva_stock(stk)
                    ords.append({"id_univoco": f"{time.time()}_{c['prodotto']}", "tavolo": st.session_state.tavolo, "prodotto": c['prodotto'], "prezzo": c['prezzo'], "stato": "NO", "orario": ora})
                salva_ordini(ords); st.session_state.carrello = []; st.success("Ordine inviato con successo!"); time.sleep(1); st.rerun()

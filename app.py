import streamlit as st
import pandas as pd
import os
import time
from datetime import datetime
import streamlit.components.v1 as components
from streamlit_autorefresh import st_autorefresh

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="BAR PAGANO", page_icon="☕", layout="wide")

# --- CSS DEFINITIVO PER COLORI E FORME ---
st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #FFFFFF; }
    
    /* Forza i bottoni dei tavoli a essere quadrati */
    div[data-testid="column"] button {
        width: 100% !important;
        aspect-ratio: 1 / 1 !important;
        font-weight: bold !important;
        font-size: 24px !important;
        border-radius: 12px !important;
        color: white !important;
    }

    /* TAVOLO LIBERO: VERDE ACCESO */
    div[data-testid="column"] button[kind="secondary"] {
        background-color: #28a745 !important; 
        border: 2px solid #34ce57 !important;
    }

    /* TAVOLO OCCUPATO: ROSSO */
    div[data-testid="column"] button[kind="primary"] {
        background-color: #dc3545 !important;
        border: 2px solid #ff4b5c !important;
    }

    .servito { color: #555555 !important; text-decoration: line-through; opacity: 0.6; font-style: italic; }
    .selected-tavolo { background-color: #dc3545; color: white; padding: 15px; border-radius: 15px; text-align: center; font-size: 24px; font-weight: bold; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNZIONI DATI ---
DB_FILE = "ordini_bar_pagano.csv"
STOCK_FILE = "stock_bar_pagano.csv"
MENU_FILE = "menu_personalizzato.csv"

def inizializza_file(file, colonne):
    if not os.path.exists(file) or os.stat(file).st_size <= 2:
        pd.DataFrame(columns=colonne).to_csv(file, index=False)

inizializza_file(DB_FILE, ["id_univoco", "tavolo", "prodotto", "prezzo", "stato", "orario"])
inizializza_file(MENU_FILE, ["categoria", "prodotto", "prezzo"])
inizializza_file(STOCK_FILE, ["prodotto", "quantita"])

def carica_menu(): return pd.read_csv(MENU_FILE)
def carica_ordini(): 
    try: return pd.read_csv(DB_FILE).to_dict('records')
    except: return []
def salva_ordini(lista): pd.DataFrame(lista).to_csv(DB_FILE, index=False)
def carica_stock(): 
    df = pd.read_csv(STOCK_FILE)
    return df.set_index('prodotto')['quantita'].to_dict() if not df.empty else {}
def salva_stock(d): pd.DataFrame(list(d.items()), columns=['prodotto', 'quantita']).to_csv(STOCK_FILE, index=False)

# --- NAVIGAZIONE ---
ruolo = st.query_params.get("ruolo", "tavolo")
menu_df = carica_menu()

# --- INTERFACCIA BANCONE ---
if ruolo == "banco":
    st_autorefresh(interval=5000, key="banco_refresh")
    col_l, col_t = st.columns([0.5, 5])
    with col_l:
        if os.path.exists("logo.png"): st.image("logo.png", use_container_width=True)
    with col_t:
        st.markdown("<h2 style='margin-top: 15px;'>CONSOLE BANCONE</h2>", unsafe_allow_html=True)
    
    ordini_attuali = carica_ordini()
    tab1, tab2, tab3, tab4 = st.tabs(["📋 ORDINI", "⚡ VENDITA", "📦 STOCK", "⚙️ LISTINO"])
    
    with tab1:
        if not ordini_attuali: st.info("In attesa di ordini...")
        else:
            tavoli_attivi = sorted(list(set(str(o['tavolo']) for o in ordini_attuali)))
            cols = st.columns(3)
            for idx, t in enumerate(tavoli_attivi):
                with cols[idx % 3]:
                    with st.container(border=True):
                        st.subheader(f"Tavolo {t}")
                        items = [o for o in ordini_attuali if str(o['tavolo']) == str(t)]
                        tot = 0.0
                        for r in items:
                            c1, c2, c3 = st.columns([0.6, 3, 1])
                            if c1.button("❌", key=f"del_{r['id_univoco']}"):
                                salva_ordini([o for o in ordini_attuali if o['id_univoco'] != r['id_univoco']]); st.rerun()
                            txt_cl = "servito" if r['stato'] == "SI" else ""
                            c2.markdown(f"<span class='{txt_cl}'>{r['prodotto']}</span>", unsafe_allow_html=True)
                            tot += float(r['prezzo'])
                            if r['stato'] == "NO" and c3.button("OK", key=f"ok_{r['id_univoco']}"):
                                for o in ordini_attuali: 
                                    if o['id_univoco'] == r['id_univoco']: o['stato'] = "SI"
                                salva_ordini(ordini_attuali); st.rerun()
                        if st.button(f"PAGA €{tot:.2f}", key=f"p_{t}", type="primary", use_container_width=True):
                            salva_ordini([o for o in ordini_attuali if str(o['tavolo']) != str(t)]); st.rerun()

    with tab4: # GESTIONE LISTINO
        with st.form("add_list"):
            c1, c2, c3 = st.columns(3)
            cat = c1.text_input("Categoria")
            prod = c2.text_input("Prodotto")
            prez = c3.number_input("Prezzo", step=0.1)
            if st.form_submit_button("AGGIUNGI"):
                if cat and prod:
                    nuovo = pd.DataFrame([{"categoria": cat, "prodotto": prod, "prezzo": prez}])
                    pd.concat([menu_df, nuovo]).to_csv(MENU_FILE, index=False); st.rerun()
        st.divider()
        for i, r in menu_df.iterrows():
            c1, c2, c3 = st.columns([3, 1, 1])
            c1.write(f"**{r['categoria']}**: {r['prodotto']}")
            c2.write(f"€{r['prezzo']:.2f}")
            if c3.button("🗑️", key=f"rm_{i}"):
                menu_df.drop(i).to_csv(MENU_FILE, index=False); st.rerun()

# --- INTERFACCIA CLIENTE ---
else:
    c_logo1, c_logo2, c_logo3 = st.columns([1, 2, 1])
    with c_logo2:
        if os.path.exists("logo.png"): st.image("logo.png", use_container_width=True)
        else: st.title("BAR PAGANO")

    if 'tavolo' not in st.session_state: st.session_state.tavolo = None
    if 'carrello' not in st.session_state: st.session_state.carrello = []
    
    if st.session_state.tavolo is None:
        st.write("### 🪑 Seleziona il tuo tavolo:")
        ordini_attuali = carica_ordini()
        occupati = [str(o['tavolo']) for o in ordini_attuali]
        
        # Griglia 5 colonne x 3 righe = 15 Tavoli
        for i in range(0, 15, 5):
            cols = st.columns(5)
            for j in range(5):
                n = i + j + 1
                if n <= 15:
                    t_str = str(n)
                    # SE OCCUPATO: Rosso (primary), SE LIBERO: Verde (secondary)
                    stile = "primary" if t_str in occupati else "secondary"
                    if cols[j].button(f"{n}", key=f"bt_{n}", type=stile):
                        st.session_state.tavolo = t_str
                        st.rerun()
    else:
        st.markdown(f"<div class='selected-tavolo'>TAVOLO {st.session_state.tavolo}</div>", unsafe_allow_html=True)
        if st.button("⬅️ CAMBIA TAVOLO"): st.session_state.tavolo = None; st.rerun()
        
        if not menu_df.empty:
            cat_scelta = st.radio("Menu:", sorted(menu_df['categoria'].unique()), horizontal=True)
            for i, r in menu_df[menu_df['categoria'] == cat_scelta].iterrows():
                if st.button(f"➕ {r['prodotto']} | €{r['prezzo']:.2f}", key=f"p_{i}", use_container_width=True):
                    st.session_state.carrello.append(r.to_dict())
                    st.toast(f"Aggiunto {r['prodotto']}")

        if st.session_state.carrello:
            st.divider(); st.write("### 🛒 Carrello")
            for idx, c in enumerate(st.session_state.carrello):
                col1, col2 = st.columns([4, 1])
                col1.write(f"{c['prodotto']} - €{c['prezzo']:.2f}")
                if col2.button("❌", key=f"rc_{idx}"): st.session_state.carrello.pop(idx); st.rerun()
            
            if st.button(f"🚀 INVIA ORDINE (€{sum(x['prezzo'] for x in st.session_state.carrello):.2f})", type="primary", use_container_width=True):
                ords = carica_ordini()
                ora = datetime.now().strftime("%H:%M")
                for c in st.session_state.carrello:
                    ords.append({"id_univoco": time.time()+idx, "tavolo": st.session_state.tavolo, "prodotto": c['prodotto'], "prezzo": c['prezzo'], "stato": "NO", "orario": ora})
                salva_ordini(ords); st.session_state.carrello = []; st.success("Ordine inviato!"); time.sleep(1); st.rerun()

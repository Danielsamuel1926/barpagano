import streamlit as st
import pandas as pd
import os
import time
from datetime import datetime

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="BAR PAGANO", page_icon="☕", layout="wide")

# CSS per testi grandi, pulsanti e stile
st.markdown("""
    <style>
    .product-text { font-size: 24px !important; font-weight: bold; }
    .note-text { font-size: 18px !important; font-style: italic; opacity: 0.8; }
    .stButton>button { height: 3.5em; font-size: 18px !important; border-radius: 10px; }
    .categoria-header { background-color: #f0f2f6; padding: 10px; border-radius: 10px; text-align: center; margin-bottom: 15px; }
    </style>
    """, unsafe_allow_html=True)

DB_FILE = "ordini_bar_pagano.csv"

# --- NUOVO LISTINO DIVISO PER CATEGORIE ---
MENU = {
    "Brioche e Cornetti": {
        "Cornetto cioccolato": 1.50, "Cornetto crema": 1.50, "Cornetto miele": 1.50,
        "Treccia noci": 1.80, "Polacca": 2.00, "Graffa": 1.20,
        "Monachina": 1.80, "Pandistelle": 1.00, "Flauto": 1.00
    },
    "Bevande Calde": {
        "Caffè": 1.00, "Caffè Macchiato": 1.10, "Cappuccino": 1.50, 
        "Latte Macchiato": 2.00, "Tè caldo": 1.50, "Cioccolata": 2.50
    },
    "Bevande Fredde": {
        "Acqua 0.5L": 1.00, "Coca Cola": 2.50, "Aranciata": 2.50, 
        "The Limone/Pesca": 2.50, "Succo Frutta": 2.00, "Birra": 3.00
    }
}

# --- STATO DELLA SESSIONE ---
if 'tavolo_scelto' not in st.session_state: st.session_state.tavolo_scelto = None
if 'categoria_scelta' not in st.session_state: st.session_state.categoria_scelta = "Brioche e Cornetti"
if 'prodotto_scelto' not in st.session_state: st.session_state.prodotto_scelto = None

# --- FUNZIONI DATABASE ---
def carica_ordini():
    if not os.path.exists(DB_FILE): return []
    try:
        df = pd.read_csv(DB_FILE)
        return [] if df.empty else df.to_dict('records')
    except: return []

def salva_ordini(lista_ordini):
    df = pd.DataFrame(lista_ordini) if lista_ordini else pd.DataFrame(columns=["tavolo", "prodotto", "prezzo", "nota", "orario"])
    df.to_csv(DB_FILE, index=False)

query_params = st.query_params
ruolo = query_params.get("ruolo", "tavolo")

# --- 1. INTERFACCIA BANCONE ---
if ruolo == "banco":
    st.title("🖥️ DASHBOARD BANCONE - BAR PAGANO")
    ordini_attivi = carica_ordini()
    if not ordini_attivi:
        st.info("In attesa di ordini...")
    else:
        df = pd.DataFrame(ordini_attivi)
        df['tavolo'] = df['tavolo'].astype(str)
        tavoli = sorted(df['tavolo'].unique(), key=lambda x: int(x) if x.isdigit() else 0)
        cols = st.columns(4)
        for idx, t in enumerate(tavoli):
            with cols[idx % 4]:
                with st.container(border=True):
                    prod_t = df[df['tavolo'] == t]
                    st.markdown(f"<div class='categoria-header'><h3>🪑 Tavolo {t}</h3></div>", unsafe_allow_html=True)
                    for _, row in prod_t.iterrows():
                        st.markdown(f"<p class='product-text'>• {row['prodotto']}</p>", unsafe_allow_html=True)
                        if str(row['nota']) != 'nan' and row['nota']:
                            st.markdown(f"<p class='note-text'>&nbsp;&nbsp;({row['nota']})</p>", unsafe_allow_html=True)
                    st.divider()
                    st.markdown(f"**Totale: € {prod_t['prezzo'].sum():.2f}**")
                    if st.button(f"CHIUDI CONTO T{t}", key=f"p_{t}", type="primary", use_container_width=True):
                        nuova = [o for o in ordini_attivi if str(o['tavolo']) != t]
                        salva_ordini(nuova)
                        st.rerun()
    time.sleep(15)
    st.rerun()

# --- 2. INTERFACCIA CLIENTE ---
else:
    st.title("☕ BENVENUTO AL BAR PAGANO")
    
    # SELEZIONE TAVOLO
    st.write("### 1. Seleziona il tuo Tavolo:")
    t_cols = st.columns(5)
    for i in range(1, 21):
        t_str = str(i)
        with t_cols[(i-1) % 5]:
            tipo_t = "primary" if st.session_state.tavolo_scelto == t_str else "secondary"
            if st.button(f"T{i}", key=f"t_{i}", use_container_width=True, type=tipo_t):
                st.session_state.tavolo_scelto = t_str
                st.rerun()

    if st.session_state.tavolo_scelto:
        st.divider()
        st.write(f"### 2. Scegli Categoria per il **Tavolo {st.session_state.tavolo_scelto}**:")
        
        # TASTI CATEGORIA
        cat_cols = st.columns(3)
        categorie = list(MENU.keys())
        for i, cat in enumerate(categorie):
            with cat_cols[i]:
                tipo_c = "primary" if st.session_state.categoria_scelta == cat else "secondary"
                if st.button(cat, key=f"cat_{i}", use_container_width=True, type=tipo_c):
                    st.session_state.categoria_scelta = cat
                    st.session_state.prodotto_scelto = None # Reset prodotto se cambio categoria
                    st.rerun()

        # TASTI PRODOTTI DELLA CATEGORIA SCELTA
        st.write(f"#### Prodotti: {st.session_state.categoria_scelta}")
        prod_list = MENU[st.session_state.categoria_scelta]
        p_cols = st.columns(2)
        for idx, (nome, prezzo) in enumerate(prod_list.items()):
            with p_cols[idx % 2]:
                tipo_p = "primary" if st.session_state.prodotto_scelto == nome else "secondary"
                if st.button(f"{nome}\n€{prezzo:.2f}", key=f"pr_{idx}", use_container_width=True, type=tipo_p):
                    st.session_state.prodotto_scelto = nome
                    st.rerun()

    # INVIO ORDINE
    if st.session_state.prodotto_scelto:
        st.divider()
        prezzo_f = MENU[st.session_state.categoria_scelta][st.session_state.prodotto_scelto]
        st.write(f"Selezionato: **{st.session_state.prodotto_scelto}** (€{prezzo_f:.2f})")
        nota = st.text_input("Note (es. macchiato caldo, senza zucchero)")
        
        if st.button("🚀 INVIA ORDINE AL BANCONE", use_container_width=True, type="primary"):
            nuovo = {
                "tavolo": st.session_state.tavolo_scelto,
                "prodotto": st.session_state.prodotto_scelto,
                "prezzo": prezzo_f,
                "nota": nota,
                "orario": datetime.now().strftime("%H:%M")
            }
            correnti = carica_ordini()
            correnti.append(nuovo)
            salva_ordini(correnti)
            st.success("Ordine inviato!")
            st.balloons()
            st.session_state.prodotto_scelto = None
            time.sleep(2)
            st.rerun()

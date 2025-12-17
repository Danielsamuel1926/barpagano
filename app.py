import streamlit as st
import pandas as pd
import os
import time
from datetime import datetime

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="BAR PAGANO", page_icon="☕", layout="wide")

# CSS per testi grandi e pulsanti
st.markdown("""
    <style>
    .product-text { font-size: 24px !important; font-weight: bold; }
    .note-text { font-size: 18px !important; font-style: italic; opacity: 0.8; }
    .stButton>button { height: 3.5em; font-size: 18px !important; border-radius: 10px; }
    .cart-item { background-color: #262730; padding: 10px; border-radius: 5px; margin-bottom: 5px; border-left: 5px solid #FF4B4B; }
    </style>
    """, unsafe_allow_html=True)

DB_FILE = "ordini_bar_pagano.csv"

# --- LISTINO ---
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

# --- STATO DELLA SESSIONE (Memoria dell'app) ---
if 'tavolo_scelto' not in st.session_state: st.session_state.tavolo_scelto = None
if 'categoria_scelta' not in st.session_state: st.session_state.categoria_scelta = "Brioche e Cornetti"
if 'carrello' not in st.session_state: st.session_state.carrello = []

# --- FUNZIONI DATABASE ---
def carica_ordini():
    if not os.path.exists(DB_FILE): return []
    try:
        df = pd.read_csv(DB_FILE)
        return [] if df.empty else df.to_dict('records')
    except: return []

def salva_ordini_multipli(nuovi_ordini):
    ordini_esistenti = carica_ordini()
    ordini_esistenti.extend(nuovi_ordini)
    df = pd.DataFrame(ordini_esistenti)
    df.to_csv(DB_FILE, index=False)

query_params = st.query_params
ruolo = query_params.get("ruolo", "tavolo")

# --- 1. INTERFACCIA BANCONE (Invariata) ---
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
                    st.subheader(f"🪑 Tavolo {t}")
                    for _, row in prod_t.iterrows():
                        st.markdown(f"<p class='product-text'>• {row['prodotto']}</p>", unsafe_allow_html=True)
                        if str(row['nota']) != 'nan' and row['nota']:
                            st.markdown(f"<p class='note-text'>&nbsp;&nbsp;({row['nota']})</p>", unsafe_allow_html=True)
                    st.divider()
                    st.markdown(f"**Totale: € {prod_t['prezzo'].sum():.2f}**")
                    if st.button(f"CHIUDI CONTO T{t}", key=f"p_{t}", type="primary", use_container_width=True):
                        nuova = [o for o in ordini_attivi if str(o['tavolo']) != t]
                        pd.DataFrame(nuova if nuova else columns=["tavolo", "prodotto", "prezzo", "nota", "orario"]).to_csv(DB_FILE, index=False)
                        st.rerun()
    time.sleep(15)
    st.rerun()

# --- 2. INTERFACCIA CLIENTE (CON CARRELLO) ---
else:
    st.title("☕ BENVENUTO AL BAR PAGANO")
    
    # STEP 1: TAVOLO
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
        col_menu, col_carrello = st.columns([2, 1])
        
        with col_menu:
            st.write(f"### 2. Aggiungi prodotti al carrello:")
            # Categorie
            cat_cols = st.columns(3)
            for i, cat in enumerate(MENU.keys()):
                with cat_cols[i]:
                    tipo_c = "primary" if st.session_state.categoria_scelta == cat else "secondary"
                    if st.button(cat, key=f"cat_{i}", use_container_width=True, type=tipo_c):
                        st.session_state.categoria_scelta = cat
                        st.rerun()
            
            # Prodotti
            prod_list = MENU[st.session_state.categoria_scelta]
            p_cols = st.columns(2)
            for idx, (nome, prezzo) in enumerate(prod_list.items()):
                with p_cols[idx % 2]:
                    if st.button(f"➕ {nome}\n€{prezzo:.2f}", key=f"pr_{idx}", use_container_width=True):
                        # Aggiunge al carrello temporaneo
                        st.session_state.carrello.append({
                            "tavolo": st.session_state.tavolo_scelto,
                            "prodotto": nome,
                            "prezzo": prezzo,
                            "orario": datetime.now().strftime("%H:%M")
                        })
                        st.toast(f"Aggiunto: {nome}")
        
        with col_carrello:
            st.write("### 🛒 Il tuo Ordine")
            if not st.session_state.carrello:
                st.write("Il carrello è vuoto")
            else:
                totale_carrello = 0
                for idx, item in enumerate(st.session_state.carrello):
                    st.markdown(f"""<div class='cart-item'><b>{item['prodotto']}</b><br>€ {item['prezzo']:.2f}</div>""", unsafe_allow_html=True)
                    totale_carrello += item['prezzo']
                
                st.markdown(f"## Totale: € {totale_carrello:.2f}")
                
                nota_ordine = st.text_input("Note generali (es. caffè freddi)")
                
                if st.button("🚀 INVIA TUTTO ORA", use_container_width=True, type="primary"):
                    # Assegna la nota a tutti gli elementi del carrello
                    for item in st.session_state.carrello:
                        item['nota'] = nota_ordine
                    
                    salva_ordini_multipli(st.session_state.carrello)
                    st.success("Ordine inviato con successo!")
                    st.balloons()
                    # Svuota il carrello
                    st.session_state.carrello = []
                    time.sleep(2)
                    st.rerun()
                
                if st.button("🗑️ Svuota carrello", use_container_width=True):
                    st.session_state.carrello = []
                    st.rerun()

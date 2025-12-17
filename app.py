import streamlit as st
import pandas as pd
import os
import time
from datetime import datetime

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="BAR PAGANO", page_icon="☕", layout="wide")

# CSS per personalizzare la grafica (testi grandi e bottoni alti)
st.markdown("""
    <style>
    .product-text { font-size: 24px !important; font-weight: bold; }
    .note-text { font-size: 18px !important; font-style: italic; opacity: 0.8; }
    .stButton>button { height: 3.5em; font-size: 18px !important; border-radius: 10px; }
    .cart-item { 
        background-color: rgba(255, 75, 75, 0.1); 
        padding: 10px; 
        border-radius: 10px; 
        margin-bottom: 10px; 
        border-left: 5px solid #FF4B4B;
    }
    </style>
    """, unsafe_allow_html=True)

DB_FILE = "ordini_bar_pagano.csv"

# --- LISTINO PRODOTTI ---
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
if 'carrello' not in st.session_state: st.session_state.carrello = []

# --- FUNZIONI DATABASE ---
def carica_ordini():
    if not os.path.exists(DB_FILE): return []
    try:
        df = pd.read_csv(DB_FILE)
        if df.empty: return []
        lista = df.to_dict('records')
        for d in lista: d['tavolo'] = str(d['tavolo'])
        return lista
    except: return []

def salva_ordini_multipli(nuovi_ordini):
    ordini_esistenti = carica_ordini()
    ordini_esistenti.extend(nuovi_ordini)
    df = pd.DataFrame(ordini_esistenti)
    df.to_csv(DB_FILE, index=False)

# Navigazione tramite URL (?ruolo=banco)
query_params = st.query_params
ruolo = query_params.get("ruolo", "tavolo")

# --- 1. INTERFACCIA BANCONE / CASSA ---
if ruolo == "banco":
    st.title("🖥️ DASHBOARD BANCONE - BAR PAGANO")
    ordini_attivi = carica_ordini()

    if not ordini_attivi:
        st.info("In attesa di nuovi ordini...")
    else:
        df = pd.DataFrame(ordini_attivi)
        df['tavolo'] = df['tavolo'].astype(str)
        tavoli_attivi = sorted(df['tavolo'].unique(), key=lambda x: int(x) if x.isdigit() else 0)

        cols = st.columns(4) 
        for idx, t in enumerate(tavoli_attivi):
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
                    
                    # Tasto Chiudi Conto (Corretto)
                    if st.button(f"CHIUDI CONTO T{t}", key=f"pay_{t}", type="primary", use_container_width=True):
                        rimanenti = [o for o in ordini_attivi if str(o['tavolo']) != t]
                        if not rimanenti:
                            pd.DataFrame(columns=["tavolo", "prodotto", "prezzo", "nota", "orario"]).to_csv(DB_FILE, index=False)
                        else:
                            pd.DataFrame(rimanenti).to_csv(DB_FILE, index=False)
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
        col_menu, col_carrello = st.columns([2, 1])
        
        with col_menu:
            st.write(f"### 2. Scegli e aggiungi prodotti:")
            # Tasti Categoria
            cat_cols = st.columns(3)
            for i, cat in enumerate(MENU.keys()):
                with cat_cols[i]:
                    tipo_c = "primary" if st.session_state.categoria_scelta == cat else "secondary"
                    if st.button(cat, key=f"cat_{i}", use_container_width=True, type=tipo_c):
                        st.session_state.categoria_scelta = cat
                        st.rerun()
            
            # Tasti Prodotti
            st.write(f"Categoria: **{st.session_state.categoria_scelta}**")
            prod_list = MENU[st.session_state.categoria_scelta]
            p_cols = st.columns(2)
            for idx, (nome, prezzo) in enumerate(prod_list.items()):
                with p_cols[idx % 2]:
                    if st.button(f"➕ {nome}\n€{prezzo:.2f}", key=f"pr_{idx}", use_container_width=True):
                        st.session_state.carrello.append({
                            "tavolo": st.session_state.tavolo_scelto,
                            "prodotto": nome,
                            "prezzo": prezzo,
                            "orario": datetime.now().strftime("%H:%M")
                        })
                        st.rerun()
        
        with col_carrello:
            st.write("### 🛒 Carrello")
            if not st.session_state.carrello:
                st.info("Aggiungi qualcosa!")
            else:
                totale_c = 0
                # Usiamo un ciclo per mostrare i prodotti e il tasto rimuovi
                for i, item in enumerate(st.session_state.carrello):
                    col_item, col_del = st.columns([4, 1])
                    with col_item:
                        st.markdown(f"<div class='cart-item'>{item['prodotto']} - €{item['prezzo']:.2f}</div>", unsafe_allow_html=True)
                    with col_del:
                        if st.button("❌", key=f"del_{i}"):
                            st.session_state.carrello.pop(i)
                            st.rerun()
                    totale_c += item['prezzo']
                
                st.markdown(f"## Totale: € {totale_c:.2f}")
                nota_ordine = st.text_input("Note (es. caffè macchiato freddo)")
                
                if st.button("🚀 INVIA ORDINE ORA", use_container_width=True, type="primary"):
                    # Aggiunge la nota a tutti i prodotti del carrello
                    for item in st.session_state.carrello:
                        item['nota'] = nota_ordine
                    
                    salva_ordini_multipli(st.session_state.carrello)
                    st.success("Inviato al bancone!")
                    st.balloons()
                    st.session_state.carrello = []
                    time.sleep(2)
                    st.rerun()
                
                if st.button("🗑️ Svuota tutto"):
                    st.session_state.carrello = []
                    st.rerun()

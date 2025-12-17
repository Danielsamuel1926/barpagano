import streamlit as st
import pandas as pd
import os
import time
from datetime import datetime

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="BAR PAGANO", page_icon="☕", layout="wide")

# CSS per testi grandi e leggibili
st.markdown("""
    <style>
    .product-text { font-size: 24px !important; font-weight: bold; }
    .note-text { font-size: 18px !important; font-style: italic; opacity: 0.8; }
    .stButton>button { height: 3em; font-size: 18px !important; }
    </style>
    """, unsafe_allow_html=True)

DB_FILE = "ordini_bar_pagano.csv"

MENU = {
    "Cornetto al cioccolato": 1.50, "Cornetto a crema": 1.50, "Cornetto a miele": 1.50,
    "Treccia miele e noci": 1.80, "Polacca": 2.00, "Graffa": 1.20,
    "Monachina": 1.80, "Pandistelle": 1.00, "Flauto": 1.00
}

# --- STATO DELLA SESSIONE (Per ricordare cosa clicca il cliente) ---
if 'tavolo_scelto' not in st.session_state: st.session_state.tavolo_scelto = None
if 'prodotto_scelto' not in st.session_state: st.session_state.prodotto_scelto = None

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

def salva_ordini(lista_ordini):
    df = pd.DataFrame(lista_ordini) if lista_ordini else pd.DataFrame(columns=["tavolo", "prodotto", "prezzo", "nota", "orario"])
    df.to_csv(DB_FILE, index=False)

query_params = st.query_params
ruolo = query_params.get("ruolo", "tavolo")

# --- INTERFACCIA BANCONE / CASSA ---
if ruolo == "banco":
    st.title("🖥️ DASHBOARD BANCONE - BAR PAGANO")
    ordini_attivi = carica_ordini()

    if not ordini_attivi:
        st.info("Nessun ordine attivo.")
    else:
        df_ordini = pd.DataFrame(ordini_attivi)
        df_ordini['tavolo'] = df_ordini['tavolo'].astype(str)
        lista_tavoli = sorted(df_ordini['tavolo'].unique(), key=int)

        cols = st.columns(4) 
        for idx, num_tavolo in enumerate(lista_tavoli):
            with cols[idx % 4]:
                with st.container(border=True):
                    prod_tavolo = df_ordini[df_ordini['tavolo'] == num_tavolo]
                    st.subheader(f"🪑 Tavolo {num_tavolo}")
                    
                    for _, row in prod_tavolo.iterrows():
                        st.markdown(f"<p class='product-text'>• {row['prodotto']}</p>", unsafe_allow_html=True)
                        if str(row['nota']) != 'nan' and row['nota']:
                            st.markdown(f"<p class='note-text'>&nbsp;&nbsp;({row['nota']})</p>", unsafe_allow_html=True)
                    
                    st.write("---")
                    st.markdown(f"**Totale: € {prod_tavolo['prezzo'].sum():.2f}**")
                    
                    if st.button(f"CHIUDI CONTO T{num_tavolo}", key=f"pay_{num_tavolo}", type="primary", use_container_width=True):
                        nuova_lista = [o for o in ordini_attivi if str(o['tavolo']) != str(num_tavolo)]
                        salva_ordini(nuova_lista)
                        st.rerun()
    time.sleep(15)
    st.rerun()

# --- INTERFACCIA CLIENTE ---
else:
    st.title("☕ BENVENUTO AL BAR PAGANO")
    
    # 1. SELEZIONE TAVOLO (Griglia 5x4)
    st.write("### 1. Seleziona il tuo Tavolo:")
    tav_cols = st.columns(5)
    for i in range(1, 21):
        t_str = str(i)
        with tav_cols[(i-1) % 5]:
            # Se il tavolo è selezionato, il tasto diventa colorato (primary)
            stile = "primary" if st.session_state.tavolo_scelto == t_str else "secondary"
            if st.button(f"T{i}", key=f"tav_{i}", use_container_width=True, type=stile):
                st.session_state.tavolo_scelto = t_str
                st.rerun()

    # 2. SELEZIONE PRODOTTO
    if st.session_state.tavolo_scelto:
        st.write(f"---")
        st.write(f"### 2. Cosa desideri per il **Tavolo {st.session_state.tavolo_scelto}**?")
        prod_cols = st.columns(2)
        for idx, (nome, prezzo) in enumerate(MENU.items()):
            with prod_cols[idx % 2]:
                stile_p = "primary" if st.session_state.prodotto_scelto == nome else "secondary"
                if st.button(f"{nome} - €{prezzo:.2f}", key=f"prod_{idx}", use_container_width=True, type=stile_p):
                    st.session_state.prodotto_scelto = nome
                    st.rerun()

    # 3. INVIO ORDINE
    if st.session_state.prodotto_scelto:
        st.write("---")
        prezzo_finale = MENU[st.session_state.prodotto_scelto]
        st.write(f"Stai ordinando: **{st.session_state.prodotto_scelto}** (€{prezzo_finale:.2f})")
        nota = st.text_input("Aggiungi note (es. senza zucchero)")
        
        if st.button("🚀 INVIA ORDINE ORA", use_container_width=True, type="primary"):
            nuovo = {
                "tavolo": st.session_state.tavolo_scelto,
                "prodotto": st.session_state.prodotto_scelto,
                "prezzo": prezzo_finale,
                "nota": nota,
                "orario": datetime.now().strftime("%H:%M")
            }
            correnti = carica_ordini()
            correnti.append(nuovo)
            salva_ordini(correnti)
            
            st.success("Ordine inviato con successo!")
            st.balloons()
            # Reset per l'ordine successivo
            st.session_state.prodotto_scelto = None
            time.sleep(2)
            st.rerun()

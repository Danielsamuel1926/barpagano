import streamlit as st
import pandas as pd
import os
import time
from datetime import datetime

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="BAR PAGANO - Gestione", page_icon="💰", layout="wide")

# CSS SOLO PER LA GRANDEZZA (Ho rimosso i colori fissi)
st.markdown("""
    <style>
    .product-text {
        font-size: 24px !important;
        font-weight: bold;
        margin-bottom: 0px;
    }
    .note-text {
        font-size: 18px !important;
        font-style: italic;
        opacity: 0.8;
    }
    </style>
    """, unsafe_allow_html=True)

DB_FILE = "ordini_bar_pagano.csv"

MENU = {
    "Cornetto al cioccolato": 1.50, "Cornetto a crema": 1.50, "Cornetto a miele": 1.50,
    "Treccia miele e noci": 1.80, "Polacca": 2.00, "Graffa": 1.20,
    "Monachina": 1.80, "Pandistelle": 1.00, "Flauto": 1.00
}

TAVOLI = [str(i) for i in range(1, 21)]

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

if 'ordini' not in st.session_state:
    st.session_state.ordini = carica_ordini()

query_params = st.query_params
ruolo = query_params.get("ruolo", "tavolo")

# --- INTERFACCIA BANCONE / CASSA ---
if ruolo == "banco":
    st.title("🖥️ DASHBOARD BANCONE - BAR PAGANO")
    
    st.session_state.ordini = carica_ordini()

    if not st.session_state.ordini:
        st.info("Nessun ordine attivo.")
    else:
        df_ordini = pd.DataFrame(st.session_state.ordini)
        df_ordini['tavolo'] = df_ordini['tavolo'].astype(str)
        lista_tavoli_attivi = sorted(df_ordini['tavolo'].unique(), key=int)

        # Griglia a 4 colonne per schede compatte
        cols = st.columns(4) 
        
        for idx, num_tavolo in enumerate(lista_tavoli_attivi):
            with cols[idx % 4]:
                with st.container(border=True):
                    prodotti_tavolo = df_ordini[df_ordini['tavolo'] == num_tavolo]
                    totale_tavolo = prodotti_tavolo['prezzo'].sum()
                    
                    # Numero Tavolo
                    st.subheader(f"🪑 Tavolo {num_tavolo}")
                    
                    # Elenco Prodotti GRANDI
                    for _, row in prodotti_tavolo.iterrows():
                        st.markdown(f"<p class='product-text'>• {row['prodotto']}</p>", unsafe_allow_html=True)
                        if str(row['nota']) != 'nan' and row['nota']:
                            st.markdown(f"<p class='note-text'>&nbsp;&nbsp;({row['nota']})</p>", unsafe_allow_html=True)
                    
                    st.write("---")
                    st.markdown(f"**Totale: € {totale_tavolo:.2f}**")
                    
                    # Pulsante Reset
                    if st.button(f"CHIUDI CONTO T{num_tavolo}", key=f"pay_{num_tavolo}", type="primary", use_container_width=True):
                        nuova_lista = [o for o in st.session_state.ordini if str(o['tavolo']) != str(num_tavolo)]
                        st.session_state.ordini = nuova_lista
                        salva_ordini(nuova_lista)
                        st.rerun()

    time.sleep(15)
    st.rerun()

# --- INTERFACCIA CLIENTE ---
else:
    st.title("☕ BAR PAGANO")
    tavolo = st.selectbox("Il tuo Tavolo", TAVOLI)
    prodotto = st.selectbox("Cosa desideri?", list(MENU.keys()))
    prezzo = MENU[prodotto]
    st.markdown(f"## Prezzo: € {prezzo:.2f}")
    nota = st.text_input("Note")
    
    if st.button("INVIA ORDINE", use_container_width=True, type="primary"):
        nuovo = {"tavolo": str(tavolo), "prodotto": prodotto, "prezzo": prezzo, "nota": nota, "orario": datetime.now().strftime("%H:%M")}
        correnti = carica_ordini()
        correnti.append(nuovo)
        salva_ordini(correnti)
        st.session_state.ordini = correnti
        st.success("Inviato!")

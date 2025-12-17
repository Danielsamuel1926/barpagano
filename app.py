import streamlit as st
import pandas as pd
import os
import time
from datetime import datetime

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="BAR PAGANO - Gestione", page_icon="💰", layout="wide")

# CSS personalizzato per pulire un po' l'interfaccia
st.markdown("""
    <style>
    .product-text {
        font-size: 22px !important;
        font-weight: bold;
        color: #1E1E1E;
        margin-bottom: 0px;
    }
    .note-text {
        font-size: 16px !important;
        color: #D32F2F;
        font-style: italic;
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
        if st.button("🔄 Verifica Nuovi Ordini"): st.rerun()
    else:
        df_ordini = pd.DataFrame(st.session_state.ordini)
        df_ordini['tavolo'] = df_ordini['tavolo'].astype(str)
        lista_tavoli_attivi = df_ordini['tavolo'].unique()

        # Usiamo 4 colonne per far sì che le schede siano compatte e non troppo larghe
        cols = st.columns(4) 
        
        for idx, num_tavolo in enumerate(lista_tavoli_attivi):
            with cols[idx % 4]: # Distribuisce le schede nelle 4 colonne
                with st.container(border=True):
                    prodotti_tavolo = df_ordini[df_ordini['tavolo'] == num_tavolo]
                    totale_tavolo = prodotti_tavolo['prezzo'].sum()
                    
                    # Intestazione Tavolo
                    st.markdown(f"<h2 style='text-align: center; background-color: #f0f2f6; border-radius: 10px;'>🪑 T{num_tavolo}</h2>", unsafe_allow_html=True)
                    
                    # Elenco Prodotti con carattere GRANDE
                    for _, row in prodotti_tavolo.iterrows():
                        st.markdown(f"<p class='product-text'>• {row['prodotto']}</p>", unsafe_allow_html=True)
                        if str(row['nota']) != 'nan' and row['nota']:
                            st.markdown(f"<p class='note-text'>&nbsp;&nbsp;&nbsp;Nota: {row['nota']}</p>", unsafe_allow_html=True)
                    
                    st.divider()
                    st.markdown(f"<h3 style='text-align: right;'>Totale: € {totale_tavolo:.2f}</h3>", unsafe_allow_html=True)
                    
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
    nota = st.text_input("Note (es: macchiato freddo, tazza grande...)")
    
    if st.button("INVIA ORDINE", use_container_width=True, type="primary"):
        nuovo = {"tavolo": str(tavolo), "prodotto": prodotto, "prezzo": prezzo, "nota": nota, "orario": datetime.now().strftime("%H:%M")}
        correnti = carica_ordini()
        correnti.append(nuovo)
        salva_ordini(correnti)
        st.session_state.ordini = correnti
        st.success("Ordine inviato!")
        st.balloons()

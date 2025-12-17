import streamlit as st
import pandas as pd
import os
import time
from datetime import datetime

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="BAR PAGANO", page_icon="☕", layout="wide")

DB_FILE = "ordini_bar_pagano.csv"
PRODOTTI = [
    "Cornetto al cioccolato", "Cornetto a crema", "Cornetto a miele", 
    "Treccia miele e noci", "Polacca", "Graffa", 
    "Monachina", "Pandistelle", "Flauto"
]
TAVOLI = [str(i) for i in range(1, 21)]

# --- FUNZIONI DATABASE ---
def carica_ordini():
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE).to_dict('records')
    return []

def salva_ordini(ordini):
    pd.DataFrame(ordini).to_csv(DB_FILE, index=False)

# Inizializzazione dati
if 'ordini' not in st.session_state:
    st.session_state.ordini = carica_ordini()

# --- LOGICA NAVIGAZIONE ---
query_params = st.query_params
ruolo = query_params.get("ruolo", "tavolo")

# --- PAGINA BANCONE ---
if ruolo == "banco":
    st.title("🖥️ DASHBOARD BANCONE - BAR PAGANO")
    
    # Suono di notifica (nascosto, si attiva se ci sono nuovi ordini)
    if st.session_state.ordini:
        st.components.v1.html(
            """
            <audio autoplay>
                <source src="https://actions.google.com/sounds/v1/alarms/beep_short.ogg" type="audio/ogg">
            </audio>
            """,
            height=0,
        )

    st.write(f"Ordini attivi: **{len(st.session_state.ordini)}**")
    
    if not st.session_state.ordini:
        st.info("In attesa di nuovi ordini...")
    else:
        # Mostra ordini
        for i, ordine in enumerate(st.session_state.ordini):
            with st.container(border=True):
                c1, c2, c3 = st.columns([1, 4, 1])
                with c1:
                    st.markdown(f"<h1 style='color:red; margin:0;'>T{ordine['tavolo']}</h1>", unsafe_allow_html=True)
                    st.caption(f"Ore {ordine['orario']}")
                with c2:
                    st.subheader(ordine['prodotto'])
                    if str(ordine['nota']) != "nan" and ordine['nota']:
                        st.warning(f"NOTA: {ordine['nota']}")
                with c3:
                    if st.button("FATTO ✅", key=f"done_{i}_{ordine['tavolo']}"):
                        st.session_state.ordini.pop(i)
                        salva_ordini(st.session_state.ordini)
                        st.rerun()
    
    # Auto-aggiornamento ogni 10 secondi
    time.sleep(10)
    st.rerun()

# --- PAGINA CLIENTE ---
else:
    st.title("☕ BAR PAGANO")
    st.subheader("Ordina comodamente dal tuo tavolo")

    with st.form("ordine_form"):
        tavolo = st.selectbox("Seleziona il tuo Tavolo", TAVOLI)
        prodotto = st.selectbox("Cosa desideri?", PRODOTTI)
        nota = st.text_input("Note (es: macchiato freddo, tazza grande...)")
        
        inviato = st.form_submit_button("INVIA ORDINE", use_container_width=True)

    if inviato:
        nuovo = {
            "tavolo": tavolo,
            "prodotto": prodotto,
            "nota": nota,
            "orario": datetime.now().strftime("%H:%M")
        }
        # Carica, aggiungi e salva
        ordini_attuali = carica_ordini()
        ordini_attuali.append(nuovo)
        salva_ordini(ordini_attuali)
        st.session_state.ordini = ordini_attuali
        
        st.success(f"Ordine inviato! Il tuo {prodotto} arriverà presto al Tavolo {tavolo}.")
        st.balloons()
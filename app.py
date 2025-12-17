import streamlit as st
import pandas as pd
import os
import time
from datetime import datetime

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="BAR PAGANO - Cassa", page_icon="💰", layout="wide")

DB_FILE = "ordini_bar_pagano.csv"

# --- LISTINO PREZZI ---
MENU = {
    "Cornetto al cioccolato": 1.50,
    "Cornetto a crema": 1.50,
    "Cornetto a miele": 1.50,
    "Treccia miele e noci": 1.80,
    "Polacca": 2.00,
    "Graffa": 1.20,
    "Monachina": 1.80,
    "Pandistelle": 1.00,
    "Flauto": 1.00
}

TAVOLI = [str(i) for i in range(1, 21)]

# --- FUNZIONI DATABASE ---
def carica_ordini():
    if os.path.exists(DB_FILE):
        try:
            df = pd.read_csv(DB_FILE)
            if df.empty: return []
            return df.to_dict('records')
        except: return []
    return []

def salva_ordini(ordini):
    df = pd.DataFrame(ordini) if ordini else pd.DataFrame(columns=["tavolo", "prodotto", "prezzo", "nota", "orario"])
    df.to_csv(DB_FILE, index=False)

# Inizializzazione dati
if 'ordini' not in st.session_state:
    st.session_state.ordini = carica_ordini()

# --- LOGICA NAVIGAZIONE ---
query_params = st.query_params
ruolo = query_params.get("ruolo", "tavolo")

# --- INTERFACCIA BANCONE / CASSA ---
if ruolo == "banco":
    st.title("👨‍🍳 BANCONE & CASSA - BAR PAGANO")
    
    if st.session_state.ordini:
        # Calcolo incasso totale potenziale (ordini non ancora chiusi)
        totale_da_incassare = sum(float(o['prezzo']) for o in st.session_state.ordini)
        st.sidebar.metric("Incasso Totale Ordini Attivi", f"€ {totale_da_incassare:.2f}")
        
        # Suono di notifica
        st.components.v1.html("""<audio autoplay><source src="https://actions.google.com/sounds/v1/alarms/beep_short.ogg" type="audio/ogg"></audio>""", height=0)

    if not st.session_state.ordini:
        st.info("Nessun ordine attivo al momento.")
    else:
        for i, ordine in enumerate(st.session_state.ordini):
            with st.container(border=True):
                c1, c2, c3, c4 = st.columns([1, 3, 1, 1])
                with c1:
                    st.markdown(f"<h1 style='color:red; margin:0;'>T{ordine['tavolo']}</h1>", unsafe_allow_html=True)
                    st.caption(f"{ordine['orario']}")
                with c2:
                    st.subheader(f"{ordine['prodotto']}")
                    if str(ordine['nota']) != "nan" and ordine['nota']:
                        st.info(f"Nota: {ordine['nota']}")
                with c3:
                    st.markdown(f"### € {ordine['prezzo']:.2f}")
                with c4:
                    # Pulsante per chiudere l'ordine e pagare
                    if st.button("CHIUDI CONTO 💰", key=f"pay_{i}"):
                        st.session_state.ordini.pop(i)
                        salva_ordini(st.session_state.ordini)
                        st.success("Conto Chiuso!")
                        st.rerun()
    
    time.sleep(10)
    st.rerun()

# --- INTERFACCIA CLIENTE ---
else:
    st.title("☕ BAR PAGANO")
    st.subheader("Fai il tuo ordine")

    with st.form("ordine_form"):
        tavolo = st.selectbox("Il tuo Tavolo", TAVOLI)
        prodotto_nome = st.selectbox("Cosa desideri?", list(MENU.keys()))
        prezzo_unitario = MENU[prodotto_nome]
        
        st.write(f"Prezzo prodotto: **€ {prezzo_unitario:.2f}**")
        
        nota = st.text_input("Note (es: ben cotto, senza zucchero...)")
        inviato = st.form_submit_button("CONFERMA E INVIA ORDINE", use_container_width=True)

    if inviato:
        nuovo = {
            "tavolo": tavolo,
            "prodotto": prodotto_nome,
            "prezzo": prezzo_unitario,
            "nota": nota,
            "orario": datetime.now().strftime("%H:%M")
        }
        ordini_attuali = carica_ordini()
        ordini_attuali.append(nuovo)
        salva_ordini(ordini_attuali)
        st.session_state.ordini = ordini_attuali
        st.success(f"Ordine inviato! Totale da pagare al banco: € {prezzo_unitario:.2f}")
        st.balloons()



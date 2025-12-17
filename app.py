import streamlit as st
import pandas as pd
import os
import time
from datetime import datetime

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="BAR PAGANO", page_icon="☕", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #FFFFFF; }
    [data-testid="column"] { flex: 1 1 calc(25% - 10px) !important; min-width: 70px !important; }
    div[data-testid="column"] button { width: 100% !important; font-weight: bold !important; border-radius: 12px !important; }
    .servito { color: #555555 !important; text-decoration: line-through; opacity: 0.6; font-style: italic; }
    .da-servire { color: #FFFFFF !important; font-weight: bold; font-size: 18px; }
    .product-info { font-size: 13px; color: #BBBBBB; text-align: center; margin-bottom: 10px; }
    .selected-tavolo { background-color: #FF4B4B; color: white; padding: 15px; border-radius: 15px; text-align: center; font-size: 24px; font-weight: bold; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

DB_FILE = "ordini_bar_pagano.csv"
STOCK_FILE = "stock_bar_pagano.csv"
COLONNE = ["id_univoco", "tavolo", "prodotto", "prezzo", "nota", "orario", "stato"]

# Categoria speciale con gestione scorte
CAT_STOCK = "Brioche e Cornetti"

MENU_DATA = {
    "Brioche e Cornetti": {"Cornetto cioccolato": 1.50, "Cornetto crema": 1.50, "Cornetto miele": 1.50, "Graffa": 1.20, "Polacca": 2.00, "Treccia noci": 1.80},
    "Bevande Calde": {"Caffè": 1.00, "Caffè Macchiato": 1.10, "Cappuccino": 1.50, "Tè caldo": 1.50},
    "Bevande Fredde": {"Acqua 0.5L": 1.00, "Coca Cola": 2.50, "Aranciata": 2.50, "Birra": 3.00}
}

# --- FUNZIONI DATI ---
def carica_ordini():
    if not os.path.exists(DB_FILE) or os.stat(DB_FILE).st_size == 0:
        pd.DataFrame(columns=COLONNE).to_csv(DB_FILE, index=False)
        return []
    try:
        return pd.read_csv(DB_FILE).to_dict('records')
    except: return []

def salva_ordini(lista):
    pd.DataFrame(lista if lista else columns=COLONNE).to_csv(DB_FILE, index=False)

def carica_stock():
    if not os.path.exists(STOCK_FILE) or os.stat(STOCK_FILE).st_size == 0:
        # Crea stock iniziale solo per le brioche
        data = [{"prodotto": n, "quantita": 100} for n in MENU_DATA[CAT_STOCK]]
        pd.DataFrame(data).to_csv(STOCK_FILE, index=False)
    return pd.read_csv(STOCK_FILE).set_index('prodotto')['quantita'].to_dict()

def aggiorna_stock(nome, var):
    # Aggiorna solo se il prodotto fa parte della categoria Brioche
    if nome in MENU_DATA[CAT_STOCK]:
        df = pd.read_csv(STOCK_FILE)
        if nome in df['prodotto'].values:
            qta = df.loc[df['prodotto'] == nome, 'quantita'].values[0]
            df.loc[df['prodotto'] == nome, 'quantita'] = max(0, qta + var)
            df.to_csv(STOCK_FILE, index=False)

# --- LOGICA ---
ruolo = st.query_params.get("ruolo", "tavolo")

if ruolo == "banco":
    st.title("🖥️ CONSOLE BANCONE")
    tab1, tab2, tab3 = st.tabs(["📋 ORDINI TAVOLI", "⚡ BANCOSERVITO", "📦 STOCK BRIOCHE"])
    
    with tab1:
        ordini = carica_ordini()
        if not ordini: st.info("In attesa ordini...")
        else:
            df_o = pd.DataFrame(ordini)
            tavoli = sorted(df_o['tavolo'].unique(), key=lambda x: int(x))
            cols = st.columns(3)
            for idx, t in enumerate(tavoli):
                with cols[idx % 3]:
                    with st.container(border=True):
                        st.subheader(f"🪑 Tavolo {t}")
                        for i, r in enumerate(ordini):
                            if str(r['tavolo']) == str(t):
                                classe = "servito" if r['stato'] == "SI" else "da-servire"
                                col_t, col_b = st.columns([3, 1])
                                col_t.markdown(f"<span class='{classe}'>{r['prodotto']}</span>", unsafe_allow_html=True)
                                if r['stato'] == "NO":
                                    if col_b.button("Fatto", key=f"sv_{t}_{i}"):
                                        ordini[i]['stato'] = "SI"
                                        salva_ordini(ordini)
                                        st.rerun()
                                else: col_b.write("✅")
                        st.divider()
                        tot = sum(float(o['prezzo']) for o in ordini if str(o['tavolo']) == str(t))
                        if st.button(f"PAGATO (€{tot:.2f})", key=f"pay_{t}", type="primary"):
                            salva_ordini([o for o in ordini if str(o['tavolo']) != str(t)])
                            st.rerun()

    with tab2:
        st.write("### ⚡ Vendita Rapida")
        dispo = carica_stock()
        for cat, prodotti in MENU_DATA.items():
            st.markdown(f"#### {cat}")
            b_cols = st.columns(4)
            for idx, (nome, prezzo) in enumerate(prodotti.items()):
                # Mostra quantità solo se è Brioche
                qta = dispo.get(nome, "∞") if cat == CAT_STOCK else "∞"
                label = f"{nome}\n({qta})"
                if b_cols[idx % 4].button(label, key=f"bs_{nome}"):
                    aggiorna_stock(nome, -1)
                    st.toast(f"Venduto: {nome}")
                    st.rerun()

    with tab3:
        st.write("### 📦 Carico Brioche e Cornetti")
        stk = carica_stock()
        for prod in MENU_DATA[CAT_STOCK]:
            c1, c2 = st.columns([3, 1])
            attuale = stk.get(prod, 0)
            nuova = c2.number_input(f"{prod}", value=int(attuale), key=f"stk_{prod}", step=1)
            if nuova != attuale:
                df = pd.read_csv(STOCK_FILE)
                df.loc[df['prodotto'] == prod, 'quantita'] = nuova
                df.to_csv(STOCK_FILE, index=False)
                st.rerun()
    time.sleep(15)
    st.rerun()

else:
    # --- CLIENTE ---
    st.title("☕ BAR PAGANO")
    if st.session_state.get('tavolo_scelto') is None:
        st.write("### 🪑 Seleziona tavolo:")
        t_cols = st.columns(4)
        for i in range(1, 21):
            if t_cols[(i-1) % 4].button(f"{i}", key=f"t_{i}", use_container_width=True):
                st.session_state.tavolo_scelto = str(i)
                st.rerun()
    else:
        col_t, col_b = st.columns([3, 1])
        col_t.markdown(f"<div class='selected-tavolo'>TAVOLO {st.session_state.tavolo_scelto}</div>", unsafe_allow_html=True)
        if col_b.button("🔄 Cambia"):
            st.session_state.tavolo_scelto = None
            st.rerun()

        st.divider()
        cat_scelta = st.radio("Categoria", list(MENU_DATA.keys()), horizontal=True)
        dispo = carica_stock()
        p_cols = st.columns(2)
        
        for idx, (nome, prezzo) in enumerate(MENU_DATA[cat_scelta].items()):
            # Logica quantità solo per Brioche
            qta = dispo.get(nome, 999) if cat_scelta == CAT_STOCK else 999
            disabled = (cat_scelta == CAT_STOCK and qta <= 0)
            
            with p_cols[idx % 2]:
                if st.button(f"➕ {nome}\n€{prezzo:.2f}", key=f"btn_{nome}", disabled=disabled, use_container_width=True):
                    if 'carrello' not in st.session_state: st.session_state.carrello = []
                    st.session_state.carrello.append({"tavolo": st.session_state.tavolo_scelto, "prodotto": nome, "prezzo": prezzo})
                
                if cat_scelta == CAT_STOCK:
                    st.markdown(f"<div class='product-info'>Rimasti: {qta}</div>", unsafe_allow_html=True)

        if st.session_state.get('carrello'):
            st.divider()
            tot = sum(item['prezzo'] for item in st.session_state.carrello)
            st.write(f"🛒 CARRELLO (€{tot:.2f})")
            if st.button("🚀 INVIA ORDINE", type="primary", use_container_width=True):
                ordini_at = carica_ordini()
                for item in st.session_state.carrello:
                    item.update({"nota": "", "orario": datetime.now().strftime("%H:%M"), "stato": "NO", "id_univoco": str(time.time()) + item['prodotto']})
                    ordini_at.append(item)
                    aggiorna_stock(item['prodotto'], -1)
                salva_ordini(ordini_at)
                st.session_state.carrello = []
                st.success("Inviato!")
                time.sleep(1)
                st.rerun()

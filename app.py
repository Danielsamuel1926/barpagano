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
    .qty-text { font-size: 20px; font-weight: bold; text-align: center; padding-top: 5px; }
    .stButton>button[kind="secondary"] { background-color: #2E7D32 !important; color: white !important; border: none !important; }
    </style>
    """, unsafe_allow_html=True)

DB_FILE = "ordini_bar_pagano.csv"
STOCK_FILE = "stock_bar_pagano.csv"
COLONNE = ["id_univoco", "tavolo", "prodotto", "prezzo", "nota", "orario", "stato"]
CAT_STOCK = "Brioche e Cornetti"

MENU_DATA = {
    "Brioche e Cornetti": {"Cornetto cioccolato": 1.50, "Cornetto crema": 1.50, "Cornetto miele": 1.50, "Graffa": 1.20, "Polacca": 2.00, "Treccia noci": 1.80},
    "Bevande Calde": {"Caffè": 1.00, "Caffè Macchiato": 1.10, "Cappuccino": 1.50, "Tè caldo": 1.50},
    "Bevande Fredde": {"Acqua 0.5L": 1.00, "Coca Cola": 2.50, "Aranciata": 2.50, "Birra": 3.00}
}

# --- FUNZIONI DATI ---
def suona_notifica():
    st.markdown("""<audio autoplay><source src="https://raw.githubusercontent.com/rafaelreis-hotmart/Audio-Notification-Streamlit/main/notification.mp3" type="audio/mp3"></audio>""", unsafe_allow_html=True)

def carica_ordini():
    if not os.path.exists(DB_FILE) or os.stat(DB_FILE).st_size == 0:
        pd.DataFrame(columns=COLONNE).to_csv(DB_FILE, index=False)
        return []
    try: return pd.read_csv(DB_FILE).to_dict('records')
    except: return []

def salva_ordini(lista):
    df = pd.DataFrame(lista) if lista else pd.DataFrame(columns=COLONNE)
    df.to_csv(DB_FILE, index=False)

def carica_stock():
    if not os.path.exists(STOCK_FILE) or os.stat(STOCK_FILE).st_size == 0:
        data = [{"prodotto": n, "quantita": 0} for n in MENU_DATA[CAT_STOCK]]
        pd.DataFrame(data).to_csv(STOCK_FILE, index=False)
    # Forza ricaricamento da disco
    return pd.read_csv(STOCK_FILE).set_index('prodotto')['quantita'].to_dict()

def aggiorna_stock_veloce(nome, var):
    if nome in MENU_DATA[CAT_STOCK]:
        df = pd.read_csv(STOCK_FILE)
        if nome in df['prodotto'].values:
            idx = df[df['prodotto'] == nome].index[0]
            df.at[idx, 'quantita'] = max(0, df.at[idx, 'quantita'] + var)
            df.to_csv(STOCK_FILE, index=False)

# --- LOGICA RUOLI ---
ruolo = st.query_params.get("ruolo", "tavolo")

if ruolo == "banco":
    st.title("🖥️ CONSOLE BANCONE")
    
    # TASTO AGGIORNA BANCONE (Sincronizza tutto)
    if st.button("🔄 AGGIORNA ORDINI E DISPONIBILITÀ", use_container_width=True, type="secondary"):
        st.cache_data.clear() # Svuota eventuali cache
        st.rerun()

    tab1, tab2, tab3 = st.tabs(["📋 ORDINI TAVOLI", "⚡ BANCOSERVITO", "📦 STOCK BRIOCHE"])
    
    with tab1:
        ordini = carica_ordini()
        if ordini and any(o['stato'] == "NO" for o in ordini): suona_notifica()
        if not ordini: st.info("In attesa di nuovi ordini...")
        else:
            tavoli_attivi = sorted(set(str(o['tavolo']) for o in ordini), key=lambda x: int(x) if x.isdigit() else 0)
            cols = st.columns(3)
            for idx, t in enumerate(tavoli_attivi):
                with cols[idx % 3]:
                    with st.container(border=True):
                        st.subheader(f"🪑 Tavolo {t}")
                        tot_tavolo = 0
                        for i, r in enumerate(ordini):
                            if str(r['tavolo']) == str(t):
                                cl = "servito" if r['stato'] == "SI" else "da-servire"
                                c_t, c_b = st.columns([3, 1])
                                c_t.markdown(f"<span class='{cl}'>{r['prodotto']}</span>", unsafe_allow_html=True)
                                tot_tavolo += float(r['prezzo'])
                                if r['stato'] == "NO" and c_b.button("Fatto", key=f"sv_{t}_{i}"):
                                    ordini[i]['stato'] = "SI"
                                    salva_ordini(ordini)
                                    st.rerun()
                        st.divider()
                        if st.button(f"PAGATO €{tot_tavolo:.2f}", key=f"pay_{t}", type="primary", use_container_width=True):
                            salva_ordini([o for o in ordini if str(o['tavolo']) != str(t)])
                            st.rerun()

    with tab2:
        st.write("### ⚡ Vendita Rapida Bancone")
        dispo = carica_stock()
        for cat_name, prodotti in MENU_DATA.items():
            st.write(f"**{cat_name}**")
            cols_b = st.columns(4)
            for i, (nome, prezzo) in enumerate(prodotti.items()):
                q = dispo.get(nome, "∞") if cat_name == CAT_STOCK else "∞"
                if cols_b[i % 4].button(f"{nome}\n({q})", key=f"bs_{nome}"):
                    aggiorna_stock_veloce(nome, -1)
                    st.rerun()

    with tab3:
        st.write("### 📦 Carico Magazzino (+/-)")
        stk = carica_stock()
        for p in MENU_DATA[CAT_STOCK]:
            c_n, c_m, c_v, c_p = st.columns([3, 1, 1, 1])
            c_n.write(f"**{p}**")
            if c_m.button("➖", key=f"m_{p}"): aggiorna_stock_veloce(p, -1); st.rerun()
            c_v.markdown(f"<div class='qty-text'>{stk.get(p,0)}</div>", unsafe_allow_html=True)
            if c_p.button("➕", key=f"p_{p}"): aggiorna_stock_veloce(p, 1); st.rerun()
    
    time.sleep(15); st.rerun()

else:
    # --- CLIENTE ---
    st.title("☕ BAR PAGANO")
    if 'tavolo_scelto' not in st.session_state: st.session_state.tavolo_scelto = None
    if 'carrello' not in st.session_state: st.session_state.carrello = []

    if st.session_state.tavolo_scelto is None:
        # TASTO AGGIORNA PER IL CLIENTE (Sincronizza Stock prima di ordinare)
        if st.button("🔄 AGGIORNA DISPONIBILITÀ PRODOTTI", use_container_width=True, type="secondary"):
            st.rerun()
            
        st.write("### 🪑 Seleziona il tuo tavolo:")
        t_cols = st.columns(4)
        for i in range(1, 21):
            if t_cols[(i-1) % 4].button(f"{i}", key=f"t_{i}", use_container_width=True):
                st.session_state.tavolo_scelto = str(i)
                st.rerun()
    else:
        # Sezione Ordinazione
        col_t, col_b = st.columns([3, 1])
        col_t.markdown(f"<div class='selected-tavolo'>TAVOLO {st.session_state.tavolo_scelto}</div>", unsafe_allow_html=True)
        if col_b.button("🔄 Cambia"):
            st.session_state.tavolo_scelto = None
            st.session_state.carrello = []
            st.rerun()
        
        # Tasto aggiorna anche dentro il menù
        if st.button("🔄 AGGIORNA DISPONIBILITÀ", use_container_width=True):
            st.rerun()

        st.divider()
        cat_scelta = st.radio("Categoria:", list(MENU_DATA.keys()), horizontal=True)
        dispo = carica_stock()
        p_cols = st.columns(2)
        
        for idx, (nome, prezzo) in enumerate(MENU_DATA[cat_scelta].items()):
            qta = dispo.get(nome, 999) if cat_scelta == CAT_STOCK else 999
            with p_cols[idx % 2]:
                if st.button(f"➕ {nome}\n€{prezzo:.2f}", key=f"btn_{nome}", disabled=(cat_scelta==CAT_STOCK and qta<=0), use_container_width=True):
                    st.session_state.carrello.append({
                        "temp_id": time.time() + idx, "tavolo": st.session_state.tavolo_scelto, "prodotto": nome, "prezzo": prezzo
                    })
                    st.toast(f"Aggiunto: {nome}")
                if cat_scelta == CAT_STOCK:
                    st.markdown(f"<div class='product-info'>Disponibili: {qta}</div>", unsafe_allow_html=True)

        if st.session_state.carrello:
            st.divider()
            st.write("🛒 **IL TUO ORDINE**")
            tot_ordine = 0
            for i, item in enumerate(st.session_state.carrello):
                c1, c2 = st.columns([5, 1])
                c1.write(f"**{item['prodotto']}** (€{item['prezzo']:.2f})")
                if c2.button("❌", key=f"del_{item['temp_id']}"):
                    st.session_state.carrello.pop(i)
                    st.rerun()
                tot_ordine += item['prezzo']
            
            st.write(f"### TOTALE: €{tot_ordine:.2f}")
            if st.button("🚀 INVIA ORDINE AL BANCONE", type="primary", use_container_width=True):
                ordini_db = carica_ordini()
                for item in st.session_state.carrello:
                    item.update({
                        "nota": "", "orario": datetime.now().strftime("%H:%M"), "stato": "NO", "id_univoco": str(time.time()) + item['prodotto']
                    })
                    if "temp_id" in item: del item["temp_id"]
                    ordini_db.append(item)
                    aggiorna_stock_veloce(item['prodotto'], -1)
                salva_ordini(ordini_db)
                st.session_state.carrello = []
                st.success("Ordine inviato!")
                time.sleep(1.5)
                st.rerun()

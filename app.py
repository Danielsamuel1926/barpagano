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
    .selected-tavolo { background-color: #FF4B4B; color: white; padding: 15px; border-radius: 15px; text-align: center; font-size: 24px; font-weight: bold; margin-bottom: 20px; }
    .stButton>button[kind="secondary"] { background-color: #2E7D32 !important; color: white !important; border: none !important; }
    </style>
    """, unsafe_allow_html=True)

# --- FILE DATABASE ---
DB_FILE = "ordini_bar_pagano.csv"
STOCK_FILE = "stock_bar_pagano.csv"
MENU_FILE = "menu_personalizzato.csv"
COLONNE_ORDINI = ["id_univoco", "tavolo", "prodotto", "prezzo", "nota", "orario", "stato"]
CAT_STOCK = "Brioche e Cornetti"

# --- FUNZIONI DI CARICAMENTO "BLINDATE" ---

def carica_menu():
    intestazioni = ["categoria", "prodotto", "prezzo"]
    if not os.path.exists(MENU_FILE) or os.stat(MENU_FILE).st_size == 0:
        default_menu = [
            {"categoria": "Brioche e Cornetti", "prodotto": "Cornetto cioccolato", "prezzo": 1.50},
            {"categoria": "Bevande Calde", "prodotto": "Caffè", "prezzo": 1.00},
            {"categoria": "Bevande Fredde", "prodotto": "Acqua 0.5L", "prezzo": 1.00}
        ]
        pd.DataFrame(default_menu).to_csv(MENU_FILE, index=False)
        return pd.DataFrame(default_menu)
    try:
        return pd.read_csv(MENU_FILE)
    except Exception:
        pd.DataFrame(columns=intestazioni).to_csv(MENU_FILE, index=False)
        return pd.DataFrame(columns=intestazioni)

def carica_ordini():
    if not os.path.exists(DB_FILE) or os.stat(DB_FILE).st_size == 0:
        pd.DataFrame(columns=COLONNE_ORDINI).to_csv(DB_FILE, index=False)
        return []
    try:
        df = pd.read_csv(DB_FILE)
        return df.to_dict('records')
    except Exception:
        pd.DataFrame(columns=COLONNE_ORDINI).to_csv(DB_FILE, index=False)
        return []

def carica_stock():
    menu = carica_menu()
    prod_brioche = menu[menu['categoria'] == CAT_STOCK]['prodotto'].tolist()
    if not os.path.exists(STOCK_FILE) or os.stat(STOCK_FILE).st_size == 0:
        data = [{"prodotto": p, "quantita": 0} for p in prod_brioche]
        pd.DataFrame(data).to_csv(STOCK_FILE, index=False)
        return {p: 0 for p in prod_brioche}
    try:
        df = pd.read_csv(STOCK_FILE)
        return df.set_index('prodotto')['quantita'].to_dict()
    except Exception:
        return {p: 0 for p in prod_brioche}

# --- FUNZIONI DI SALVATAGGIO ---

def salva_ordini(lista):
    df = pd.DataFrame(lista) if lista else pd.DataFrame(columns=COLONNE_ORDINI)
    df.to_csv(DB_FILE, index=False)

def salva_nuovo_prodotto(cat, nome, prezzo):
    df = carica_menu()
    nuovo = pd.DataFrame([{"categoria": cat, "prodotto": nome, "prezzo": prezzo}])
    df = pd.concat([df, nuovo], ignore_index=True)
    df.to_csv(MENU_FILE, index=False)

def elimina_prodotto_menu(nome):
    df = carica_menu()
    df = df[df['prodotto'] != nome]
    df.to_csv(MENU_FILE, index=False)

def aggiorna_stock_veloce(nome, var):
    if os.path.exists(STOCK_FILE):
        df = pd.read_csv(STOCK_FILE)
        if nome in df['prodotto'].values:
            idx = df[df['prodotto'] == nome].index[0]
            df.at[idx, 'quantita'] = max(0, df.at[idx, 'quantita'] + var)
            df.to_csv(STOCK_FILE, index=False)

# --- LOGICA APPLICAZIONE ---
ruolo = st.query_params.get("ruolo", "tavolo")
menu_df = carica_menu()

if ruolo == "banco":
    st.title("🖥️ CONSOLE BANCONE")
    if st.button("🔄 AGGIORNA DISPLAY", use_container_width=True, type="secondary"):
        st.rerun()

    tab1, tab2, tab3, tab4 = st.tabs(["📋 ORDINI", "⚡ VENDITA RAPIDA", "📦 STOCK", "⚙️ GESTIONE LISTINO"])
    
    with tab1:
        ordini = carica_ordini()
        if not ordini: st.info("Nessun ordine attivo.")
        else:
            tavoli = sorted(set(str(o['tavolo']) for o in ordini), key=lambda x: int(x) if x.isdigit() else 0)
            cols = st.columns(3)
            for idx, t in enumerate(tavoli):
                with cols[idx % 3]:
                    with st.container(border=True):
                        st.subheader(f"🪑 Tavolo {t}")
                        tot_tavolo, tutto_servito = 0, True
                        for i, r in enumerate(ordini):
                            if str(r['tavolo']) == str(t):
                                if r['stato'] == "NO": tutto_servito = False
                                c_t, c_b = st.columns([3, 1])
                                cl = "servito" if r['stato'] == "SI" else "da-servire"
                                c_t.markdown(f"<span class='{cl}'>{r['prodotto']}</span>", unsafe_allow_html=True)
                                tot_tavolo += float(r['prezzo'])
                                if r['stato'] == "NO" and c_b.button("Fatto", key=f"sv_{t}_{i}"):
                                    ordini[i]['stato'] = "SI"; salva_ordini(ordini); st.rerun()
                        st.divider()
                        if st.button(f"PAGATO €{tot_tavolo:.2f}", key=f"pay_{t}", type="primary", use_container_width=True, disabled=not tutto_servito):
                            salva_ordini([o for o in ordini if str(o['tavolo']) != str(t)]); st.rerun()

    with tab2:
        st.write("### ⚡ Vendita Rapida")
        stk = carica_stock()
        for cat in menu_df['categoria'].unique():
            st.write(f"**{cat}**")
            prods = menu_df[menu_df['categoria'] == cat]
            cols_v = st.columns(4)
            for i, (idx_r, r) in enumerate(prods.iterrows()):
                if cols_v[i % 4].button(f"{r['prodotto']}", key=f"bs_{r['prodotto']}"):
                    if cat == CAT_STOCK: aggiorna_stock_veloce(r['prodotto'], -1)
                    st.rerun()

    with tab3:
        st.write("### 📦 Carico Magazzino")
        stk = carica_stock()
        for p, q in stk.items():
            c1, c2, c3, c4 = st.columns([3, 1, 1, 1])
            c1.write(f"**{p}**")
            if c2.button("➖", key=f"m_{p}"): aggiorna_stock_veloce(p, -1); st.rerun()
            c3.write(f"**{q}**")
            if c4.button("➕", key=f"p_{p}"): aggiorna_stock_veloce(p, 1); st.rerun()

    with tab4:
        st.subheader("⚙️ Modifica Listino Prezzi")
        with st.form("aggiunta_prodotto"):
            c1, c2, c3 = st.columns([2, 2, 1])
            cat_n = c1.selectbox("Categoria", ["Brioche e Cornetti", "Bevande Calde", "Bevande Fredde", "Altro"])
            nom_n = c2.text_input("Nome Prodotto")
            pre_n = c3.number_input("Prezzo €", min_value=0.0, step=0.1)
            if st.form_submit_button("AGGIORNA LISTINO"):
                if nom_n:
                    salva_nuovo_prodotto(cat_n, nom_n, pre_n)
                    st.success("Aggiunto!"); st.rerun()
        st.divider()
        da_canc = st.selectbox("Seleziona prodotto da cancellare", menu_df['prodotto'].tolist())
        if st.button("ELIMINA PRODOTTO", type="primary"):
            elimina_prodotto_menu(da_canc); st.rerun()

else:
    # --- CLIENTE ---
    st.title("☕ BAR PAGANO")
    if 'tavolo_scelto' not in st.session_state: st.session_state.tavolo_scelto = None
    if 'carrello' not in st.session_state: st.session_state.carrello = []

    if st.session_state.tavolo_scelto is None:
        st.write("### 🪑 Seleziona il tuo tavolo:")
        t_cols = st.columns(4)
        for i in range(1, 21):
            if t_cols[(i-1) % 4].button(f"{i}", key=f"t_{i}", use_container_width=True):
                st.session_state.tavolo_scelto = str(i); st.rerun()
    else:
        st.markdown(f"<div class='selected-tavolo'>TAVOLO {st.session_state.tavolo_scelto}</div>", unsafe_allow_html=True)
        if st.button("🔄 Cambia Tavolo"): st.session_state.tavolo_scelto = None; st.rerun()
        
        st.divider()
        categorie = menu_df['categoria'].unique()
        if len(categorie) > 0:
            scelta_cat = st.radio("Scegli:", categorie, horizontal=True)
            stk = carica_stock()
            prod_filtrati = menu_df[menu_df['categoria'] == scelta_cat]
            p_cols = st.columns(2)
            for idx, (idx_r, r) in enumerate(prod_filtrati.iterrows()):
                qta = stk.get(r['prodotto'], 999) if scelta_cat == CAT_STOCK else 999
                with p_cols[idx % 2]:
                    if st.button(f"➕ {r['prodotto']}\n€{r['prezzo']:.2f}", key=f"c_{r['prodotto']}", disabled=(qta<=0), use_container_width=True):
                        st.session_state.carrello.append({"prodotto": r['prodotto'], "prezzo": r['prezzo'], "id": time.time()})
                        st.toast("Aggiunto!")
                    if scelta_cat == CAT_STOCK: st.caption(f"Disponibili: {qta}")
        else:
            st.warning("Menù in fase di aggiornamento...")

        if st.session_state.carrello:
            st.divider()
            st.write("🛒 **IL TUO ORDINE**")
            tot = sum(item['prezzo'] for item in st.session_state.carrello)
            for i, item in enumerate(st.session_state.carrello):
                c1, c2 = st.columns([5, 1])
                c1.write(f"{item['prodotto']} (€{item['prezzo']:.2f})")
                if c2.button("❌", key=f"del_{item['id']}"):
                    st.session_state.carrello.pop(i); st.rerun()
            
            if st.button(f"🚀 INVIA ORDINE €{tot:.2f}", type="primary", use_container_width=True):
                ord_db = carica_ordini()
                for item in st.session_state.carrello:
                    nuovo_ordine = {
                        "tavolo": st.session_state.tavolo_scelto,
                        "prodotto": item['prodotto'],
                        "prezzo": item['prezzo'],
                        "nota": "",
                        "orario": datetime.now().strftime("%H:%M"),
                        "stato": "NO",
                        "id_univoco": str(time.time()) + item['prodotto']
                    }
                    ord_db.append(nuovo_ordine)
                    aggiorna_stock_veloce(item['prodotto'], -1)
                salva_ordini(ord_db); st.session_state.carrello = []; st.success("Inviato!"); time.sleep(1); st.rerun()


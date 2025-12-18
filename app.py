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
    .selected-tavolo { background-color: #FF4B4B; color: white; padding: 15px; border-radius: 15px; text-align: center; font-size: 24px; font-weight: bold; margin-bottom: 10px; }
    .stButton>button[kind="secondary"] { background-color: #2E7D32 !important; color: white !important; font-size: 18px !important; }
    </style>
    """, unsafe_allow_html=True)

# --- FILE DATABASE ---
DB_FILE = "ordini_bar_pagano.csv"
STOCK_FILE = "stock_bar_pagano.csv"
MENU_FILE = "menu_personalizzato.csv"

# --- FUNZIONI DI CARICAMENTO ---
def carica_menu():
    if not os.path.exists(MENU_FILE) or os.stat(MENU_FILE).st_size <= 2:
        return pd.DataFrame(columns=["categoria", "prodotto", "prezzo"])
    return pd.read_csv(MENU_FILE)

def carica_ordini():
    if not os.path.exists(DB_FILE) or os.stat(DB_FILE).st_size <= 2: return []
    return pd.read_csv(DB_FILE).to_dict('records')

def salva_ordini(lista):
    pd.DataFrame(lista).to_csv(DB_FILE, index=False)

def carica_stock():
    if not os.path.exists(STOCK_FILE) or os.stat(STOCK_FILE).st_size <= 2: return {}
    df = pd.read_csv(STOCK_FILE)
    return df.set_index('prodotto')['quantita'].to_dict()

def salva_stock(dizionario):
    df = pd.DataFrame(list(dizionario.items()), columns=['prodotto', 'quantita'])
    df.to_csv(STOCK_FILE, index=False)

def aggiorna_stock_veloce(nome, var):
    stk = carica_stock()
    if nome in stk:
        stk[nome] = max(0, stk[nome] + var)
        salva_stock(stk)

# --- LOGICA APP ---
ruolo = st.query_params.get("ruolo", "tavolo")
menu_df = carica_menu()

if ruolo == "banco":
    st.title("🖥️ CONSOLE BANCONE")
    if st.button("🔄 AGGIORNA ORDINI", use_container_width=True, type="secondary"): st.rerun()

    tab1, tab2, tab3, tab4 = st.tabs(["📋 ORDINI", "⚡ VENDITA RAPIDA", "📦 STOCK", "⚙️ GESTIONE LISTINO"])
    
    with tab1:
        ordini = carica_ordini()
        if not ordini: st.info("Nessun ordine.")
        else:
            tavoli = sorted(set(str(o['tavolo']) for o in ordini), key=lambda x: int(x) if x.isdigit() else 0)
            cols = st.columns(3)
            for idx, t in enumerate(tavoli):
                with cols[idx % 3]:
                    with st.container(border=True):
                        st.subheader(f"🪑 Tavolo {t}")
                        items = [o for o in ordini if str(o['tavolo']) == str(t)]
                        for r in items:
                            cx, ct, cok = st.columns([0.5, 3, 1])
                            if cx.button("❌", key=f"del_{r['id_univoco']}"):
                                ordini = [o for o in ordini if o['id_univoco'] != r['id_univoco']]
                                salva_ordini(ordini); st.rerun()
                            cl = "servito" if r['stato'] == "SI" else "da-servire"
                            ct.markdown(f"<span class='{cl}'>{r['prodotto']}</span>", unsafe_allow_html=True)
                            if r['stato'] == "NO" and cok.button("Ok", key=f"ok_{r['id_univoco']}"):
                                for o in ordini: 
                                    if o['id_univoco'] == r['id_univoco']: o['stato'] = "SI"
                                salva_ordini(ordini); st.rerun()
                        tutti_ok = all(o['stato'] == "SI" for o in items)
                        if st.button(f"PAGATO €{sum(float(o['prezzo']) for o in items):.2f}", key=f"p_{t}", type="primary", use_container_width=True, disabled=not tutti_ok):
                            salva_ordini([o for o in ordini if str(o['tavolo']) != str(t)]); st.rerun()

    with tab2:
        st.write("### ⚡ Vendita Rapida (Prodotti con Stock)")
        stk = carica_stock()
        if not stk: st.warning("Configura prima i prodotti nello Stock.")
        else:
            cols_v = st.columns(4)
            for i, (p, q) in enumerate(stk.items()):
                if cols_v[i % 4].button(f"{p}\n({q})", key=f"vr_{p}", disabled=(q <= 0)):
                    aggiorna_stock_veloce(p, -1); st.rerun()

    with tab3:
        st.write("### 📦 Gestione Stock")
        stk = carica_stock()
        # Aggiungi prodotto al magazzino dal listino
        prod_da_aggiungere = st.selectbox("Aggiungi prodotto al magazzino:", ["---"] + list(menu_df['prodotto'].unique()))
        if st.button("ABILITA GESTIONE STOCK") and prod_da_aggiungere != "---":
            stk[prod_da_aggiungere] = 0
            salva_stock(stk); st.rerun()
        
        st.divider()
        for p, q in stk.items():
            c1, c2, c3, c4, c5 = st.columns([3, 1, 1, 1, 1])
            c1.write(f"**{p}**")
            if c2.button("➖", key=f"m_{p}"): aggiorna_stock_veloce(p, -1); st.rerun()
            c3.write(f"**{q}**")
            if c4.button("➕", key=f"p_{p}"): aggiorna_stock_veloce(p, 1); st.rerun()
            if c5.button("🗑️", key=f"rm_{p}"): 
                del stk[p]; salva_stock(stk); st.rerun()

    with tab4:
        st.subheader("⚙️ Listino")
        with st.form("add"):
            c1, c2 = st.columns(2)
            cat = c2.text_input("Nuova Categoria") if (c1.selectbox("Cat Esistente", ["---"] + sorted(list(menu_df['categoria'].unique())))) == "---" else c1.selectbox("Cat Esistente", sorted(list(menu_df['categoria'].unique())))
            nome = st.text_input("Nome Prodotto")
            prezzo = st.number_input("Prezzo", step=0.1)
            if st.form_submit_button("AGGIUNGI"):
                nuovo = pd.DataFrame([{"categoria": cat, "prodotto": nome, "prezzo": prezzo}])
                pd.concat([menu_df, nuovo]).to_csv(MENU_FILE, index=False); st.rerun()
        
        for i, r in menu_df.iterrows():
            with st.expander(f"{r['categoria']} - {r['prodotto']}"):
                if st.button("ELIMINA DEFINITIVAMENTE", key=f"del_list_{i}"):
                    menu_df.drop(i).to_csv(MENU_FILE, index=False); st.rerun()

else:
    # --- CLIENTE ---
    st.title("☕ BAR PAGANO")
    if 'tavolo' not in st.session_state: st.session_state.tavolo = None
    if 'carrello' not in st.session_state: st.session_state.carrello = []
    
    if st.session_state.tavolo is None:
        t_cols = st.columns(4)
        for i in range(1, 21):
            if t_cols[(i-1) % 4].button(f"{i}", key=f"t_{i}", use_container_width=True):
                st.session_state.tavolo = str(i); st.rerun()
    else:
        st.markdown(f"<div class='selected-tavolo'>TAVOLO {st.session_state.tavolo}</div>", unsafe_allow_html=True)
        if st.button("⬅️ CAMBIA TAVOLO", use_container_width=True): st.session_state.tavolo = None; st.rerun()
        
        stk = carica_stock()
        cat_scelta = st.radio("Menu:", sorted(menu_df['categoria'].unique()), horizontal=True)
        for i, r in menu_df[menu_df['categoria'] == cat_scelta].iterrows():
            q = stk.get(r['prodotto'], None)
            txt = f"➕ {r['prodotto']} | €{r['prezzo']:.2f}" + (f" (Disp: {q})" if q is not None else "")
            if st.button(txt, key=f"c_{i}", use_container_width=True, disabled=(q is not None and q <= 0)):
                item = r.to_dict(); item['temp_id'] = time.time()+i
                st.session_state.carrello.append(item); st.toast("Aggiunto!")

        if st.session_state.carrello:
            st.write("### 🛒 Carrello")
            for idx, c in enumerate(st.session_state.carrello):
                col1, col2 = st.columns([4, 1])
                col1.write(f"{c['prodotto']} - €{c['prezzo']:.2f}")
                if col2.button("❌", key=f"rm_c_{idx}"): st.session_state.carrello.pop(idx); st.rerun()
            if st.button(f"ORDINA €{sum(float(x['prezzo']) for x in st.session_state.carrello):.2f}", type="primary", use_container_width=True):
                ords = carica_ordini()
                for c in st.session_state.carrello:
                    if c['prodotto'] in stk: aggiorna_stock_veloce(c['prodotto'], -1)
                    ords.append({"id_univoco": str(time.time())+c['prodotto'], "tavolo": st.session_state.tavolo, "prodotto": c['prodotto'], "prezzo": c['prezzo'], "stato": "NO"})
                salva_ordini(ords); st.session_state.carrello = []; st.success("Inviato!"); time.sleep(1); st.rerun()


import streamlit as st
import pandas as pd
import os
import time
from datetime import datetime

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="BAR PAGANO", page_icon="☕", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #FFFFFF; }
    [data-testid="column"] { flex: 1 1 calc(25% - 10px) !important; min-width: 70px !important; }
    div[data-testid="column"] button { width: 100% !important; font-weight: bold !important; border-radius: 12px !important; }
    .servito { color: #555555 !important; text-decoration: line-through; opacity: 0.6; font-style: italic; }
    .da-servire { color: #FFFFFF !important; font-weight: bold; font-size: 18px; }
    .selected-tavolo { background-color: #FF4B4B; color: white; padding: 15px; border-radius: 15px; text-align: center; font-size: 24px; font-weight: bold; margin-bottom: 10px; }
    .stButton>button[kind="secondary"] { background-color: #2E7D32 !important; color: white !important; }
    </style>
    """, unsafe_allow_html=True)

# --- GESTIONE DATI ---
DB_FILE = "ordini_bar_pagano.csv"
STOCK_FILE = "stock_bar_pagano.csv"
MENU_FILE = "menu_personalizzato.csv"

def inizializza_file(file, colonne):
    if not os.path.exists(file) or os.stat(file).st_size <= 2:
        pd.DataFrame(columns=colonne).to_csv(file, index=False)

inizializza_file(DB_FILE, ["id_univoco", "tavolo", "prodotto", "prezzo", "stato"])
inizializza_file(MENU_FILE, ["categoria", "prodotto", "prezzo"])
inizializza_file(STOCK_FILE, ["prodotto", "quantita"])

def carica_menu(): return pd.read_csv(MENU_FILE)
def carica_ordini(): 
    try: return pd.read_csv(DB_FILE).to_dict('records')
    except: return []
def salva_ordini(lista): pd.DataFrame(lista).to_csv(DB_FILE, index=False)
def carica_stock(): 
    df = pd.read_csv(STOCK_FILE)
    if df.empty: return {}
    return df.set_index('prodotto')['quantita'].to_dict()
def salva_stock(d): pd.DataFrame(list(d.items()), columns=['prodotto', 'quantita']).to_csv(STOCK_FILE, index=False)

# --- LOGICA ---
ruolo = st.query_params.get("ruolo", "tavolo")
menu_df = carica_menu()

if ruolo == "banco":
    st.title("🖥️ CONSOLE BANCONE")
    if st.button("🔄 AGGIORNA PAGINA", use_container_width=True, type="secondary"): st.rerun()

    tab1, tab2, tab3, tab4 = st.tabs(["📋 ORDINI", "⚡ VENDITA RAPIDA", "📦 STOCK", "⚙️ GESTIONE LISTINO"])
    
    with tab1: # TABELLA ORDINI
        ordini = carica_ordini()
        if not ordini: st.info("In attesa di nuovi ordini...")
        else:
            tavoli = sorted(set(str(o['tavolo']) for o in ordini), key=lambda x: int(x) if x.isdigit() else 0)
            cols = st.columns(3)
            for idx, t in enumerate(tavoli):
                with cols[idx % 3]:
                    with st.container(border=True):
                        st.subheader(f"🪑 Tavolo {t}")
                        items = [o for o in ordini if str(o['tavolo']) == str(t)]
                        
                        for r in items:
                            cx, ct, cok = st.columns([0.6, 3, 1])
                            # 1. ELIMINA PRODOTTO DA ORDINE (RIPENSAMENTO)
                            if cx.button("❌", key=f"del_o_{r['id_univoco']}"):
                                ordini = [o for o in ordini if o['id_univoco'] != r['id_univoco']]
                                salva_ordini(ordini); st.rerun()
                                
                            cl = "servito" if r['stato'] == "SI" else "da-servire"
                            ct.markdown(f"<span class='{cl}'>{r['prodotto']}</span>", unsafe_allow_html=True)
                            
                            if r['stato'] == "NO" and cok.button("Ok", key=f"ok_{r['id_univoco']}"):
                                for o in ordini: 
                                    if o['id_univoco'] == r['id_univoco']: o['stato'] = "SI"
                                salva_ordini(ordini); st.rerun()
                        
                        st.divider()
                        tutti_ok = all(o['stato'] == "SI" for o in items)
                        tot = sum(float(o['prezzo']) for o in items)
                        # 2. TASTO PAGATO VINCOLATO AL SERVIZIO
                        if st.button(f"PAGATO €{tot:.2f}", key=f"pay_{t}", type="primary", use_container_width=True, disabled=not tutti_ok):
                            salva_ordini([o for o in ordini if str(o['tavolo']) != str(t)]); st.rerun()

    with tab2: # VENDITA RAPIDA
        stk = carica_stock()
        if not stk: st.warning("Aggiungi prodotti nello Stock per vederli qui.")
        else:
            cols_v = st.columns(4)
            for i, (p, q) in enumerate(stk.items()):
                if cols_v[i % 4].button(f"{p}\n({q})", key=f"vr_{p}", disabled=(q <= 0)):
                    stk[p] = max(0, q - 1); salva_stock(stk); st.rerun()

    with tab3: # STOCK
        st.write("### 📦 Carico/Scarico Magazzino")
        stk = carica_stock()
        nuovo_s = st.selectbox("Seleziona dal listino:", ["---"] + list(menu_df['prodotto'].unique()))
        if st.button("ABILITA MONITORAGGIO") and nuovo_s != "---":
            stk[nuovo_s] = 0; salva_stock(stk); st.rerun()
        st.divider()
        for p, q in stk.items():
            c1, c2, c3, c4, c5 = st.columns([3, 1, 1, 1, 1])
            c1.write(f"**{p}**")
            if c2.button("➖", key=f"sm_{p}"): stk[p] = max(0, q-1); salva_stock(stk); st.rerun()
            c3.write(f"**{q}**")
            if c4.button("➕", key=f"sp_{p}"): stk[p] = q+1; salva_stock(stk); st.rerun()
            if c5.button("🗑️", key=f"sdel_{p}"): del stk[p]; salva_stock(stk); st.rerun()

    with tab4: # LISTINO
        st.subheader("⚙️ Gestione Listino")
        with st.form("add_list", clear_on_submit=True):
            c1, c2 = st.columns(2)
            cat = c2.text_input("Nuova Categoria") if (c1.selectbox("Categoria", ["---"] + sorted(list(menu_df['categoria'].unique())))) == "---" else c1.selectbox("Categoria", sorted(list(menu_df['categoria'].unique())))
            nome = st.text_input("Nome Prodotto")
            prez = st.number_input("Prezzo €", min_value=0.0, step=0.1)
            if st.form_submit_button("AGGIUNGI PRODOTTO"):
                if cat != "---" and nome:
                    nuovo = pd.DataFrame([{"categoria": cat, "prodotto": nome, "prezzo": prez}])
                    pd.concat([menu_df, nuovo]).to_csv(MENU_FILE, index=False); st.rerun()
        st.divider()
        for i, r in menu_df.iterrows():
            with st.expander(f"{r['categoria']} - {r['prodotto']} (€{r['prezzo']})"):
                # 3. ELIMINAZIONE DEFINITIVA PRODOTTO
                if st.button("🗑️ ELIMINA DEFINITIVAMENTE", key=f"ldel_{i}"):
                    menu_df.drop(i).to_csv(MENU_FILE, index=False); st.rerun()

else: # --- CLIENTE ---
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
        # 4. TASTO CAMBIA TAVOLO
        if st.button("⬅️ CAMBIA TAVOLO", use_container_width=True): 
            st.session_state.tavolo = None
            st.rerun()
        
        stk = carica_stock()
        if not menu_df.empty:
            cat_s = st.radio("Menu:", sorted(menu_df['categoria'].unique()), horizontal=True)
            for i, r in menu_df[menu_df['categoria'] == cat_s].iterrows():
                q = stk.get(r['prodotto'], None)
                label = f"➕ {r['prodotto']} | €{r['prezzo']:.2f}" + (f" (Disp: {q})" if q is not None else "")
                if st.button(label, key=f"c_{i}", use_container_width=True, disabled=(q is not None and q <= 0)):
                    st.session_state.carrello.append({"prodotto": r['prodotto'], "prezzo": r['prezzo'], "id": time.time()+i})
                    st.toast(f"{r['prodotto']} aggiunto!")

        if st.session_state.carrello:
            st.divider(); st.write("### 🛒 Carrello")
            for idx, c in enumerate(st.session_state.carrello):
                col1, col2 = st.columns([4, 1])
                col1.write(f"{c['prodotto']} - €{c['prezzo']:.2f}")
                if col2.button("❌", key=f"rc_{idx}"): st.session_state.carrello.pop(idx); st.rerun()
            
            if st.button(f"🚀 INVIA ORDINE €{sum(x['prezzo'] for x in st.session_state.carrello):.2f}", type="primary", use_container_width=True):
                ords = carica_ordini()
                for c in st.session_state.carrello:
                    if c['prodotto'] in stk: 
                        stk[c['prodotto']] = max(0, stk[c['prodotto']] - 1)
                        salva_stock(stk)
                    ords.append({"id_univoco": str(time.time())+c['prodotto'], "tavolo": st.session_state.tavolo, "prodotto": c['prodotto'], "prezzo": c['prezzo'], "stato": "NO"})
                salva_ordini(ords); st.session_state.carrello = []; st.success("Inviato!"); time.sleep(1); st.rerun()


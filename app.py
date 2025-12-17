import streamlit as st
import pandas as pd
import os
import time
from datetime import datetime

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="BAR PAGANO", page_icon="☕", layout="wide")

# File per i dati
DB_FILE = "ordini_bar_pagano.csv"
STOCK_FILE = "stock_bar_pagano.csv"
MENU_FILE = "menu_personalizzato.csv"
COLONNE_ORDINI = ["id_univoco", "tavolo", "prodotto", "prezzo", "nota", "orario", "stato"]

# Categoria speciale per lo stock
CAT_STOCK = "Brioche e Cornetti"

# --- FUNZIONI DI GESTIONE MENU (LISTINO) ---
def carica_menu():
    if not os.path.exists(MENU_FILE) or os.stat(MENU_FILE).st_size == 0:
        # Menu di default iniziale
        default_menu = [
            {"categoria": "Brioche e Cornetti", "prodotto": "Cornetto cioccolato", "prezzo": 1.50},
            {"categoria": "Bevande Calde", "prodotto": "Caffè", "prezzo": 1.00},
            {"categoria": "Bevande Fredde", "prodotto": "Acqua 0.5L", "prezzo": 1.00}
        ]
        pd.DataFrame(default_menu).to_csv(MENU_FILE, index=False)
    return pd.read_csv(MENU_FILE)

def salva_nuovo_prodotto(cat, nome, prezzo):
    df = carica_menu()
    nuovo = pd.DataFrame([{"categoria": cat, "prodotto": nome, "prezzo": prezzo}])
    df = pd.concat([df, nuovo], ignore_index=True)
    df.to_csv(MENU_FILE, index=False)

def elimina_prodotto_menu(nome):
    df = carica_menu()
    df = df[df['prodotto'] != nome]
    df.to_csv(MENU_FILE, index=False)

# --- FUNZIONI DATI ORDINI E STOCK ---
def carica_ordini():
    if not os.path.exists(DB_FILE) or os.stat(DB_FILE).st_size == 0:
        pd.DataFrame(columns=COLONNE_ORDINI).to_csv(DB_FILE, index=False)
        return []
    return pd.read_csv(DB_FILE).to_dict('records')

def salva_ordini(lista):
    df = pd.DataFrame(lista) if lista else pd.DataFrame(columns=COLONNE_ORDINI)
    df.to_csv(DB_FILE, index=False)

def carica_stock():
    menu = carica_menu()
    prodotti_brioche = menu[menu['categoria'] == CAT_STOCK]['prodotto'].tolist()
    if not os.path.exists(STOCK_FILE) or os.stat(STOCK_FILE).st_size == 0:
        data = [{"prodotto": n, "quantita": 0} for n in prodotti_brioche]
        pd.DataFrame(data).to_csv(STOCK_FILE, index=False)
        return {n: 0 for n in prodotti_brioche}
    df_stk = pd.read_csv(STOCK_FILE)
    # Assicurati che nuovi prodotti in "Brioche" siano nel file stock
    for p in prodotti_brioche:
        if p not in df_stk['prodotto'].values:
            nuovo_s = pd.DataFrame([{"prodotto": p, "quantita": 0}])
            df_stk = pd.concat([df_stk, nuovo_s], ignore_index=True)
    df_stk.to_csv(STOCK_FILE, index=False)
    return df_stk.set_index('prodotto')['quantita'].to_dict()

def aggiorna_stock_veloce(nome, var):
    df = pd.read_csv(STOCK_FILE)
    if nome in df['prodotto'].values:
        idx = df[df['prodotto'] == nome].index[0]
        df.at[idx, 'quantita'] = max(0, df.at[idx, 'quantita'] + var)
        df.to_csv(STOCK_FILE, index=False)

# --- INTERFACCIA ---
ruolo = st.query_params.get("ruolo", "tavolo")
menu_df = carica_menu()

if ruolo == "banco":
    st.title("🖥️ CONSOLE BANCONE")
    
    if st.button("🔄 AGGIORNA TUTTO", use_container_width=True, type="secondary"):
        st.rerun()

    tab1, tab2, tab3, tab4 = st.tabs(["📋 ORDINI", "⚡ VENDITA RAPIDA", "📦 STOCK", "⚙️ GESTIONE LISTINO"])
    
    with tab1:
        ordini = carica_ordini()
        if not ordini: st.info("In attesa di ordini...")
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
                                c_t.write(f"{'✅' if r['stato']=='SI' else '⏳'} {r['prodotto']}")
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
            for i, r in prods.iterrows():
                q = stk.get(r['prodotto'], "∞") if cat == CAT_STOCK else "∞"
                if cols_v[i % 4].button(f"{r['prodotto']}\n({q})", key=f"bs_{r['prodotto']}"):
                    if cat == CAT_STOCK: aggiorna_stock_veloce(r['prodotto'], -1)
                    st.rerun()

    with tab3:
        st.write("### 📦 Carico Magazzino Brioche")
        stk = carica_stock()
        for p, q in stk.items():
            c1, c2, c3, c4 = st.columns([3, 1, 1, 1])
            c1.write(f"**{p}**")
            if c2.button("➖", key=f"m_{p}"): aggiorna_stock_veloce(p, -1); st.rerun()
            c3.markdown(f"<div style='text-align:center;font-size:20px;'>{q}</div>", unsafe_allow_html=True)
            if c4.button("➕", key=f"p_{p}"): aggiorna_stock_veloce(p, 1); st.rerun()

    with tab4:
        st.subheader("🆕 Aggiungi Prodotto al Listino")
        with st.form("nuovo_prodotto"):
            nuova_cat = st.selectbox("Categoria", ["Brioche e Cornetti", "Bevande Calde", "Bevande Fredde", "Altro"])
            nuovo_nome = st.text_input("Nome Prodotto")
            nuovo_prezzo = st.number_input("Prezzo (€)", min_value=0.0, step=0.10)
            if st.form_submit_button("SALVA NEL LISTINO"):
                if nuovo_nome:
                    salva_nuovo_prodotto(nuova_cat, nuovo_nome, nuovo_prezzo)
                    st.success("Prodotto aggiunto!"); st.rerun()
        
        st.divider()
        st.subheader("🗑️ Elimina Prodotto")
        prod_da_elim = st.selectbox("Seleziona prodotto da rimuovere", menu_df['prodotto'].tolist())
        if st.button("ELIMINA DEFINITIVAMENTE", type="primary"):
            elimina_prodotto_menu(prod_da_elim)
            st.warning("Prodotto rimosso!"); st.rerun()

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
        st.subheader(f"TAVOLO {st.session_state.tavolo_scelto}")
        if st.button("🔄 Cambia Tavolo"): st.session_state.tavolo_scelto = None; st.rerun()
        
        st.divider()
        categorie = menu_df['categoria'].unique()
        scelta_cat = st.radio("Cosa desideri?", categorie, horizontal=True)
        
        stk = carica_stock()
        prod_filtrati = menu_df[menu_df['categoria'] == scelta_cat]
        p_cols = st.columns(2)
        
        for idx, r in prod_filtrati.reset_index().iterrows():
            qta = stk.get(r['prodotto'], 999) if scelta_cat == CAT_STOCK else 999
            with p_cols[idx % 2]:
                btn_label = f"➕ {r['prodotto']}\n€{r['prezzo']:.2f}"
                if st.button(btn_label, key=f"c_{r['prodotto']}", disabled=(qta<=0), use_container_width=True):
                    st.session_state.carrello.append({"prodotto": r['prodotto'], "prezzo": r['prezzo'], "id": time.time()})
                    st.toast(f"Aggiunto: {r['prodotto']}")
                if scelta_cat == CAT_STOCK: st.caption(f"Disponibili: {qta}")

        if st.session_state.carrello:
            st.divider()
            st.write("🛒 **IL TUO ORDINE**")
            tot = 0
            for i, item in enumerate(st.session_state.carrello):
                c1, c2 = st.columns([4, 1])
                c1.write(f"{item['prodotto']} - €{item['prezzo']:.2f}")
                if c2.button("❌", key=f"del_{item['id']}"):
                    st.session_state.carrello.pop(i); st.rerun()
                tot += item['prezzo']
            
            if st.button(f"🚀 INVIA ORDINE (€{tot:.2f})", type="primary", use_container_width=True):
                ord_db = carica_ordini()
                for item in st.session_state.carrello:
                    item.update({"tavolo": st.session_state.tavolo_scelto, "stato": "NO", "orario": datetime.now().strftime("%H:%M"), "id_univoco": str(time.time())+item['prodotto']})
                    ord_db.append(item)
                    if scelta_cat == CAT_STOCK: aggiorna_stock_veloce(item['prodotto'], -1)
                salva_ordini(ord_db); st.session_state.carrello = []; st.success("Inviato!"); time.sleep(1); st.rerun()

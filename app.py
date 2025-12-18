import streamlit as st
import pandas as pd
import os
import time
from datetime import datetime
import streamlit.components.v1 as components

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="BAR PAGANO - POS", page_icon="☕", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0E1117; color: #FFFFFF; }
    .servito { color: #555555 !important; text-decoration: line-through; opacity: 0.6; font-style: italic; }
    .da-servire { color: #FFFFFF !important; font-weight: bold; font-size: 18px; }
    .selected-tavolo { background-color: #FF4B4B; color: white; padding: 15px; border-radius: 15px; text-align: center; font-size: 24px; font-weight: bold; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

DB_FILE = "ordini_bar_pagano.csv"
MENU_FILE = "menu_personalizzato.csv"
STOCK_FILE = "stock_bar_pagano.csv"
COLONNE_ORDINI = ["id_univoco", "tavolo", "prodotto", "prezzo", "orario", "stato"]

# --- FUNZIONI DATA ---

def carica_menu():
    if not os.path.exists(MENU_FILE) or os.stat(MENU_FILE).st_size <= 2:
        df = pd.DataFrame([
            {"categoria": "Brioche", "prodotto": "Cornetto Semplice", "prezzo": 1.20},
            {"categoria": "Brioche", "prodotto": "Cornetto Crema", "prezzo": 1.30},
            {"categoria": "Caffetteria", "prodotto": "Caffè", "prezzo": 1.00}
        ])
        df.to_csv(MENU_FILE, index=False)
        return df
    return pd.read_csv(MENU_FILE)

def carica_ordini():
    if not os.path.exists(DB_FILE) or os.stat(DB_FILE).st_size <= 2:
        return []
    try:
        return pd.read_csv(DB_FILE).to_dict('records')
    except:
        return []

def salva_ordini(lista):
    pd.DataFrame(lista if lista else columns=COLONNE_ORDINI).to_csv(DB_FILE, index=False)

def carica_stock():
    if not os.path.exists(STOCK_FILE) or os.stat(STOCK_FILE).st_size <= 2:
        menu = carica_menu()
        stock = menu[menu['categoria'].isin(['Brioche', 'Cornetti'])].copy()
        stock['quantita'] = 20
        stock.to_csv(STOCK_FILE, index=False)
        return stock
    return pd.read_csv(STOCK_FILE)

# --- FUNZIONE STAMPA ---
def genera_stampa(tavolo, prodotti, totale):
    ora = datetime.now().strftime("%d/%m/%Y %H:%M")
    righe = "".join([f"<tr><td>{p['prodotto']}</td><td style='text-align:right'>€{float(p['prezzo']):.2f}</td></tr>" for p in prodotti])
    html = f"""
    <div id="s" style="font-family:monospace; width:80mm; color:black; background:white; padding:10px;">
        <h2 style="text-align:center;">BAR PAGANO</h2>
        <p>Tavolo: {tavolo} - {ora}</p><hr>
        <table style="width:100%;">{righe}</table><hr>
        <h3 style="text-align:right;">TOTALE: €{totale:.2f}</h3>
    </div>
    <script>
        var w = window.open('', '_blank');
        w.document.write('<html><body>' + document.getElementById('s').outerHTML + '</body></html>');
        w.document.close();
        setTimeout(function(){{ w.print(); w.close(); }}, 500);
    </script>
    """
    components.html(html, height=0)

# --- LOGICA ---
ruolo = st.query_params.get("ruolo", "tavolo")
menu_df = carica_menu()

if ruolo == "banco":
    st.title("🖥️ CONSOLE BANCONE")
    t1, t2, t3 = st.tabs(["📋 ORDINI", "🥐 VENDITA RAPIDA (STOCK)", "⚙️ MODIFICA LISTINO"])
    
    with t1:
        ordini = carica_ordini()
        if not ordini: st.info("Nessun ordine attivo.")
        else:
            tavoli = sorted(list(set(str(o['tavolo']) for o in ordini)))
            cols = st.columns(3)
            for idx, t in enumerate(tavoli):
                with cols[idx % 3]:
                    with st.container(border=True):
                        items = [o for o in ordini if str(o['tavolo']) == t]
                        tot = sum(float(i['prezzo']) for i in items)
                        st.subheader(f"Tavolo {t}")
                        for r in items:
                            cl = "servito" if r['stato'] == "SI" else "da-servire"
                            st.markdown(f"<div class='{cl}'>{r['prodotto']}</div>", unsafe_allow_html=True)
                        if st.button(f"PAGA €{tot:.2f}", key=f"p_{t}", use_container_width=True):
                            genera_stampa(t, items, tot)
                            salva_ordini([o for o in ordini if str(o['tavolo']) != t])
                            st.rerun()

    with t2:
        st.subheader("⚡ Solo Brioche & Cornetti")
        stock_df = carica_stock()
        # Filtriamo solo brioche e cornetti
        brioche_stock = stock_df[stock_df['categoria'].isin(['Brioche', 'Cornetti'])]
        
        cols_s = st.columns(2)
        for i, (idx, r) in enumerate(brioche_stock.iterrows()):
            with cols_s[i % 2]:
                with st.container(border=True):
                    st.write(f"**{r['prodotto']}**")
                    st.write(f"Disp: {r['quantita']}")
                    if st.button(f"VENDI €{r['prezzo']}", key=f"v_{idx}"):
                        stock_df.at[idx, 'quantita'] = max(0, r['quantita'] - 1)
                        stock_df.to_csv(STOCK_FILE, index=False)
                        st.toast(f"Venduto {r['prodotto']}")
                        time.sleep(0.5)
                        st.rerun()

    with t3:
        st.subheader("📝 Modifica Prodotti Esistenti")
        for i, row in menu_df.iterrows():
            with st.expander(f"Modifica: {row['prodotto']} ({row['categoria']})"):
                with st.form(f"f_{i}"):
                    new_cat = st.text_input("Categoria", row['categoria'])
                    new_prod = st.text_input("Nome", row['prodotto'])
                    new_prez = st.number_input("Prezzo €", value=float(row['prezzo']), step=0.1)
                    c1, c2 = st.columns(2)
                    if c1.form_submit_button("SALVA MODIFICHE"):
                        menu_df.at[i, 'categoria'] = new_cat
                        menu_df.at[i, 'prodotto'] = new_prod
                        menu_df.at[i, 'prezzo'] = new_prez
                        menu_df.to_csv(MENU_FILE, index=False)
                        st.rerun()
                    if c2.form_submit_button("ELIMINA PRODOTTO", type="primary"):
                        menu_df.drop(i).to_csv(MENU_FILE, index=False)
                        st.rerun()

        st.divider()
        st.subheader("➕ Aggiungi Nuovo Prodotto")
        with st.form("nuovo_p"):
            n_cat = st.text_input("Categoria (es: Brioche, Caffetteria)")
            n_nome = st.text_input("Nome Prodotto")
            n_prez = st.number_input("Prezzo €", min_value=0.0, step=0.1)
            if st.form_submit_button("AGGIUNGI"):
                if n_nome:
                    nuovo = pd.DataFrame([{"categoria": n_cat, "prodotto": n_nome, "prezzo": n_prez}])
                    pd.concat([menu_df, nuovo], ignore_index=True).to_csv(MENU_FILE, index=False)
                    st.rerun()

else:
    # --- CLIENTE ---
    st.title("☕ BAR PAGANO")
    if 'tavolo' not in st.session_state: st.session_state.tavolo = None
    if 'carrello' not in st.session_state: st.session_state.carrello = []

    if st.session_state.tavolo is None:
        t_cols = st.columns(5)
        for i in range(1, 11):
            if t_cols[(i-1)%5].button(f"Tavolo {i}", use_container_width=True):
                st.session_state.tavolo = str(i); st.rerun()
    else:
        st.markdown(f"<div class='selected-tavolo'>TAVOLO {st.session_state.tavolo}</div>", unsafe_allow_html=True)
        if st.button("⬅️ Cambia Tavolo"): st.session_state.tavolo = None; st.rerun()
        
        scelta = st.radio("Scegli categoria:", menu_df['categoria'].unique(), horizontal=True)
        items = menu_df[menu_df['categoria'] == scelta]
        p_cols = st.columns(2)
        for i, (idx, r) in enumerate(items.iterrows()):
            with p_cols[i % 2]:
                if st.button(f"{r['prodotto']}\n€{r['prezzo']}", key=f"c_{idx}", use_container_width=True):
                    st.session_state.carrello.append(r.to_dict())
                    st.toast("Aggiunto!")

        if st.session_state.carrello:
            st.divider()
            tot_c = sum(c['prezzo'] for c in st.session_state.carrello)
            if st.button(f"INVIA ORDINE €{tot_c:.2f}", type="primary", use_container_width=True):
                ord_db = carica_ordini()
                for c in st.session_state.carrello:
                    ord_db.append({
                        "id_univoco": f"{time.time()}_{c['prodotto']}", "tavolo": st.session_state.tavolo,
                        "prodotto": c['prodotto'], "prezzo": c['prezzo'], "orario": datetime.now().strftime("%H:%M"), "stato": "NO"
                    })
                salva_ordini(ord_db)
                st.session_state.carrello = []
                st.success("Inviato!")
                time.sleep(1); st.rerun()



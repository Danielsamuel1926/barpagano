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

# --- FUNZIONI DI GESTIONE DATI ---

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
    if lista:
        df = pd.DataFrame(lista)
    else:
        df = pd.DataFrame(columns=COLONNE_ORDINI)
    df.to_csv(DB_FILE, index=False)

def carica_stock():
    if not os.path.exists(STOCK_FILE) or os.stat(STOCK_FILE).st_size <= 2:
        menu = carica_menu()
        # Filtro iniziale per lo stock
        stock = menu[menu['categoria'].str.contains('Brioche|Cornetti', case=False, na=False)].copy()
        stock['quantita'] = 0
        stock.to_csv(STOCK_FILE, index=False)
        return stock
    return pd.read_csv(STOCK_FILE)

# --- SISTEMA DI STAMPA ---
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
        w.document.write('<html><body style="margin:0;">' + document.getElementById('s').outerHTML + '</body></html>');
        w.document.close();
        setTimeout(function(){{ w.print(); w.close(); }}, 500);
    </script>
    """
    components.html(html, height=0)

# --- LOGICA INTERFACCIA ---
ruolo = st.query_params.get("ruolo", "tavolo")
menu_df = carica_menu()

if ruolo == "banco":
    st.title("🖥️ CONSOLE BANCONE")
    t1, t2, t3 = st.tabs(["📋 ORDINI", "🥐 VENDITA RAPIDA & STOCK", "⚙️ MODIFICA LISTINO"])
    
    with t1:
        ordini = carica_ordini()
        if not ordini: st.info("In attesa di ordini...")
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
        # Visualizziamo solo le categorie richieste
        brioche_stock = stock_df[stock_df['categoria'].str.contains('Brioche|Cornetti', case=False, na=False)]
        
        if brioche_stock.empty:
            st.warning("Nessun prodotto trovato nelle categorie Brioche o Cornetti.")
        
        for i, (idx, r) in enumerate(brioche_stock.iterrows()):
            c1, c2, c3 = st.columns([3, 2, 2])
            c1.write(f"**{r['prodotto']}** (Disponibili: {r['quantita']})")
            if c2.button("➕ CARICO +10", key=f"add_{idx}"):
                stock_df.at[idx, 'quantita'] += 10
                stock_df.to_csv(STOCK_FILE, index=False)
                st.rerun()
            if c3.button(f"⚡ VENDI (€{r['prezzo']})", key=f"v_{idx}", disabled=r['quantita'] <= 0):
                stock_df.at[idx, 'quantita'] = max(0, r['quantita'] - 1)
                stock_df.to_csv(STOCK_FILE, index=False)
                st.toast(f"Venduto {r['prodotto']}!")
                time.sleep(0.5)
                st.rerun()

    with t3:
        st.subheader("📝 Modifica Listino")
        for i, row in menu_df.iterrows():
            with st.expander(f"Modifica: {row['prodotto']} ({row['categoria']})"):
                with st.form(f"f_{i}"):
                    c_cat = st.text_input("Categoria", row['categoria'])
                    c_prod = st.text_input("Nome", row['prodotto'])
                    c_prez = st.number_input("Prezzo €", value=float(row['prezzo']), step=0.1)
                    col1, col2 = st.columns(2)
                    if col1.form_submit_button("AGGIORNA"):
                        menu_df.at[i, 'categoria'] = c_cat
                        menu_df.at[i, 'prodotto'] = c_prod
                        menu_df.at[i, 'prezzo'] = c_prez
                        menu_df.to_csv(MENU_FILE, index=False)
                        st.success("Modificato!")
                        st.rerun()
                    if col2.form_submit_button("ELIMINA", type="primary"):
                        menu_df.drop(i).reset_index(drop=True).to_csv(MENU_FILE, index=False)
                        st.rerun()

        st.divider()
        st.subheader("➕ Aggiungi Nuovo")
        with st.form("new"):
            n_cat = st.text_input("Categoria (es: Brioche, Caffetteria, Bevande)")
            n_nom = st.text_input("Nome Prodotto")
            n_pre = st.number_input("Prezzo €", min_value=0.0, step=0.1)
            if st.form_submit_button("AGGIUNGI"):
                if n_nom and n_cat:
                    nuovo = pd.DataFrame([{"categoria": n_cat, "prodotto": n_nom, "prezzo": n_pre}])
                    pd.concat([menu_df, nuovo], ignore_index=True).to_csv(MENU_FILE, index=False)
                    st.rerun()

else:
    # --- CLIENTE ---
    st.title("☕ BENVENUTO AL BAR PAGANO")
    if 'tavolo' not in st.session_state: st.session_state.tavolo = None
    if 'carrello' not in st.session_state: st.session_state.carrello = []

    if st.session_state.tavolo is None:
        t_cols = st.columns(4)
        for i in range(1, 13):
            if t_cols[(i-1)%4].button(f"Tavolo {i}", use_container_width=True):
                st.session_state.tavolo = str(i); st.rerun()
    else:
        st.markdown(f"<div class='selected-tavolo'>TAVOLO {st.session_state.tavolo}</div>", unsafe_allow_html=True)
        if st.button("⬅️ Cambia Tavolo"): st.session_state.tavolo = None; st.rerun()
        
        st.write("### Scegli cosa ordinare:")
        cats = menu_df['categoria'].unique()
        scelta = st.radio("Sezioni:", cats, horizontal=True)
        
        items = menu_df[menu_df['categoria'] == scelta]
        p_cols = st.columns(2)
        for i, (idx, r) in enumerate(items.iterrows()):
            with p_cols[i % 2]:
                if st.button(f"{r['prodotto']}\n€{r['prezzo']:.2f}", key=f"c_{idx}", use_container_width=True):
                    st.session_state.carrello.append(r.to_dict())
                    st.toast(f"Aggiunto {r['prodotto']}")

        if st.session_state.carrello:
            st.divider()
            tot_c = sum(c['prezzo'] for c in st.session_state.carrello)
            st.write(f"**Elementi nel carrello:** {len(st.session_state.carrello)}")
            if st.button(f"🚀 INVIA ORDINE €{tot_c:.2f}", type="primary", use_container_width=True):
                ord_db = carica_ordini()
                for c in st.session_state.carrello:
                    ord_db.append({
                        "id_univoco": f"{time.time()}_{c['prodotto']}", "tavolo": st.session_state.tavolo,
                        "prodotto": c['prodotto'], "prezzo": c['prezzo'], "orario": datetime.now().strftime("%H:%M"), "stato": "NO"
                    })
                salva_ordini(ord_db)
                st.session_state.carrello = []
                st.success("Ordine Inviato!")
                time.sleep(1); st.rerun()


import streamlit as st
import pandas as pd
import os
import time
from datetime import datetime
import streamlit.components.v1 as components

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
    /* STILE TASTO AGGIORNA VERDE - FORZATO */
    .stButton>button.aggiorna-btn { 
        background-color: #2E7D32 !important; 
        color: white !important; 
        font-size: 24px !important; 
        height: 60px !important; 
        border: 2px solid white !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- FILE DATABASE ---
DB_FILE = "ordini_bar_pagano.csv"
STOCK_FILE = "stock_bar_pagano.csv"
MENU_FILE = "menu_personalizzato.csv"
COLONNE_ORDINI = ["id_univoco", "tavolo", "prodotto", "prezzo", "nota", "orario", "stato"]

# --- FUNZIONI DI SUPPORTO ---
def suona_notifica():
    audio_url = "https://www.soundjay.com/buttons/sounds/button-3.mp3"
    components.html(f"<audio autoplay><source src='{audio_url}' type='audio/mp3'></audio>", height=0)

def stampa_scontrino(tavolo, prodotti, totale):
    ora = datetime.now().strftime("%d/%m/%Y %H:%M")
    righe = "".join([f"<tr><td>{p['prodotto']}</td><td style='text-align:right'>€{float(p['prezzo']):.2f}</td></tr>" for p in prodotti])
    html = f"""
    <div id="s" style="font-family:monospace; width:75mm; color:black; background:white; padding:10px;">
        <h2 style="text-align:center;">BAR PAGANO</h2><hr>
        <p><b>TAVOLO {tavolo}</b><br>{ora}</p><hr>
        <table style="width:100%;">{righe}</table><hr>
        <h3 style="text-align:right;">TOTALE: €{totale:.2f}</h3>
    </div>
    <script>
        var w = window.open('', '', 'width=600,height=600');
        w.document.write('<html><body>' + document.getElementById('s').outerHTML + '</body></html>');
        w.document.close();
        setTimeout(function(){{ w.print(); w.close(); }}, 700);
    </script>
    """
    components.html(html, height=0)

def carica_menu():
    if not os.path.exists(MENU_FILE) or os.stat(MENU_FILE).st_size <= 2:
        df = pd.DataFrame([{"categoria": "Caffetteria", "prodotto": "Caffè", "prezzo": 1.00}])
        df.to_csv(MENU_FILE, index=False)
        return df
    return pd.read_csv(MENU_FILE)

def carica_ordini():
    if not os.path.exists(DB_FILE) or os.stat(DB_FILE).st_size <= 2: return []
    try: return pd.read_csv(DB_FILE).to_dict('records')
    except: return []

def salva_ordini(lista):
    df = pd.DataFrame(lista) if lista else pd.DataFrame(columns=COLONNE_ORDINI)
    df.to_csv(DB_FILE, index=False)

def carica_stock():
    menu = carica_menu()
    mask = menu['categoria'].str.contains('Brioche|Cornetti', case=False, na=False)
    prod_con_stock = menu[mask]['prodotto'].unique().tolist()
    if not os.path.exists(STOCK_FILE) or os.stat(STOCK_FILE).st_size <= 2:
        df = pd.DataFrame([{"prodotto": p, "quantita": 0} for p in prod_con_stock])
        df.to_csv(STOCK_FILE, index=False)
        return df.set_index('prodotto')['quantita'].to_dict()
    df = pd.read_csv(STOCK_FILE)
    return df.set_index('prodotto')['quantita'].to_dict()

def aggiorna_stock_veloce(nome, var):
    if os.path.exists(STOCK_FILE):
        df = pd.read_csv(STOCK_FILE)
        if nome in df['prodotto'].values:
            idx = df[df['prodotto'] == nome].index[0]
            df.at[idx, 'quantita'] = max(0, df.at[idx, 'quantita'] + var)
            df.to_csv(STOCK_FILE, index=False)

# --- LOGICA APP ---
ruolo = st.query_params.get("ruolo", "tavolo")
menu_df = carica_menu()

if ruolo == "banco":
    st.title("🖥️ CONSOLE BANCONE")
    
    # 1. IL TASTO AGGIORNA MANUALE (POSIZIONE FISSA)
    if st.button("🔄 AGGIORNA PAGINA", use_container_width=True, type="secondary"):
        st.rerun()

    st.divider()

    # 2. AUTO-REFRESH SILENZIOSO (OGNI 3 SECONDI)
    if "last_refresh" not in st.session_state:
        st.session_state.last_refresh = time.time()
    
    current_time = time.time()
    if current_time - st.session_state.last_refresh > 3:
        st.session_state.last_refresh = current_time
        st.rerun()

    tab1, tab2, tab3, tab4 = st.tabs(["📋 ORDINI", "⚡ VENDITA RAPIDA", "📦 STOCK", "⚙️ GESTIONE LISTINO"])
    
    with tab1:
        ordini = carica_ordini()
        if not ordini: st.info("In attesa di nuovi ordini...")
        else:
            tavoli = sorted(set(str(o['tavolo']) for o in ordini), key=lambda x: int(x) if x.isdigit() else 0)
            cols = st.columns(3)
            for idx, t in enumerate(tavoli):
                with cols[idx % 3]:
                    with st.container(border=True):
                        st.subheader(f"🪑 Tavolo {t}")
                        items_tavolo = [o for o in ordini if str(o['tavolo']) == str(t)]
                        tot_tavolo = sum(float(o['prezzo']) for o in items_tavolo)
                        for r in items_tavolo:
                            c_t, c_b = st.columns([3, 1])
                            cl = "servito" if r['stato'] == "SI" else "da-servire"
                            c_t.markdown(f"<span class='{cl}'>{r['prodotto']}</span>", unsafe_allow_html=True)
                            if r['stato'] == "NO" and c_b.button("Ok", key=f"sv_{r['id_univoco']}"):
                                for o in ordini: 
                                    if o['id_univoco'] == r['id_univoco']: o['stato'] = "SI"
                                salva_ordini(ordini); st.rerun()
                        st.divider()
                        if st.button(f"PAGATO €{tot_tavolo:.2f}", key=f"pay_{t}", type="primary", use_container_width=True):
                            stampa_scontrino(t, items_tavolo, tot_tavolo)
                            salva_ordini([o for o in ordini if str(o['tavolo']) != str(t)]); st.rerun()

    with tab2:
        st.write("### ⚡ Vendita Rapida")
        stk = carica_stock()
        brioche_prods = menu_df[menu_df['categoria'].str.contains('Brioche|Cornetti', case=False, na=False)]
        cols_v = st.columns(4)
        for i, (idx_r, r) in enumerate(brioche_prods.iterrows()):
            if cols_v[i % 4].button(f"{r['prodotto']}", key=f"bs_{idx_r}"):
                aggiorna_stock_veloce(r['prodotto'], -1); st.rerun()

    with tab3:
        st.write("### 📦 Carico Magazzino (+1)")
        stk = carica_stock()
        for p, q in stk.items():
            c1, c2, c3, c4 = st.columns([3, 1, 1, 1])
            c1.write(f"**{p}**")
            if c2.button("➖", key=f"m_{p}"): aggiorna_stock_veloce(p, -1); st.rerun()
            c3.write(f"**{q}**")
            if c4.button("➕", key=f"p_{p}"): aggiorna_stock_veloce(p, 1); st.rerun()

    with tab4:
        # CANCELLAZIONE CATEGORIE
        st.subheader("🗑️ Cancellazione Categorie")
        lista_cats = sorted(menu_df['categoria'].unique())
        cat_da_cancellare = st.selectbox("Seleziona categoria da eliminare", ["---"] + lista_cats)
        if cat_da_cancellare != "---":
            if st.button(f"Elimina Categoria {cat_da_cancellare}", type="primary"):
                menu_df = menu_df[menu_df['categoria'] != cat_da_cancellare]
                menu_df.to_csv(MENU_FILE, index=False); st.success("Eliminata!"); time.sleep(1); st.rerun()

        st.divider()
        # AGGIUNTA NUOVO PRODOTTO
        st.subheader("🆕 Aggiungi Nuovo Prodotto")
        with st.form("nuovo_p"):
            c1, c2 = st.columns(2)
            cat_esistente = c1.selectbox("Usa Categoria Esistente", ["---"] + lista_cats)
            cat_nuova = c2.text_input("OPPURE scrivi Nuova Categoria")
            nome_n = st.text_input("Nome Prodotto")
            prezzo_n = st.number_input("Prezzo €", step=0.1, min_value=0.0)
            if st.form_submit_button("AGGIUNGI"):
                cat_finale = cat_nuova if cat_nuova.strip() != "" else cat_esistente
                if cat_finale != "---" and nome_n:
                    nuovo_df = pd.DataFrame([{"categoria": cat_finale, "prodotto": nome_n, "prezzo": prezzo_n}])
                    pd.concat([menu_df, nuovo_df], ignore_index=True).to_csv(MENU_FILE, index=False); st.rerun()

        st.divider()
        st.subheader("📝 Modifica Singolo Prodotto")
        for i, row in menu_df.iterrows():
            with st.expander(f"{row['categoria']} - {row['prodotto']}"):
                with st.form(f"mod_{i}"):
                    nc = st.text_input("Categoria", row['categoria'])
                    np = st.text_input("Prodotto", row['prodotto'])
                    nr = st.number_input("Prezzo €", value=float(row['prezzo']))
                    c1, c2 = st.columns(2)
                    if c1.form_submit_button("SALVA"):
                        menu_df.at[i, 'categoria'], menu_df.at[i, 'prodotto'], menu_df.at[i, 'prezzo'] = nc, np, nr
                        menu_df.to_csv(MENU_FILE, index=False); st.rerun()
                    if c2.form_submit_button("ELIMINA"):
                        menu_df.drop(i).to_csv(MENU_FILE, index=False); st.rerun()

else:
    # --- CLIENTE --- (Invariato)
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
        if st.button("⬅️ Cambia Tavolo"): st.session_state.tavolo = None; st.rerun()
        
        scelta_cat = st.radio("Sezioni:", sorted(menu_df['categoria'].unique()), horizontal=True)
        prods = menu_df[menu_df['categoria'] == scelta_cat]
        p_cols = st.columns(2)
        for idx, (idx_r, r) in enumerate(prods.iterrows()):
            with p_cols[idx % 2]:
                if st.button(f"➕ {r['prodotto']}\n€{r['prezzo']:.2f}", key=f"cl_{idx_r}", use_container_width=True):
                    item = r.to_dict()
                    item['temp_id'] = time.time() + idx
                    st.session_state.carrello.append(item); st.toast("Aggiunto!")
        
        if st.session_state.carrello:
            st.divider(); st.write("### 🛒 Carrello:")
            for i, item in enumerate(st.session_state.carrello):
                c1, c2, c3 = st.columns([4, 2, 1])
                c1.write(item['prodotto'])
                c2.write(f"€{item['prezzo']:.2f}")
                if c3.button("❌", key=f"del_{item['temp_id']}"): st.session_state.carrello.pop(i); st.rerun()
            if st.button(f"🚀 INVIA ORDINE €{sum(c['prezzo'] for c in st.session_state.carrello):.2f}", type="primary", use_container_width=True):
                suona_notifica()
                ord_db = carica_ordini()
                for c in st.session_state.carrello:
                    ord_db.append({"id_univoco": str(time.time())+c['prodotto'], "tavolo": st.session_state.tavolo, "prodotto": c['prodotto'], "prezzo": c['prezzo'], "nota": "", "orario": datetime.now().strftime("%H:%M"), "stato": "NO"})
                salva_ordini(ord_db); st.session_state.carrello = []; st.success("Ordine Inviato!"); time.sleep(1); st.rerun()


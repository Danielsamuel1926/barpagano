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
    .servito { color: #555555 !important; text-decoration: line-through; opacity: 0.6; font-style: italic; }
    .da-servire { color: #FFFFFF !important; font-weight: bold; font-size: 18px; }
    .selected-tavolo { background-color: #FF4B4B; color: white; padding: 15px; border-radius: 15px; text-align: center; font-size: 24px; font-weight: bold; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- FILE DATABASE ---
DB_FILE = "ordini_bar_pagano.csv"
STOCK_FILE = "stock_bar_pagano.csv"
MENU_FILE = "menu_personalizzato.csv"
COLONNE_ORDINI = ["id_univoco", "tavolo", "prodotto", "prezzo", "nota", "orario", "stato"]

# --- FUNZIONE STAMPA SCONTRINO ---
def stampa_scontrino(tavolo, prodotti, totale):
    data_ora = datetime.now().strftime("%d/%m/%Y %H:%M")
    linee = "".join([f"<tr><td style='padding:5px 0'>{p['prodotto']}</td><td style='text-align:right'>€{float(p['prezzo']):.2f}</td></tr>" for p in prodotti])
    
    html_scontrino = f"""
    <html>
    <head>
        <style>
            body {{ font-family: 'Courier New', monospace; width: 80mm; font-size: 14px; color: black; background: white; }}
            .header {{ text-align: center; border-bottom: 1px dashed black; margin-bottom: 10px; }}
            table {{ width: 100%; border-collapse: collapse; }}
            .totale {{ border-top: 2px solid black; font-weight: bold; font-size: 18px; }}
            .footer {{ text-align: center; margin-top: 20px; border-top: 1px dashed black; font-size: 12px; }}
        </style>
    </head>
    <body onload="window.print(); setTimeout(function() {{ window.close(); }}, 500);">
        <div class="header">
            <h2 style="margin:5px 0;">BAR PAGANO</h2>
            <p style="margin:5px 0;">SCONTRINO NON FISCALE<br>Tavolo: {tavolo}<br>{data_ora}</p>
        </div>
        <table>
            {linee}
            <tr class="totale">
                <td style="padding-top:10px">TOTALE</td>
                <td style="text-align:right; padding-top:10px">€{totale:.2f}</td>
            </tr>
        </table>
        <div class="footer"><p>Grazie per la preferenza!</p></div>
    </body>
    </html>
    """
    components.html(f"<script>var win = window.open('', '_blank'); win.document.write(`{html_scontrino}`); win.document.close();</script>", height=0)

# --- FUNZIONI DI CARICAMENTO ROBUSTE (FISSA EMPTYDATAERROR) ---
def carica_menu():
    cols = ["categoria", "prodotto", "prezzo"]
    if not os.path.exists(MENU_FILE) or os.stat(MENU_FILE).st_size == 0:
        df = pd.DataFrame([{"categoria": "Caffetteria", "prodotto": "Caffè", "prezzo": 1.00}])
        df.to_csv(MENU_FILE, index=False)
        return df
    try:
        return pd.read_csv(MENU_FILE)
    except:
        pd.DataFrame(columns=cols).to_csv(MENU_FILE, index=False)
        return pd.DataFrame(columns=cols)

def carica_ordini():
    if not os.path.exists(DB_FILE) or os.stat(DB_FILE).st_size == 0:
        pd.DataFrame(columns=COLONNE_ORDINI).to_csv(DB_FILE, index=False)
        return []
    try:
        df = pd.read_csv(DB_FILE)
        return df.to_dict('records')
    except:
        pd.DataFrame(columns=COLONNE_ORDINI).to_csv(DB_FILE, index=False)
        return []

def salva_ordini(lista):
    df = pd.DataFrame(lista) if lista else pd.DataFrame(columns=COLONNE_ORDINI)
    df.to_csv(DB_FILE, index=False)

# --- LOGICA APPLICAZIONE ---
ruolo = st.query_params.get("ruolo", "tavolo")
menu_df = carica_menu()

if ruolo == "banco":
    st.title("🖥️ CONSOLE BANCONE")
    tab1, tab2, tab3, tab4 = st.tabs(["📋 ORDINI", "⚡ VENDITA RAPIDA", "📦 STOCK", "⚙️ LISTINO"])
    
    with tab1:
        ordini = carica_ordini()
        if not ordini: st.info("Nessun ordine attivo.")
        else:
            tavoli = sorted(list(set(str(o['tavolo']) for o in ordini)))
            cols = st.columns(3)
            for idx, t in enumerate(tavoli):
                with cols[idx % 3]:
                    with st.container(border=True):
                        st.subheader(f"🪑 Tavolo {t}")
                        prod_tavolo = [o for o in ordini if str(o['tavolo']) == str(t)]
                        tot_tavolo = sum(float(p['prezzo']) for p in prod_tavolo)
                        tutto_servito = all(p['stato'] == "SI" for p in prod_tavolo)

                        for r in ordini:
                            if str(r['tavolo']) == str(t):
                                c_t, c_b = st.columns([3, 1])
                                cl = "servito" if r['stato'] == "SI" else "da-servire"
                                c_t.markdown(f"<span class='{cl}'>{r['prodotto']}</span>", unsafe_allow_html=True)
                                if r['stato'] == "NO" and c_b.button("Ok", key=f"ok_{r['id_univoco']}"):
                                    r['stato'] = "SI"; salva_ordini(ordini); st.rerun()

                        st.divider()
                        if st.button(f"PAGATO €{tot_tavolo:.2f}", key=f"pay_{t}", type="primary", use_container_width=True, disabled=not tutto_servito):
                            stampa_scontrino(t, prod_tavolo, tot_tavolo)
                            nuovi_ordini = [o for o in ordini if str(o['tavolo']) != str(t)]
                            salva_ordini(nuovi_ordini)
                            st.rerun()
    
    with tab4:
        st.subheader("⚙️ Aggiungi Prodotto/Categoria")
        with st.form("add_form"):
            nuova_cat = st.text_input("Nuova Categoria (o lascia vuoto)")
            cat_esistente = st.selectbox("Categoria Esistente", menu_df['categoria'].unique() if not menu_df.empty else ["Generale"])
            nome_p = st.text_input("Nome Prodotto")
            prezzo_p = st.number_input("Prezzo €", min_value=0.0, step=0.1)
            if st.form_submit_button("SALVA"):
                c = nuova_cat if nuova_cat else cat_esistente
                if nome_p:
                    nuovo_df = pd.DataFrame([{"categoria": c, "prodotto": nome_p, "prezzo": prezzo_p}])
                    pd.concat([menu_df, nuovo_df], ignore_index=True).to_csv(MENU_FILE, index=False)
                    st.rerun()

else:
    # --- CLIENTE ---
    st.title("☕ BAR PAGANO")
    if 'tavolo_scelto' not in st.session_state: st.session_state.tavolo_scelto = None
    if 'carrello' not in st.session_state: st.session_state.carrello = []

    if st.session_state.tavolo_scelto is None:
        st.write("### Seleziona il tuo tavolo:")
        t_cols = st.columns(4)
        for i in range(1, 21):
            if t_cols[(i-1) % 4].button(f"{i}", key=f"t_{i}", use_container_width=True):
                st.session_state.tavolo_scelto = str(i); st.rerun()
    else:
        st.markdown(f"<div class='selected-tavolo'>TAVOLO {st.session_state.tavolo_scelto}</div>", unsafe_allow_html=True)
        if st.button("🔄 Cambia Tavolo"): st.session_state.tavolo_scelto = None; st.rerun()
        
        st.divider()
        if not menu_df.empty:
            scelta_cat = st.radio("Scegli:", menu_df['categoria'].unique(), horizontal=True)
            prod_filtrati = menu_df[menu_df['categoria'] == scelta_cat]
            p_cols = st.columns(2)
            for idx, (idx_r, r) in enumerate(prod_filtrati.iterrows()):
                with p_cols[idx % 2]:
                    if st.button(f"➕ {r['prodotto']}\n€{r['prezzo']:.2f}", key=f"cl_{idx_r}", use_container_width=True):
                        st.session_state.carrello.append({"prodotto": r['prodotto'], "prezzo": r['prezzo'], "id": time.time()})
                        st.toast("Aggiunto!")

        if st.session_state.carrello:
            st.divider()
            tot = sum(item['prezzo'] for item in st.session_state.carrello)
            if st.button(f"🚀 ORDINA €{tot:.2f}", type="primary", use_container_width=True):
                ord_db = carica_ordini()
                for item in st.session_state.carrello:
                    ord_db.append({
                        "tavolo": st.session_state.tavolo_scelto, "prodotto": item['prodotto'], 
                        "prezzo": item['prezzo'], "nota": "", "orario": datetime.now().strftime("%H:%M"), 
                        "stato": "NO", "id_univoco": str(time.time()) + item['prodotto']
                    })
                salva_ordini(ord_db)
                st.session_state.carrello = []
                st.success("Inviato!")
                time.sleep(1)
                st.rerun()



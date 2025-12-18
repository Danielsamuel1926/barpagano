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
            body {{ font-family: 'Courier New', monospace; width: 80mm; font-size: 14px; color: black; }}
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
        <div class="footer">
            <p>Grazie per la preferenza!</p>
        </div>
    </body>
    </html>
    """
    components.html(f"""
        <script>
        var win = window.open('', '_blank');
        win.document.write(`{html_scontrino}`);
        win.document.close();
        </script>
    """, height=0)

# --- FUNZIONI DI CARICAMENTO E SALVATAGGIO ---
def carica_menu():
    if not os.path.exists(MENU_FILE) or os.stat(MENU_FILE).st_size == 0:
        default = [{"categoria": "Brioche", "prodotto": "Cornetto", "prezzo": 1.50}]
        pd.DataFrame(default).to_csv(MENU_FILE, index=False)
        return pd.DataFrame(default)
    return pd.read_csv(MENU_FILE)

def carica_ordini():
    if not os.path.exists(DB_FILE) or os.stat(DB_FILE).st_size == 0:
        pd.DataFrame(columns=COLONNE_ORDINI).to_csv(DB_FILE, index=False)
        return []
    return pd.read_csv(DB_FILE).to_dict('records')

def salva_ordini(lista):
    if lista:
        df = pd.DataFrame(lista)
    else:
        df = pd.DataFrame(columns=COLONNE_ORDINI)
    df.to_csv(DB_FILE, index=False)

def aggiorna_stock_veloce(nome, var):
    if os.path.exists(STOCK_FILE):
        df = pd.read_csv(STOCK_FILE)
        if nome in df['prodotto'].values:
            idx = df[df['prodotto'] == nome].index[0]
            df.at[idx, 'quantita'] = max(0, df.at[idx, 'quantita'] + var)
            df.to_csv(STOCK_FILE, index=False)

# --- LOGICA BANCONE ---
ruolo = st.query_params.get("ruolo", "tavolo")
menu_df = carica_menu()

if ruolo == "banco":
    st.title("🖥️ CONSOLE BANCONE")
    
    tab1, tab2, tab3, tab4 = st.tabs(["📋 ORDINI", "⚡ VENDITA RAPIDA", "📦 STOCK", "⚙️ LISTINO"])
    
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
                            st.toast("Scontrino generato!")
                            time.sleep(1)
                            st.rerun()

    # (Le altre tab seguono la stessa logica delle versioni precedenti)
    with tab4:
        st.subheader("⚙️ Gestione Menù")
        with st.form("add_p"):
            c1, c2, c3 = st.columns([2, 2, 1])
            cat_n = c1.selectbox("Categoria", menu_df['categoria'].unique().tolist() if not menu_df.empty else ["Generale"])
            nom_n = c2.text_input("Nome Prodotto")
            pre_n = c3.number_input("Prezzo €", min_value=0.0, step=0.1)
            if st.form_submit_button("AGGIUNGI"):
                if nom_n:
                    nuovo = pd.DataFrame([{"categoria": cat_n, "prodotto": nom_n, "prezzo": pre_n}])
                    pd.concat([menu_df, nuovo], ignore_index=True).to_csv(MENU_FILE, index=False)
                    st.rerun()

else:
    # --- LOGICA CLIENTE ---
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
        categorie = menu_df['categoria'].unique()
        if len(categorie) > 0:
            scelta_cat = st.radio("Cosa desideri?", categorie, horizontal=True)
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
            if st.button(f"🚀 ORDINA TUTTO €{tot:.2f}", type="primary", use_container_width=True):
                ord_db = carica_ordini()
                for item in st.session_state.carrello:
                    ord_db.append({
                        "tavolo": st.session_state.tavolo_scelto, "prodotto": item['prodotto'], 
                        "prezzo": item['prezzo'], "nota": "", "orario": datetime.now().strftime("%H:%M"), 
                        "stato": "NO", "id_univoco": str(time.time()) + item['prodotto']
                    })
                salva_ordini(ord_db); st.session_state.carrello = []; st.success("Ordine Inviato!"); time.sleep(1); st.rerun()


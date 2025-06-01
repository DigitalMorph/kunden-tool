import streamlit as st
st.set_page_config(layout="wide")

import pandas as pd
from datetime import datetime
import os
import yaml
import streamlit_authenticator as stauth

# Login-Konfiguration
with open("config.yaml") as file:
    config = yaml.safe_load(file)

authenticator = stauth.Authenticate(
    config["credentials"],
    config["cookie"]["name"],
    config["cookie"]["key"],
    config["cookie"]["expiry_days"]
)

name, authentication_status, username = authenticator.login("Login", location="main")

if authentication_status is False:
    st.error("Benutzername oder Passwort ist falsch.")
if authentication_status is None:
    st.warning("Bitte einloggen.")
if authentication_status:

    authenticator.logout("Logout", "sidebar")
    st.sidebar.success(f"Eingeloggt als {name}")

    # Datei-Pfade
    KUNDEN_DATEI = "data/kunden.csv"
    KOMMENTAR_DATEI = "data/kommentare.csv"
    LOG_DATEI = "data/logs.csv"

    ALLE_TAGS = ["LIT2Trade", "LIT-EA", "LIT-Signal", "Interessent", "gekauft"]
    ALLE_PRODUKTE = ["kein Produkt", "Expert-Advisor", "LIT2Trade"]
    ALLE_STATUS = ["Interesse", "Kauf"]

    def lade_daten():
        if not os.path.exists("data"):
            os.makedirs("data")
        if not os.path.isfile(KUNDEN_DATEI):
            pd.DataFrame(columns=[
                "ID", "Vorname", "Nachname", "E-Mail", "Adresse", "Produkt", "Status", "Tags",
                "Konto ID1", "Konto ID2", "Konto ID3", "Konto ID4", "Bestelldatum", "Erstgespräch",
                "Rechnung geschickt", "Rechnung bezahlt", "Zugang DigiMember"
            ]).to_csv(KUNDEN_DATEI, index=False)
        if not os.path.isfile(KOMMENTAR_DATEI):
            pd.DataFrame(columns=["Kunden-ID", "Datum", "Kommentar"]).to_csv(KOMMENTAR_DATEI, index=False)
        if not os.path.isfile(LOG_DATEI):
            pd.DataFrame(columns=["Datum", "Benutzer", "Aktion", "Kunden-ID", "Details"]).to_csv(LOG_DATEI, index=False)
        return pd.read_csv(KUNDEN_DATEI), pd.read_csv(KOMMENTAR_DATEI)

    def speichere_kunde(kunde, kunden_id=None):
        df = pd.read_csv(KUNDEN_DATEI)
        if kunden_id:
            df.loc[df["ID"] == kunden_id, list(kunde.keys())] = list(kunde.values())
            neue_id = kunden_id
        else:
            neue_id = df["ID"].max() + 1 if not df.empty else 1
            kunde["ID"] = neue_id
            df = pd.concat([df, pd.DataFrame([kunde])])
        df.to_csv(KUNDEN_DATEI, index=False)
        return neue_id

    def speichere_kommentar(kunden_id, kommentar_text):
        df = pd.read_csv(KOMMENTAR_DATEI)
        neuer_kommentar = {
            "Kunden-ID": kunden_id,
            "Datum": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Kommentar": kommentar_text
        }
        df = pd.concat([df, pd.DataFrame([neuer_kommentar])])
        df.to_csv(KOMMENTAR_DATEI, index=False)

    def log_aktion(aktion, kunden_id, details=""):
        df = pd.read_csv(LOG_DATEI)
        neuer_log = {
            "Datum": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Benutzer": name,
            "Aktion": aktion,
            "Kunden-ID": kunden_id,
            "Details": details
        }
        df = pd.concat([df, pd.DataFrame([neuer_log])])
        df.to_csv(LOG_DATEI, index=False)


    st.title("👤 Kundenmanagement Tool")

    kunden_df, kommentar_df = lade_daten()

    st.sidebar.header("🗕️ Neuen Kunden anlegen")
    with st.sidebar.form("neuer_kunde"):
        vorname = st.text_input("Vorname")
        nachname = st.text_input("Nachname")
        email = st.text_input("E-Mail")
        adresse = st.text_area("Adresse")
        erstgespraech = st.date_input("Erstgespräch")
        produkt = st.selectbox("Produkt", ALLE_PRODUKTE)
        status = st.selectbox("Status", ALLE_STATUS)
        tags = st.multiselect("Tags", ALLE_TAGS)

        bestelldatum = ""
        rechnung_geschickt = False
        rechnung_bezahlt = False
        zugang_digimember = False

        if status == "gekauft":
            bestelldatum = st.date_input("Bestelldatum")

        kommentar = st.text_area("Kommentar (optional)")
        submitted = st.form_submit_button("Speichern")

        if submitted and vorname and nachname and email:
            if not kunden_df[(kunden_df["Vorname"] == vorname) & (kunden_df["Nachname"] == nachname)].empty:
                st.warning("⚠️ Ein Kunde mit diesem Namen existiert bereits.")
            else:
                kunde = {
                    "Vorname": vorname,
                    "Nachname": nachname,
                    "E-Mail": email,
                    "Adresse": adresse,
                    "Produkt": produkt,
                    "Status": status,
                    "Tags": ";".join(tags),
                    "Konto ID1": "",
                    "Konto ID2": "",
                    "Konto ID3": "",
                    "Konto ID4": "",
                    "Bestelldatum": str(bestelldatum) if status == "gekauft" else "",
                    "Erstgespräch": str(erstgespraech),
                    "Rechnung geschickt": rechnung_geschickt,
                    "Rechnung bezahlt": rechnung_bezahlt,
                    "Zugang DigiMember": zugang_digimember
                }
                neue_id = speichere_kunde(kunde)
                if kommentar.strip():
                    
                    speichere_kommentar(neue_id, kommentar.strip())
                log_aktion("Neu angelegt", neue_id)
                st.success(f"Kunde {vorname} {nachname} wurde erfolgreich angelegt.")
                st.experimental_rerun()

    st.subheader("🔍 Kunden filtern (optional)")
    tag_filter = st.multiselect("Tags", ALLE_TAGS)
    produkt_filter = st.multiselect("Produkt", ALLE_PRODUKTE)

    kunden_df, kommentar_df = lade_daten()
    gefiltert = kunden_df.copy()
    if tag_filter:
        gefiltert = gefiltert[gefiltert["Tags"].fillna("").str.contains("|".join(tag_filter))]
    if produkt_filter:
        gefiltert = gefiltert[gefiltert["Produkt"].isin(produkt_filter)]

    st.dataframe(gefiltert)

    if not kunden_df.empty:
        with st.expander("✏️ Kundendaten bearbeiten", expanded=False):
            kunden_df, kommentar_df = lade_daten()
            bearbeite_kunde = st.selectbox(
                "Kunden-ID auswählen",
                kunden_df["ID"].astype(str) + " – " + kunden_df["Vorname"] + " " + kunden_df["Nachname"],
                key="bearbeiten_selectbox"
            )
            if bearbeite_kunde:
                ausgewählte_id = int(bearbeite_kunde.split("–")[0].strip())
                kunde = kunden_df[kunden_df["ID"] == ausgewählte_id].iloc[0]

                with st.form("kunde_bearbeiten"):
                    kunde_dict = {}
                    kunde_dict["Vorname"] = st.text_input("Vorname", value=kunde["Vorname"])
                    kunde_dict["Nachname"] = st.text_input("Nachname", value=kunde["Nachname"])
                    kunde_dict["E-Mail"] = st.text_input("E-Mail", value=kunde["E-Mail"])
                    kunde_dict["Adresse"] = st.text_area("Adresse", value=kunde["Adresse"])
                    kunde_dict["Erstgespräch"] = st.date_input("Erstgespräch", value=pd.to_datetime(kunde["Erstgespräch"]))
                    kunde_dict["Produkt"] = st.selectbox("Produkt", ALLE_PRODUKTE, index=ALLE_PRODUKTE.index(kunde["Produkt"]))
                    kunde_dict["Status"] = st.selectbox("Status", ALLE_STATUS, index=ALLE_STATUS.index(kunde["Status"]))
                    kunde_dict["Tags"] = ";".join(st.multiselect("Tags", ALLE_TAGS, default=kunde["Tags"].split(";") if pd.notna(kunde["Tags"]) else []))

                    if kunde_dict["Produkt"] == "Expert-Advisor":
                        kunde_dict["Konto ID1"] = st.text_input("Konto ID1", value=kunde["Konto ID1"])
                        kunde_dict["Konto ID2"] = st.text_input("Konto ID2", value=kunde["Konto ID2"])
                        kunde_dict["Konto ID3"] = st.text_input("Konto ID3", value=kunde["Konto ID3"])
                        kunde_dict["Konto ID4"] = st.text_input("Konto ID4", value=kunde["Konto ID4"])
                    else:
                        kunde_dict["Konto ID1"] = kunde_dict["Konto ID2"] = kunde_dict["Konto ID3"] = kunde_dict["Konto ID4"] = ""

                    if kunde_dict["Status"] == "Kauf":
                        kunde_dict["Bestelldatum"] = st.date_input("Bestelldatum", value=pd.to_datetime(kunde["Bestelldatum"]) if pd.notna(kunde["Bestelldatum"]) else datetime.today())
                        kunde_dict["Rechnung geschickt"] = st.checkbox("Rechnung geschickt", value=bool(kunde["Rechnung geschickt"]))
                        kunde_dict["Rechnung bezahlt"] = st.checkbox("Rechnung bezahlt", value=bool(kunde["Rechnung bezahlt"]))
                        kunde_dict["Zugang DigiMember"] = st.checkbox("Zugang DigiMember angelegt", value=bool(kunde["Zugang DigiMember"]))
                    else:
                        kunde_dict["Bestelldatum"] = ""
                        kunde_dict["Rechnung geschickt"] = kunde_dict["Rechnung bezahlt"] = kunde_dict["Zugang DigiMember"] = False

                    kommentar_neu = st.text_area("Neuen Kommentar hinzufügen")
                    speichern = st.form_submit_button("Änderungen speichern")

                    if speichern:
                        aenderungen = []
                        for key in kunde_dict:
                            alt = str(kunde[key]) if key in kunde else ""
                            neu = str(kunde_dict[key])
                            if alt != neu:
                                aenderungen.append(f"{key}: '{alt}' → '{neu}'")
                        aenderungs_text = "; ".join(aenderungen) if aenderungen else "Keine Änderungen"

                        speichere_kunde(kunde_dict, kunden_id=ausgewählte_id)
                        if kommentar_neu.strip():
                            speichere_kommentar(ausgewählte_id, kommentar_neu.strip())
                        log_aktion("Bearbeitet", ausgewählte_id, aenderungs_text)
                        st.success("Kunde wurde aktualisiert.")
                        st.experimental_rerun()


                kommentare_kunde = kommentar_df[kommentar_df["Kunden-ID"] == ausgewählte_id].sort_values("Datum", ascending=False).reset_index(drop=True)

                st.markdown("""<style>
                    .kommentar-box {
                        white-space: pre-wrap;
                        border: 1px solid #ddd; 
                        padding: 0px 8px 6px 8px;
                        margin-bottom: 4px;
                        border-radius: 4px;
                        background-color: #f9f9f9;
                        font-size: 13px;
                        line-height: 1.3;
                    }
                    .kommentar-datum {
                        font-weight: bold;
                        color: #1b3061;
                        margin: 0;
                    }
                    .kommentar-text {
                        margin: 0;
                    }
                    .block-container {
                        padding-left: 1rem !important;
                        padding-right: 1rem !important;
                    }
                </style>""", unsafe_allow_html=True)

                if st.button("🗑️ Kundenprofil löschen"):
                    kunden_df = kunden_df[kunden_df["ID"] != ausgewählte_id]
                    kunden_df.to_csv(KUNDEN_DATEI, index=False)
                    kommentar_df = kommentar_df[kommentar_df["Kunden-ID"] != ausgewählte_id]
                    kommentar_df.to_csv(KOMMENTAR_DATEI, index=False)
                    log_aktion("Gelöscht", ausgewählte_id)
                    st.success("Kunde wurde gelöscht.")
                    st.experimental_rerun()

                for _, row in kommentare_kunde.iterrows():
                    st.markdown(f"""
                        <div class='kommentar-box'>
                            <div class='kommentar-datum'>{row['Datum']}</div>
                            <div class='kommentar-text'>{row['Kommentar']}</div>
                        </div>
                    """, unsafe_allow_html=True)

                st.subheader("📋 Änderungsprotokoll")
                try:
                    logs_df = pd.read_csv(LOG_DATEI)
                    logs_df = logs_df.sort_values("Datum", ascending=False).reset_index(drop=True)
                    st.dataframe(logs_df)
                except Exception as e:
                    st.info("Noch keine Logs vorhanden oder Datei konnte nicht geladen werden.")
    else:
        st.info("❕ Noch keine Kunden vorhanden.")

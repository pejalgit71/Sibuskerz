import streamlit as st
import pandas as pd
import gspread
import requests
import json
from google.oauth2.service_account import Credentials

# --- CONFIG ---
SHEET_ID = "1xDkePn-ka6xvfoInEGe0PRWLPd39j7fhigQNEpOFkDw"  # Replace with your Google Sheet ID
WORKSHEET_NAME = "lyrics"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

# --- GOOGLE SHEETS SETUP ---
@st.cache_resource

def get_worksheet():
    creds_dict = dict(st.secrets["gcp_service_account"])
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    client = gspread.authorize(creds)
    worksheet = client.open_by_key(SHEET_ID).worksheet(WORKSHEET_NAME)
    return worksheet

def get_lyrics_df(worksheet):
    data = worksheet.get_all_records()
    return pd.DataFrame(data)

def add_new_song(worksheet, title, artist, lyrics):
    worksheet.append_row([title.strip(), artist.strip(), lyrics.strip()])

# --- LYRICS API SEARCH ---
def search_lyrics_online(artist, title):
    try:
        url = f"https://api.lyrics.ovh/v1/{artist}/{title}"
        res = requests.get(url)
        if res.status_code == 200:
            return res.json().get('lyrics', 'Lyrics not found.')
        else:
            return "Lyrics not found online."
    except:
        return "Error fetching lyrics."

# --- STREAMLIT UI ---
st.set_page_config(page_title="🎤 Busker Lyrics App", layout="wide")
st.sidebar.image("SIBuskerz.JPG", use_container_width =True)
st.title("🎶 Busker Lyrics Performance App")

menu = ["📖 View Lyrics", "➕ Add New Song", "🌐 Search Lyrics Online"]
choice = st.sidebar.radio("Menu", menu)

worksheet = get_worksheet()
lyrics_df = get_lyrics_df(worksheet)

# --- CSS for readable text ---
# st.markdown("""
#     <style>
#     .big-lyrics textarea {
#         font-size: 22px !important;
#         color:DodgerBlue;
#         font-family: monospace;
#         background-color: #f9f9f9;
#         line-height: 1.7;
#     }
#     </style>
# """, unsafe_allow_html=True)

# --- VIEW LYRICS ---
if choice == "📖 View Lyrics":
    st.subheader("Select a song to view lyrics")
    song_titles = lyrics_df['Title'] + " - " + lyrics_df['Artist']
    selection = st.selectbox("Song List", song_titles)

    if selection:
        title, artist = selection.split(" - ")
        row = lyrics_df[(lyrics_df['Title'] == title) & (lyrics_df['Artist'] == artist)].iloc[0]
        st.markdown(f"### 🎵 {row['Title']} by {row['Artist']}")
        st.markdown("""
    <style>
    textarea {
        font-size: 24px !important;
        font-family: 'Courier New', monospace !important;
        color: #ffffff !important;
        background-color: #1e1e1e !important;
        line-height: 1.6 !important;
        padding: 10px !important;
    }
    </style>
""", unsafe_allow_html=True)

        st.text_area("Lyrics", value=row['Lyrics'], height=600, key="view_lyrics", label_visibility="collapsed", disabled=True)

# --- ADD NEW SONG ---
elif choice == "➕ Add New Song":
    st.subheader("Add a new song to your collection")
    with st.form("add_song_form"):
        new_title = st.text_input("Song Title")
        new_artist = st.text_input("Artist Name")
        new_lyrics = st.text_area("Paste Full Lyrics Here", height=300)
        submitted = st.form_submit_button("Add Song")

        if submitted:
            if new_title and new_artist and new_lyrics:
                add_new_song(worksheet, new_title, new_artist, new_lyrics)
                st.success(f"✅ '{new_title}' by {new_artist}' has been added!")
            else:
                st.error("Please complete all fields.")

# --- SEARCH ONLINE ---
elif choice == "🌐 Search Lyrics Online":
    st.subheader("Search lyrics from the internet (Lyrics.ovh)")
    with st.form("search_online"):
        artist = st.text_input("Artist Name")
        title = st.text_input("Song Title")
        search = st.form_submit_button("Search")

        if search and artist and title:
            lyrics = search_lyrics_online(artist, title)
            st.text_area("Lyrics Result", value=lyrics, height=400)

            if "not found" not in lyrics.lower() and st.button("Save to Google Sheet"):
                add_new_song(worksheet, title, artist, lyrics)
                st.success(f"✅ '{title}' by {artist}' added to your lyrics list!")

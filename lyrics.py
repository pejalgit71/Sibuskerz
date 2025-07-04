import streamlit as st
import pandas as pd
import gspread
import requests
import json
from google.oauth2.service_account import Credentials

# --- CONFIG ---
SHEET_ID = "1xDkePn-ka6xvfoInEGe0PRWLPd39j7fhigQNEpOFkDw"  # Replace with your Google Sheet ID
WORKSHEET_NAME1 = "lyrics"
WORKSHEET_NAME2 = "members"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

# --- GOOGLE SHEETS SETUP ---
@st.cache_resource

# def get_worksheet():
#     creds_dict = dict(st.secrets["gcp_service_account"])
#     creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
#     client = gspread.authorize(creds)
#     worksheet = client.open_by_key(SHEET_ID).worksheet(WORKSHEET_NAME)
#     return worksheet

def get_worksheets():
    creds_dict = dict(st.secrets["gcp_service_account"])
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    client = gspread.authorize(creds)
    
    sheet = client.open_by_key(SHEET_ID)
    songs_worksheet = sheet.worksheet(WORKSHEET_NAME1)         # or your original WORKSHEET_NAME
    members_worksheet = sheet.worksheet(WORKSHEET_NAME2)     # must match Google Sheet tab name exactly

    return songs_worksheet, members_worksheet
    
def get_lyrics_df(songs_worksheet):
    data = songs_worksheet.get_all_records()
    return pd.DataFrame(data)

def add_new_song(songs_worksheet, title, artist, lyrics):
    songs_worksheet.append_row([title.strip(), artist.strip(), lyrics.strip()])

def load_members(members_worksheet):
    df = pd.DataFrame(members_worksheet.get_all_records())
    return df.to_dict(orient="records")    

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
st.set_page_config(page_title="🎤 SIBuskerz Lyrics App", layout="wide")
st.sidebar.image("SIBuskerz.JPG", use_container_width =True)
st.title("🎶 SIBuskerz Lyrics Performance App©")

menu = ["📖 View Lyrics/Lihat Lirik", "➕ Add New Song/Masukkan lirik Lagu baru", "🌐 Search Lyrics Online", "👥 Meet The Members", "🎤 Performance Mode"]
# choice = st.sidebar.radio("Menu", menu)

choice = st.sidebar.selectbox("Navigation", menu)


worksheet, members_sheet = get_worksheets()
# worksheet = get_worksheet()
lyrics_df = get_lyrics_df(worksheet)

st.markdown("""
    <style>
    .lyrics-box {
        background-color: #fffbe6;
        padding: 20px;
        border-radius: 10px;
        font-size: 24px;
        font-family: 'Courier New', monospace;
        color: black;
        line-height: 1.6;
        white-space: pre-wrap;
        word-wrap: break-word;
    }

    @media screen and (max-width: 600px) {
        .lyrics-box {
            font-size: 20px;
        }
    }
    </style>
""", unsafe_allow_html=True)


# --- VIEW LYRICS ---
if choice == "📖 View Lyrics/Lihat Lirik":
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
                color: black !important;
                background-color: #fffbe6 !important;
                line-height: 1.6 !important;
                padding: 10px !important;
            }
            </style>
        """, unsafe_allow_html=True)



        st.markdown(f"""
        <div class="lyrics-box">
            <pre>{row['Lyrics']}</pre>
        </div>
        """, unsafe_allow_html=True)


# --- ADD NEW SONG ---
elif choice == "➕ Add New Song/Masukkan lirik Lagu baru":
    st.subheader("Add a new song's lyric to your collection/Masukkan Lirik Lagu Baru")

    # Admin Password Prompt
    password = st.text_input("Enter admin password to continue/Masukkan password admin:", type="password")

    if password == st.secrets["admin_password"]:
        st.success("Access granted. You may now add a new song's lyric/Anda dibenarkan masukkan lirik lagu baru")

        with st.form("add_song_form"):
            new_title = st.text_input("🎵 Song Title/Tajuk Lagu")
            new_artist = st.text_input("🎤 Artist Name/ Nama Artis")
            new_lyrics = st.text_area("📝 Paste Full Lyrics Here/Masukkan Lirik disini", height=300)
            submitted = st.form_submit_button("Add Song")

            if submitted:
                if new_title and new_artist and new_lyrics:
                    add_new_song(worksheet, new_title, new_artist, new_lyrics)
                    st.success(f"✅ '{new_title}' by {new_artist} has been added!")
                else:
                    st.error("❌ Please complete all fields before submitting.")
    elif password:
        st.error("Incorrect password. Access denied.")

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
                
elif choice == "👥 Meet The Members":
    st.subheader("🎸 SiBuskerz Members")

    members = load_members(members_sheet)

    for member in members:
        with st.container():
            cols = st.columns([1, 2])
            with cols[0]:
                st.image(member["Photo"], use_container_width=True)
            with cols[1]:
                st.markdown(f"### {member['Name']}")
                st.markdown(f"**Role:** {member['Role']}")
                st.markdown(f"*{member['Bio']}*")
        st.markdown("---")
        
elif choice == "🎤 Performance Mode":
    st.subheader("🎤 SiBuskerz Performance Mode")
    
    # Load lyrics list
    song_data = worksheet.get_all_records()
    song_titles = [f"{row['Title']} - {row['Artist']}" for row in song_data]

    # Select songs for the session
    selected_songs = st.multiselect("Select up to 10 songs to perform", options=song_titles, max_selections=10)

    if selected_songs:
        if st.button("🎬 Start Performance"):
            st.session_state.performance_queue = selected_songs
            st.session_state.current_song_index = 0

    # Show queue
    if "performance_queue" in st.session_state:
        queue = st.session_state.performance_queue
        index = st.session_state.get("current_song_index", 0)

        if index < len(queue):
            current_title_artist = queue[index]
            title, artist = current_title_artist.split(" - ")

            # Find lyrics for current song
            for row in song_data:
                if row["Title"] == title and row["Artist"] == artist:
                    st.markdown(f"### 🎶 Now Performing: **{title}** by *{artist}*")
                    st.text_area("Lyrics", value=row["Lyrics"], height=500, label_visibility="collapsed", disabled=True)

            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("⏭️ Next Song"):
                    st.session_state.current_song_index += 1
            with col2:
                if st.button("🛑 End Performance"):
                    st.session_state.pop("performance_queue", None)
                    st.session_state.pop("current_song_index", None)
                    st.success("Performance ended.")

        else:
            st.success("✅ You've finished your performance!")
            if st.button("Reset"):
                st.session_state.pop("performance_queue", None)
                st.session_state.pop("current_song_index", None)


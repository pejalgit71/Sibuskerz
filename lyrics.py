import streamlit as st
import pandas as pd
import gspread
import requests
from google.oauth2.service_account import Credentials

# --- CONFIG ---
SHEET_ID = "1xDkePn-ka6xvfoInEGe0PRWLPd39j7fhigQNEpOFkDw"
WORKSHEET_NAME1 = "lyrics"
WORKSHEET_NAME2 = "members"
WORKSHEET_NAME3 = "videos"
WORKSHEET_NAME4 = "performances"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

# --- GOOGLE SHEETS SETUP ---
@st.cache_resource
def get_worksheets():
    creds_dict = dict(st.secrets["gcp_service_account"])
    creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(SHEET_ID)
    songs_ws = sheet.worksheet(WORKSHEET_NAME1)
    members_ws = sheet.worksheet(WORKSHEET_NAME2)
    videos_ws = sheet.worksheet(WORKSHEET_NAME3)
    performance_ws = sheet.worksheet(WORKSHEET_NAME4)
    return songs_ws, members_ws, videos_ws, performance_ws

def get_lyrics_df(ws):
    data = ws.get_all_records()
    return pd.DataFrame(data)

def add_new_song(ws, title, artist, lyrics):
    ws.append_row([title.strip(), artist.strip(), lyrics.strip()])

def load_members(ws):
    df = pd.DataFrame(ws.get_all_records())
    return df.to_dict(orient="records")

def load_videos(ws):
    df = pd.DataFrame(ws.get_all_records())
    return df.to_dict(orient="records")
    
def load_performances(ws):
    df = pd.DataFrame(ws.get_all_records())
    return df.to_dict(orient="records")


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


# --- CUSTOM STYLES ---
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
# --- STREAMLIT UI ---
st.set_page_config(page_title="🎤 SIBuskerz Lyrics App", layout="wide")
st.sidebar.image("SIBuskerz.JPG", use_container_width=True)

st.title("🎶 SIBuskerz Lyrics Performance©")

menu = [
    "📖 View Lyrics/Lihat Lirik",
    "➕ Add New Song/Masukkan lirik Lagu baru",
    "🌐 Search Lyrics Online",
    "👥 Meet The Members",
    "🎤 Performance Mode",
    "📍 Performance Venues & Tokens"
]

choice = st.sidebar.selectbox("Navigation", menu)

worksheet, members_sheet, videos_sheet, performances_sheet = get_worksheets()
lyrics_df = get_lyrics_df(worksheet)

# --- VIEW LYRICS ---
if choice == "📖 View Lyrics/Lihat Lirik":
   
    st.subheader("Select a song to view lyrics")

    lyrics_df_sorted = lyrics_df.sort_values(by='Title')
    full_titles = lyrics_df_sorted['Title'] + " - " + lyrics_df_sorted['Artist']

    search_term = st.text_input("🔍 Search song title")
    filtered_titles = [title for title in full_titles if search_term.lower() in title.lower()]

    selection = st.selectbox("Song List", filtered_titles if search_term else full_titles)

    if selection:
        title, artist = selection.split(" - ")
        row = lyrics_df_sorted[(lyrics_df_sorted['Title'] == title) & (lyrics_df_sorted['Artist'] == artist)].iloc[0]
        st.markdown(f"### 🎵 {row['Title']} by {row['Artist']}")
        st.markdown(f"""
        <div class="lyrics-box">
            <pre>{row['Lyrics']}</pre>
        </div>
        """, unsafe_allow_html=True)

# --- ADD NEW SONG ---
elif choice == "➕ Add New Song/Masukkan lirik Lagu baru":
    st.subheader("Add a new song's lyric to your collection")
    password = st.text_input("Enter admin password to continue:", type="password")

    if password == st.secrets["admin_password"]:
        st.success("Access granted.")

        with st.form("add_song_form"):
            new_title = st.text_input("🎵 Song Title")
            new_artist = st.text_input("🎤 Artist Name")
            new_lyrics = st.text_area("📝 Paste Full Lyrics Here", height=300)
            submitted = st.form_submit_button("Add Song")

            if submitted:
                if new_title and new_artist and new_lyrics:
                    add_new_song(worksheet, new_title, new_artist, new_lyrics)
                    st.success(f"✅ '{new_title}' by {new_artist} has been added!")
                else:
                    st.error("❌ Please complete all fields.")
    elif password:
        st.error("Incorrect password.")

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
                st.success(f"✅ '{title}' by {artist}' added!")

# --- MEET THE MEMBERS ---
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

# --- PERFORMANCE MODE ---
elif choice == "🎤 Performance Mode":
    st.subheader("🎤 SiBuskerz Performance Mode/Pilih Lagu-lagu untuk persembahan")

    song_data = worksheet.get_all_records()
    song_data_sorted = sorted(song_data, key=lambda x: x['Title'].lower())
    full_titles = [f"{row['Title']} - {row['Artist']}" for row in song_data_sorted]

    search_term = st.text_input("🔍 Search and filter songs (Performance Mode)")
    filtered_titles = [title for title in full_titles if search_term.lower() in title.lower()]

    selected_songs = st.multiselect("🎶 Pilih maksima 30 lagu untuk nyanyi", options=filtered_titles if search_term else full_titles, max_selections=30)

    if selected_songs:
        if st.button("🎬 Start Performance"):
            st.session_state.performance_queue = selected_songs
            st.session_state.current_song_index = 0

    # Show current song
    if "performance_queue" in st.session_state:
        queue = st.session_state.performance_queue
        index = st.session_state.get("current_song_index", 0)

        if index < len(queue):
            current_title_artist = queue[index]
            title, artist = current_title_artist.split(" - ")

            for row in song_data_sorted:
                if row["Title"] == title and row["Artist"] == artist:
                    st.markdown(f"### 🎶 Now Performing: **{title}** by *{artist}*")
                   
                    st.markdown(f"""
                    <div class="lyrics-box">
                        <pre>{row['Lyrics']}</pre>
                    </div>
                    """, unsafe_allow_html=True)

                    # st.text_area("Lyrics", value=row["Lyrics"], height=500, label_visibility="collapsed", disabled=True)

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

# --- VIDEO GALLERY ---
elif choice == "🎞️ Past Performances":
    st.subheader("🎬 SiBuskerz Video Performances")

    videos = load_videos(videos_sheet)  # Your function that loads videos from the Google Sheet

    if videos:
        for i in range(0, len(videos), 2):
            cols = st.columns(2)
            for j in range(2):
                if i + j < len(videos):
                    vid = videos[i + j]
                    with cols[j]:
                        st.markdown(f"**🎵 {vid['Title']}**")
                        st.markdown(f"*{vid['Description']}*")

                        video_link = vid['VideoLink']

                        if "drive.google.com" in video_link:
                            try:
                                # Extract the video ID from Google Drive link
                                video_id = video_link.split("/d/")[1].split("/")[0]
                                embed_url = f"https://drive.google.com/file/d/{video_id}/preview"
                                st.markdown(f"""
                                    <iframe src="{embed_url}" width="100%" height="315" allow="autoplay" allowfullscreen></iframe>
                                """, unsafe_allow_html=True)
                            except:
                                st.error("⚠️ Unable to display Google Drive video.")
                        else:
                            st.video(video_link)

                        st.markdown("---")
    else:
        st.info("No video performances listed yet.")
        
elif choice == "📍 Performance Venues & Tokens":
    st.subheader("🎪 SiBuskerz Performance Schedule & Appreciation Tokens")

    # Load data from sheet
    df_perf = pd.DataFrame(performances_sheet.get_all_records())
    df_members = pd.DataFrame(members_sheet.get_all_records())
    num_members = len(df_members)
    total_shares = num_members + 1  # 1 share for equipment

    if not df_perf.empty:
        st.markdown("### 🎤 Upcoming & Past Performances")
        st.dataframe(df_perf)

        # Compute token stats
        done_perf = df_perf[df_perf['Status'].str.lower() == 'done']
        total_token = done_perf['TotalToken'].fillna(0).astype(float).sum()
        total_distributed = done_perf['SharedPerPerson'].fillna(0).astype(float).sum() * num_members
        total_equipment = done_perf['EquipmentShare'].fillna(0).astype(float).sum()
        total_undistributed = total_token - (total_distributed + total_equipment)

        st.markdown(f"""
        ### 💰 Token Summary
        - 🎁 **Total Token Collected**: RM {total_token:.2f}
        - 👥 **Total Shared to Members**: RM {total_distributed:.2f}
        - 🎛️ **Equipment Share**: RM {total_equipment:.2f}
        - ❓ **Undistributed Token**: RM {total_undistributed:.2f}
        """)
    else:
        st.info("No performance records yet.")

    # Form to add new performance
    st.markdown("### ➕ Add or Update Performance Info")
    with st.form("add_perf_form"):
        perf_date = st.date_input("📅 Performance Date")
        venue = st.text_input("📍 Venue Name")
        status = st.selectbox("Status", ["Upcoming", "Done"])
        token = st.number_input("🎁 Total Token Collected (only for Done)", min_value=0.0, value=0.0, step=1.0)
        notes = st.text_area("📝 Notes (optional)")
        submitted = st.form_submit_button("Save Performance Info")

        if submitted:
            # Calculate shares if Done and token is given
            if status == "Done" and token > 0:
                shared = round(token / total_shares, 2)
                equipment = round(shared, 2)
            else:
                shared = ""
                equipment = ""

            # Append to sheet
            performances_sheet.append_row([
                str(perf_date),
                venue,
                status,
                token if token else "",
                shared,
                equipment,
                notes
            ])
            st.success("✅ Performance info saved! Please refresh to view updated data.")

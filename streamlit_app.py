import streamlit as st
import requests
import time
import os
import tempfile
from urllib.parse import quote_plus


def start_progress():
    progress_bar = st.progress(0)
    status_text = st.empty()
    return progress_bar, status_text


def update_progress(progress_bar, status_text, percent, text):
    progress_bar.progress(percent)
    status_text.markdown(f"**{text}**")


BASE_URL = os.getenv("BACKEND_URL") or st.secrets.get("BACKEND_URL")
print(f"Using backend URL:", BASE_URL)


st.set_page_config(
    page_title="AI Ad Studio",
    page_icon="",
    layout="wide"
)


def api_post(url, params=None, timeout=300):
    try:
        r = requests.post(url, params=params, timeout=timeout)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"__error__": str(e)}


st.markdown(
    """
    <div style="padding:20px;border-radius:14px;background:linear-gradient(90deg,#0f2027,#203a43,#2c5364);color:white">
        <h1 style="margin-bottom:0"> AI Ad Studio</h1>
        <p style="margin-top:6px;font-size:16px">
            Generate professional AI video ads with character consistency, voiceover & music
        </p>
    </div>
    """,
    unsafe_allow_html=True
)


st.markdown("")


st.sidebar.header(" Campaign Settings")


business_type = st.sidebar.selectbox("Business type", ["nail salon", "hair salon", "spa"])
campaign_theme = st.sidebar.selectbox("Theme", ["Christmas", "Valentine", "New Year", "Summer", "Spring"])
num_scenes = st.sidebar.slider("Number of scenes", 1, 5, 3)


character_age = st.sidebar.text_input("Character age", "28-32")
character_gender = st.sidebar.selectbox("Gender", ["woman", "man", "non-binary"])
character_ethnicity = st.sidebar.text_input("Ethnicity", "Indian")


st.sidebar.divider()
st.sidebar.subheader(" Business Info")
business_name = st.sidebar.text_input("Business name", "Paradise Nails")
phone_number = st.sidebar.text_input("Phone", "9876543210")
website = st.sidebar.text_input("Website", "https://example.com")


st.markdown(" Step 1 — Generate Campaign Images")


if st.button(" Generate Campaign"):
    with st.spinner("Generating campaign & images..."):
        params = {
            "business_type": business_type,
            "campaign_theme": campaign_theme,
            "character_age": character_age,
            "character_gender": character_gender,
            "character_ethnicity": character_ethnicity,
            "num_scenes": num_scenes
        }
        res = api_post(f"{BASE_URL}/campaign/generate_beauty_campaign", params=params, timeout=600)

    if "__error__" in res:
        st.error(res["__error__"])
    else:
        st.success("Campaign created successfully")
        st.session_state["campaign"] = res
        st.session_state["campaign_id"] = res.get("campaign_id")


campaign = st.session_state.get("campaign")

if campaign:
    st.markdown("### Generated Images")

    scenes = campaign.get("scenes")

    if not scenes:
        st.warning("No images were returned from the backend.")
        st.json(campaign)  # temporary debug – you can remove later
    else:
        cols = st.columns(len(scenes))
        for i, scene in enumerate(scenes):
            with cols[i]:
                image_url = scene.get("image")
                scene_number = scene.get("scene_number", i + 1)

                if image_url:
                    st.image(image_url, use_column_width=True)
                else:
                    st.warning("Image URL missing")

                st.caption(f"Scene {scene_number}")


st.markdown("##  Step 2 — Generate Videos")


campaign_id = st.text_input(
    "Campaign ID",
    value=st.session_state.get("campaign_id", "")
)


if st.button(" Generate Videos"):
    if not campaign_id:
        st.error("Campaign ID missing")
    else:
        st.session_state.pop("video_result", None)

        progress_bar, status_text = start_progress()

        try:
            update_progress(progress_bar, status_text, 5, " Starting video generation...")

            params = {
                "business_name": business_name,
                "phone_number": phone_number,
                "website": website
            }

            update_progress(progress_bar, status_text, 15, " Sending request to backend...")

            res = api_post(
                f"{BASE_URL}/campaign/generate_campaign_videos/{campaign_id}",
                params=params,
                timeout=3600
            )

            if "__error__" in res:
                progress_bar.empty()
                status_text.empty()
                st.error(res["__error__"])
                st.stop()

            update_progress(progress_bar, status_text, 70, " Videos generated, processing results...")

            st.session_state["video_result"] = res

            update_progress(progress_bar, status_text, 100, " Done! Videos ready below.")

            time.sleep(0.4)
            progress_bar.empty()
            status_text.empty()

            st.success("Videos generated successfully")

        except Exception as e:
            progress_bar.empty()
            status_text.empty()
            st.error(f"Something went wrong: {e}")


video_result = st.session_state.get("video_result")


if video_result:
    final_video = video_result.get("final_merged_video")

    if final_video:
        st.markdown("Final AI Advertisement")
        st.video(final_video)

        try:
            r = requests.get(final_video)
            if r.status_code == 200:
                st.download_button(
                    "⬇ Download Final Ad",
                    data=r.content,
                    file_name="final_ai_ad.mp4",
                    mime="video/mp4"
                )
        except Exception:
            st.warning("Unable to fetch video for download")

    else:
        st.markdown(" Scene Videos (Demo Preview)")
        shown = set()

        for v in video_result.get("videos", []):
            url = v.get("video_url")
            if url and url not in shown:
                st.video(url)
                st.caption(f"Scene {v['scene_number']}")
                shown.add(url)


st.markdown("---")
st.caption(
    " AI Ad Studio Demo — Character consistency • Voiceover • Music • VEO 3.1"
)




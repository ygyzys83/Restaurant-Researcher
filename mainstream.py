import streamlit as st
import google.genai as genai
from google.genai import types
import smtplib
import re
from email.message import EmailMessage

# --- UI Header ---
st.title("Neighborhood Nosh")
st.caption("Real local spots. Zero guesswork.")

# Display header image (shows before AND after unlock - looks better this way)
st.image("images/neighborhood_nosh.jpg", use_container_width=False)

# App Password Check (placed at the very top)
if "app_unlocked" not in st.session_state:
    st.session_state.app_unlocked = False

# Show password input ONLY if not yet unlocked
if not st.session_state.app_unlocked:
    app_password = st.text_input(
        "Enter App Password to Unlock",
        type="password",
        placeholder="Enter the password to use this app..."
    )

    if st.button("Unlock App"):
        if app_password == st.secrets["APP_PASSWORD"]:
            st.session_state.app_unlocked = True
            st.success("✅ App unlocked successfully!")
            st.rerun()
        else:
            st.error("❌ Incorrect password. Access denied.")

    st.stop()  # Stop execution until unlocked

# --- Sidebar for Settings
with st.sidebar:
    st.header("Search Parameters")
    res_type = st.text_input("Restaurant Type", "pizza")
    miles = st.number_input("Max Distance (miles)", min_value=1, value=5)
    address = st.text_input("From Address", "350 Macarthur Blvd, Oakland, CA")
    min_rating = st.slider("Min Google Rating", 1.0, 5.0, 4.0, format="%1.1f")
    min_reviews = st.number_input("Min Review Count", min_value=0, value=100)
    num_results = st.number_input("Number of Results", 1, 10, 5)
    recipient_email = st.text_input("Recipient Email", st.secrets["GMAIL_USER"])
    run_button = st.button("Research & Email")

# --- The Logic (Inside the button click) ---
if run_button:
    research_results = None
    usage_data = None

    with st.spinner("Searching live web..."):
        try:
            client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

            grounding_tool = types.Tool(
                google_maps=types.GoogleMaps()
            )

            prompt = f"""
                You are a strict local restaurant researcher using Google Maps data in 2026.
                
                Task: Find up to {num_results} actual {res_type} restaurants near {address}.

                Requirements — follow these strictly:
                - Only {res_type} restaurants or restaurants that have a reputation for good {res_type}.
                - Within approximately {miles} driving miles of {address}
                - Minimum {min_rating} stars on Google Maps
                - Minimum {min_reviews} reviews on Google Maps
                - Only places that are currently open or have recent activity.

                Do NOT return any restaurant that fails the rating or review minimum. It is better to return fewer results than to include lower-quality ones.

                Output rules:
                - Return ONLY a valid HTML table. Start immediately with <table>.
                - Do not add any explanation or markdown.
                - Use this exact table style:
                  <table style="width:100%; border:1px solid #333; border-collapse:collapse; font-family:sans-serif;">
                - Header cells: <th style="background-color:#2c3e50; color:white; padding:8px; border:1px solid #333;">
                - Data cells: <td style="padding:8px; border:1px solid #ddd; vertical-align:top;">
                - Columns in this order: Name, Distance From {address}, Rating, Review Count, Hours of Operation, Value Score (1-10), Value Score Rationale
                - For Value Score (1-10): Compare the price versus quality versus customer satisfaction vs portions relative to other restaurants of this type. Utilize Reddit and Google Maps reviews for insight if available.
                - For Value Score Rationale: Use chain of thought logic to justify the Value Score. Use exactly 2-3 short bullets in an HTML <ul><li>...</li></ul>. Quotes from Reddit and Google Maps reviews that support the logic are encouraged.

                Begin generating the table now.

"""

            response = client.models.generate_content(
                model="gemini-2.5-flash-lite",
                contents=prompt,
                config=types.GenerateContentConfig(
                    tools=[grounding_tool],
                    temperature=0.15,
                    max_output_tokens=16384,
                )
            )

            # 2. Process Response
            raw_text = response.text if response.text else ""
            clean_html = re.sub(r'```(?:html)?', '', raw_text).strip()
            table_match = re.search(r'(<table.*?>.*?</table>)', clean_html, re.DOTALL | re.IGNORECASE)

            if table_match:
                research_results = table_match.group(1)
            else:
                research_results = clean_html if len(clean_html) > 10 else "No table found."

            # 3. Capture Usage
            usage_data = {
                "in": response.usage_metadata.prompt_token_count,
                "out": response.usage_metadata.candidates_token_count
            }

            # 4. Email Logic
            msg = EmailMessage()
            msg['Subject'] = f"Food Research: {res_type}"
            msg['From'] = st.secrets["GMAIL_USER"]
            msg['To'] = recipient_email
            msg.set_content("Please enable HTML to view this report.")
            msg.add_alternative(f"<html><body>{research_results}</body></html>", subtype='html')

            with smtplib.SMTP("smtp.gmail.com", port=587) as server:
                server.starttls()
                server.login(st.secrets["GMAIL_USER"], st.secrets["GMAIL_PASS"])
                server.send_message(msg)

            st.success("Research complete and email sent!")

        except Exception as e:
            st.error(f"An error occurred: {e}")
            st.info("Check if your API key or Gmail secrets are correct.")

    # --- 5. DISPLAY SECTION (Always safe now) ---
    if research_results:
        st.markdown(research_results, unsafe_allow_html=True)

    if usage_data:
        st.divider()
        st.subheader("Cost Observation")

        # Wrap in int() to satisfy the type checker and prevent None errors
        in_tokens = int(usage_data.get("in", 0))
        out_tokens = int(usage_data.get("out", 0))

        # Calculate Cost
        est_cost = (in_tokens * 0.0000001) + (out_tokens * 0.0000004)

        c1, c2, c3 = st.columns(3)
        c1.metric("Input Tokens", in_tokens)
        c2.metric("Output Tokens", out_tokens)
        c3.metric("Est. API Cost", f"${est_cost:.5f}")
        st.caption("Note: Does not include flat-rate Google Search grounding fees.")
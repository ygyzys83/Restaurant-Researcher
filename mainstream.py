import streamlit as st
import google.genai as genai
from google.genai import types
import smtplib
import re
from email.message import EmailMessage

# --- UI Header ---
st.title("GT's Grounded Restaurant Researcher v2026")
st.write("Find local spots and get the results emailed to you.")

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

            search_query = f"Highest rated {res_type} restaurants near {address} Google Maps"

            prompt = f"""
                        ACT AS: A local restaurant concierge in 2026.

                        GOAL: 
                        Find UP TO {num_results} real {res_type} restaurants near {address}. 
                        If fewer than {num_results} perfect matches exist, provide as many as possible
                        (at least 1) that strictly meet the rating/review criteria:
                        - Distance: Within {miles} DRIVING miles of this specific address: {address}.
                        - Rating: Minimum {min_rating} stars in GOOGLE MAPS.
                        - Reviews: Minimum {min_reviews} reviews in GOOGLE MAPS.
                        - Verify: Use the search tool to ensure each spot is OPEN in 2026.

                        RULES:
                        1. FORMATTING: Return ONLY a valid HTML table. Do NOT include markdown blocks (```html). Start immediately with <table>.
                        2. STYLING: Use <table style="width:100%; border:1px solid #333; border-collapse:collapse; font-family:sans-serif;">.
                        3. HEADER STYLING: <th style="background-color:#2c3e50; color:white; padding:8px; border:1px solid #333;">.
                        4. CELL STYLING: <td style="padding:8px; border:1px solid #ddd;">.
                        5. COLUMNS: Name, Distance, Rating, Review Count, Value Score (1-10), Value Score Rationale.
                        6. VALUE SCORE RATIONALE FORMAT: The column MUST use an HTML unordered list (<ul><li>...</li></ul>). 
                           NO plain sentences. EXACTLY 2-3 bullets per cell.

                           EXAMPLE OF DESIRED RATIONALE CELL FORMAT:
                                <td>
                                    <ul>
                                        <li>High review-to-rating ratio suggests consistent quality.</li>
                                        <li>Price point is 20% lower than neighborhood average.</li>
                                        <li>Recent 2026 check-ins confirm wait times under 15 mins.</li>
                                    </ul>
                                </td>

                                [Begin Table Generation Now]

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
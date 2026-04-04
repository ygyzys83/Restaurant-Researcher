import streamlit as st
import re
from email.message import EmailMessage
import smtplib
from google import genai
from google.genai import types

# --- Page Config ---
st.set_page_config(page_title="GT's Grounded Restaurant Researcher", layout="wide")
st.title("🍽️ GT's Grounded Restaurant Researcher v2026")
st.write("Find quality local restaurants and get the results emailed to you.")

# --- Sidebar ---
with st.sidebar:
    st.header("Search Parameters")

    res_type = st.text_input("Restaurant Type (e.g. sushi, Italian, vegan)", value="sushi")
    miles = st.number_input("Max Distance (miles)", min_value=1, value=5)
    address = st.text_input("Starting Address", "350 Macarthur Blvd, Oakland, CA")

    min_rating = st.slider("Minimum Google Rating", 1.0, 5.0, 4.0, step=0.1)
    min_reviews = st.number_input("Minimum Review Count", min_value=0, value=100)
    num_results = st.number_input("Number of Results", min_value=1, max_value=10, value=5)

    recipient_email = st.text_input("Recipient Email",
                                    value=st.secrets.get("GMAIL_USER", "godmantan@gmail.com"))

    run_button = st.button("🔍 Research & Email", type="primary")

# --- Main Logic ---
if run_button:
    research_results = None
    usage_data = None

    with st.spinner("Searching live web with Gemini grounding..."):
        try:
            client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

            # Use Google Search grounding (kept as is — it's working for you)
            grounding_tool = types.Tool(google_search=types.GoogleSearch())

            # === IMPROVED SEARCH QUERY ===
            search_query = f"{res_type} restaurants near {address} best highly rated"

            # === MUCH STRONGER PROMPT ===
            prompt = f"""
You are an expert local restaurant researcher in 2026.

Task: Find the **best {res_type} restaurants** near the address: **{address}**

Requirements (strict):
- Focus **only** on {res_type} restaurants (or very close variants like "pizza place", "pizzeria", etc. if {res_type} is pizza).
- They must be within approximately {miles} driving miles of the given address.
- Each restaurant must have **at least {min_rating} stars** on Google Maps.
- Each restaurant must have **at least {min_reviews} reviews** on Google Maps.
- Prioritize places that are currently open or have recent positive activity in 2026.

Return **up to {num_results} restaurants**. 
If fewer than {num_results} fully match all criteria, return as many as possible that come closest (but never return non-{res_type} places just to fill the number).

Output Format:
Return **ONLY** a valid HTML table. Do not include any explanation, markdown, or ```html blocks.
Start directly with the <table> tag.

Table specifications:
- <table style="width:100%; border:1px solid #333; border-collapse:collapse; font-family:sans-serif;">
- Header: <th style="background-color:#2c3e50; color:white; padding:8px; border:1px solid #333;">
- Cells: <td style="padding:8px; border:1px solid #ddd; vertical-align:top;">
- Columns: Name, Distance, Rating, Review Count, Value Score (1-10), Value Score Rationale

For the "Value Score Rationale" column: Use an HTML unordered list with **exactly 2-3 short bullets**. No full sentences.

Example of correct rationale cell:
<td>
    <ul>
        <li>Excellent 4.7 rating with over 800 reviews shows strong consistency.</li>
        <li>Generous portions at reasonable prices for the area.</li>
        <li>Recent 2026 reviews praise fast service and fresh ingredients.</li>
    </ul>
</td>

Now generate the table.
"""

            response = client.models.generate_content(
                model="gemini-2.5-flash-lite",  # or gemini-2.5-flash if you have quota
                contents=prompt,
                config=types.GenerateContentConfig(
                    tools=[grounding_tool],
                    temperature=0.1,  # Lower temperature = more consistent & literal
                )
            )

            # Process response (same as before, slightly cleaned)
            raw_text = response.text or ""
            clean_html = re.sub(r'```(?:html)?\s*', '', raw_text).strip()

            table_match = re.search(r'(<table.*?</table>)', clean_html, re.DOTALL | re.IGNORECASE)
            research_results = table_match.group(1) if table_match else clean_html

            # Usage data
            if hasattr(response, 'usage_metadata') and response.usage_metadata:
                usage_data = {
                    "in": response.usage_metadata.prompt_token_count or 0,
                    "out": response.usage_metadata.candidates_token_count or 0
                }
            else:
                usage_data = {"in": 0, "out": 0}

            # === Email sending (unchanged, but kept for completeness) ===
            msg = EmailMessage()
            msg['Subject'] = f"🍕 Restaurant Research: {res_type.capitalize()} near {address[:50]}"
            msg['From'] = st.secrets["GMAIL_USER"]
            msg['To'] = recipient_email
            msg.set_content("Please view this email with HTML enabled.")
            msg.add_alternative(f"<html><body>{research_results}</body></html>", subtype='html')

            with smtplib.SMTP("smtp.gmail.com", 587) as server:
                server.starttls()
                server.login(st.secrets["GMAIL_USER"], st.secrets["GMAIL_PASS"])
                server.send_message(msg)

            st.success("✅ Research complete and email sent!")

        except Exception as e:
            st.error(f"An error occurred: {e}")

    # Display results
    if research_results:
        st.markdown("### 📋 Research Results")
        st.markdown(research_results, unsafe_allow_html=True)

    if usage_data:
        st.divider()
        st.subheader("Token Usage & Estimated Cost")
        in_tokens = int(usage_data.get("in", 0))
        out_tokens = int(usage_data.get("out", 0))

        # Rough pricing (update if Google changes rates)
        est_cost = (in_tokens * 0.0000001) + (out_tokens * 0.0000004)

        c1, c2, c3 = st.columns(3)
        c1.metric("Input Tokens", in_tokens)
        c2.metric("Output Tokens", out_tokens)
        c3.metric("Est. Cost", f"${est_cost:.6f}")
        st.caption("Note: Does not include Google Search grounding fees.")
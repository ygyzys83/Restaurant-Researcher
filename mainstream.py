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

    with st.spinner("Searching the web with Gemini + Google grounding..."):
        try:
            # 1. Gemini Client
            client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])

            grounding_tool = types.Tool(google_search=types.GoogleSearch())

            search_query = f"Best {res_type} restaurants near {address} with high ratings on Google Maps"

            prompt = f"""
You are a local restaurant concierge in 2026.

Search for UP TO {num_results} restaurants that best match these criteria:
- Within {miles} driving miles of: {address}
- Minimum {min_rating} stars on Google Maps
- At least {min_reviews} Google reviews

Rules:
1. Verify each restaurant is currently open (or has recent 2026 activity).
2. Return ONLY a valid HTML table. Do NOT wrap it in ```html or any markdown.
3. Start directly with <table ...>
4. Use this exact table style:
   <table style="width:100%; border:1px solid #333; border-collapse:collapse; font-family:sans-serif;">
   <th style="background-color:#2c3e50; color:white; padding:8px; border:1px solid #333;">
   <td style="padding:8px; border:1px solid #ddd;">
5. Columns: Name, Distance, Rating, Review Count, Value Score (1-10), Value Score Rationale
6. For the Rationale column: Use an HTML <ul><li>...</li></ul> with exactly 2-3 concise bullets. No plain text paragraphs.

Begin generating the table now.
"""

            response = client.models.generate_content(
                model="gemini-2.5-flash-lite",
                contents=prompt,
                config=types.GenerateContentConfig(
                    tools=[grounding_tool],
                    temperature=0.2,
                )
            )

            # 2. Process the HTML response
            raw_text = response.text or ""
            # Clean possible markdown fences
            clean_html = re.sub(r'```(?:html)?\s*', '', raw_text).strip()

            # Extract the table if present
            table_match = re.search(r'(<table.*?</table>)', clean_html, re.DOTALL | re.IGNORECASE)
            research_results = table_match.group(1) if table_match else clean_html

            # 3. Usage stats
            if hasattr(response, 'usage_metadata') and response.usage_metadata:
                usage_data = {
                    "in": response.usage_metadata.prompt_token_count or 0,
                    "out": response.usage_metadata.candidates_token_count or 0
                }
            else:
                usage_data = {"in": 0, "out": 0}

            # 4. Send Email
            msg = EmailMessage()
            msg['Subject'] = f"🍽️ Restaurant Research: {res_type.capitalize()} near {address[:40]}..."
            msg['From'] = st.secrets["GMAIL_USER"]
            msg['To'] = recipient_email
            msg.set_content("Please view this email in an HTML-capable client.")
            msg.add_alternative(f"<html><body>{research_results}</body></html>", subtype='html')

            # FIXED SMTP connection
            with smtplib.SMTP("smtp.gmail.com", port=587) as server:
                server.starttls()
                server.login(st.secrets["GMAIL_USER"], st.secrets["GMAIL_PASS"])
                server.send_message(msg)

            st.success("✅ Research complete and email sent successfully!")

        except Exception as e:
            st.error(f"An error occurred: {e}")
            if "getaddrinfo" in str(e).lower() or "smtp" in str(e).lower():
                st.info("**Tip:** This is usually a network/DNS issue or typo in the SMTP server name. "
                        "Make sure you're not behind a restrictive firewall/VPN.")
            elif "API key" in str(e).lower() or "auth" in str(e).lower():
                st.info("Check your GEMINI_API_KEY or Gmail credentials in `.streamlit/secrets.toml`")
            else:
                st.info("Check your secrets and internet connection.")

    # --- Display Results (outside the spinner) ---
    if research_results:
        st.markdown("### Research Results")
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
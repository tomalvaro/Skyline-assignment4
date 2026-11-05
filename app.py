import httpx
import streamlit as st
from openai import OpenAI
from PIL import Image

# Page settings (must be the first Streamlit command)
st.set_page_config(page_title="SkyBot | Skyline Chili Oxford", page_icon="🌶️")

st.title("SkyBot: Skyline Chili Oxford")
st.caption(
    "Order Cincinnati chili and get answers about Skyline Chili, One East High St., Oxford, OH. "
    "Student class project (ISA 414), not affiliated with Skyline Chili. "
    "Prices may differ from the store; the register price is final."
)

# Initialize OpenAI client
@st.cache_resource
def get_openai_client(api_key):
    return OpenAI(
        api_key=api_key,
        http_client=httpx.Client()
    )

client = get_openai_client(st.secrets["OPENAI_API_KEY"])

# System instructions (grounding text stored in Streamlit secrets)
grounding = st.secrets["GROUNDING"]

# Display logo
image = Image.open("logo.png")
st.image(image, width=220)

# Initialize model
if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "gpt-5-mini"

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Sidebar: quick info and a button to start a fresh order
with st.sidebar:
    st.subheader("Skyline Chili Oxford")
    st.markdown(
        "One East High Street  \n"
        "Oxford, OH 45056  \n"
        "(513) 523-3330\n\n"
        "**Hours**  \n"
        "Mon to Sat: 10:30 AM to 9:00 PM  \n"
        "Sun: 11:00 AM to 9:00 PM"
    )
    if st.button("Start a new order"):
        st.session_state.messages = []
        st.rerun()


def show(text):
    # Streamlit treats a pair of $ signs as LaTeX math, which breaks prices like $3.53.
    # Escaping the $ keeps prices displayed correctly.
    return text.replace("$", "\\$")


# Display conversation history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(show(message["content"]))

# User input
if prompt := st.chat_input("What can I get for you today? (e.g., a regular 3-Way and two cheese coneys)"):

    st.session_state.messages.append(
        {"role": "user", "content": prompt}
    )

    with st.chat_message("user"):
        st.markdown(show(prompt))

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""

        try:
            response = client.responses.create(
                model=st.session_state["openai_model"],
                instructions=grounding,
                input=[
                    {
                        "role": m["role"],
                        "content": m["content"]
                    }
                    for m in st.session_state.messages
                ],
                reasoning={"effort": "low"},  # faster replies, fewer (billed) reasoning tokens
                stream=True,
            )

            for event in response:
                if event.type == "response.output_text.delta":
                    full_response += event.delta

                    message_placeholder.markdown(
                        show(full_response) + "▌"
                    )

            message_placeholder.markdown(show(full_response))

            # Save assistant response
            st.session_state.messages.append(
                {
                    "role": "assistant",
                    "content": full_response
                }
            )

        except Exception as e:
            st.error(f"OpenAI API error: {e}")
            st.session_state.messages.pop()

import requests
import streamlit as st


API_URL = "http://localhost:8000/query"


st.set_page_config(
    page_title="LibraAI",
    page_icon="📚",
    layout="centered",
)


# -----------------------------
# Page Header
# -----------------------------

st.title("📚 LibraAI")
st.caption("University Library Research Assistant")

st.markdown(
    "Ask a question and get a concise answer grounded in the available "
    "library materials."
)


# -----------------------------
# Session History
# -----------------------------

if "messages" not in st.session_state:
    st.session_state.messages = []


# -----------------------------
# Display Previous Messages
# -----------------------------

for message in st.session_state.messages:

    if message["role"] == "user":
        with st.chat_message("user"):
            st.write(message["content"])

    else:
        with st.chat_message("assistant"):

            if message["refused"]:
                st.warning("⚠️ Not covered")
                st.write(message["answer"])

            else:
                st.success("💡 Answer")
                st.write(message["answer"])

                citations = message.get("citations", [])

                if citations:
                    st.info("📚 Sources")

                    for citation in citations:
                        st.markdown(
                            f"""
                            **📄 {citation["doc_title"]}**

                            Page: {citation["page_number"]}  
                            Section: {citation["section"]}
                            """
                        )


# -----------------------------
# Question Input
# -----------------------------

question = st.chat_input(
    "Ask a question about the library materials..."
)


# -----------------------------
# Send Question
# -----------------------------

if question:

    # Display user question immediately
    st.session_state.messages.append(
        {
            "role": "user",
            "content": question,
        }
    )

    try:

        response = requests.post(
            API_URL,
            json={"query": question},
            timeout=30,
        )

        response.raise_for_status()

        data = response.json()

        answer = data.get("answer", "")
        citations = data.get("citations", [])
        refused = data.get("refused", False)

        # Store assistant response in session history
        st.session_state.messages.append(
            {
                "role": "assistant",
                "answer": answer,
                "citations": citations,
                "refused": refused,
            }
        )

    except requests.exceptions.ConnectionError:

        st.session_state.messages.append(
            {
                "role": "assistant",
                "answer": (
                    "Unable to connect to the LibraAI backend. "
                    "Please make sure the FastAPI server is running."
                ),
                "citations": [],
                "refused": True,
            }
        )

    except requests.exceptions.RequestException as error:

        st.session_state.messages.append(
            {
                "role": "assistant",
                "answer": f"Request failed: {error}",
                "citations": [],
                "refused": True,
            }
        )

    # Rerun so the newly added messages are displayed
    st.rerun()
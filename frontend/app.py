
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import requests
import streamlit as st

from config.settings import QUERY_ENDPOINT

API_URL = QUERY_ENDPOINT


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

                    # Count distinct documents.
                    document_count = message.get(
                        "source_document_count",
                        len({
                            citation.get("doc_title", "")
                            for citation in citations
                            if citation.get("doc_title")
                        }),
                    )

                    if document_count > 1:
                        st.caption(
                            f"📚 This answer draws on "
                            f"{document_count} different documents."
                        )
                    elif document_count == 1:
                        st.caption(
                            "📚 This answer draws on 1 document."
                        )

                    for index, citation in enumerate(citations, start=1):
                        title = citation.get(
                            "doc_title",
                            "Untitled document",
                        )
                        page = citation.get("page_number", "Unknown")
                        section = citation.get("section", "General")
                        chunk_text = citation.get("chunk_text")

                        with st.expander(
                            f"📄 {title} — Page {page}",
                            expanded=False,
                        ):
                            st.markdown(f"**Section:** {section}")

                            if chunk_text and chunk_text.strip():
                                st.markdown("**Retrieved source text:**")
                                st.write(chunk_text)
                            else:
                                st.caption(
                                    "Source text is not available for "
                                    "this citation."
                                )

                            source_path = citation.get("source_path")
                            if source_path:
                                st.caption(f"Source file: {source_path}")

                            chunk_id = citation.get("chunk_id")
                            if chunk_id:
                                st.caption(f"Chunk ID: {chunk_id}")


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
        document_count = data.get(
            "source_document_count",
            len({
                citation.get("doc_title", "")
                for citation in citations
                if citation.get("doc_title")
            }),
        )

        st.session_state.messages.append(
            {
                "role": "assistant",
                "answer": answer,
                "citations": citations,
                "refused": refused,
                "source_document_count": document_count,
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
                "source_document_count": 0,
            }
        )

    except requests.exceptions.Timeout:
        st.session_state.messages.append(
            {
                "role": "assistant",
                "answer": (
                    "The request timed out. Please try again."
                ),
                "citations": [],
                "refused": True,
                "source_document_count": 0,
            }
        )

    except requests.exceptions.HTTPError as error:
        st.session_state.messages.append(
            {
                "role": "assistant",
                "answer": (
                    f"The backend returned an error: {error.response.status_code}. "
                    "Please check the server logs and try again."
                ),
                "citations": [],
                "refused": True,
                "source_document_count": 0,
            }
        )

    except requests.exceptions.RequestException as error:
        st.session_state.messages.append(
            {
                "role": "assistant",
                "answer": f"Request failed: {error}",
                "citations": [],
                "refused": True,
                "source_document_count": 0,
            }
        )

    except ValueError:
        st.session_state.messages.append(
            {
                "role": "assistant",
                "answer": (
                    "The backend returned an invalid response. "
                    "Please try again."
                ),
                "citations": [],
                "refused": True,
                "source_document_count": 0,
            }
        )

    st.rerun()
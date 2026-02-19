import streamlit as st
import PyPDF2
import os
from io import BytesIO
from dotenv import load_dotenv

# Optional Groq client check
try:
    from groq import Groq
    _HAS_GROQ = True
except Exception:
    _HAS_GROQ = False

# Load environment variables
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Streamlit input for Groq key (if not set in env)
if not GROQ_API_KEY:
    groq_input = st.sidebar.text_input("GROQ API Key (optional)", type="password")
    if groq_input:
        os.environ["GROQ_API_KEY"] = groq_input
        GROQ_API_KEY = groq_input

# App title and config
st.set_page_config(page_title="Resource AI Assistant", page_icon="📚", layout="wide")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "pdf_text" not in st.session_state:
    st.session_state.pdf_text = ""
if "pdf_name" not in st.session_state:
    st.session_state.pdf_name = "No document loaded"
if "active_resource" not in st.session_state:
    st.session_state.active_resource = None


# Function to extract text from PDF
def extract_text_from_pdf(uploaded_file):
    try:
        pdf_reader = PyPDF2.PdfReader(uploaded_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        return text
    except Exception as e:
        st.error(f"Error extracting text: {e}")
        return ""


# Function to get AI response
def get_ai_response(prompt, context=""):
    system_content = """You are a helpful AI assistant that answers questions about documents and web resources.
        Respond concisely but helpfully to user queries."""

    if context:
        system_content += f"\n\nCurrent resource context:\n{context}"

    if not _HAS_GROQ or not os.getenv("GROQ_API_KEY"):
        return "Error: Groq SDK not available or GROQ_API_KEY not set. Please set GROQ_API_KEY in your .env or the sidebar."

    MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

    # Try official groq client first (if installed)
    try:
        from groq import Groq
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        completion = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_content},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1024,
            stream=False
        )
        # Extract text from response object
        try:
            choice = completion.choices[0]
            if hasattr(choice, 'message') and getattr(choice.message, 'content', None):
                return choice.message.content
            if hasattr(choice, 'delta') and getattr(choice.delta, 'content', None):
                return choice.delta.content
        except Exception:
            pass
        return str(completion)
    except Exception as e_client:
        # Fall back to langchain_groq's ChatGroq wrapper if available
        try:
            # cache LLM in session
            if "groq_llm" not in st.session_state:
                st.session_state.groq_llm = ChatGroq(model_name=MODEL, temperature=0)
            llm = st.session_state.groq_llm

            # Try explicit, non-callable invocation methods only
            if hasattr(llm, 'predict'):
                try:
                    return llm.predict(system_content + "\n\n" + prompt)
                except Exception as e_pred:
                    return f"Error calling llm.predict: {e_pred}"

            if hasattr(llm, 'generate'):
                try:
                    gen = llm.generate([system_content + "\n\n" + prompt])
                    if hasattr(gen, 'generations'):
                        try:
                            return gen.generations[0][0].text
                        except Exception:
                            return str(gen)
                    return str(gen)
                except Exception as e_gen:
                    return f"Error calling llm.generate: {e_gen}"

            if hasattr(llm, 'chat'):
                try:
                    out = llm.chat([{"role": "system", "content": system_content}, {"role": "user", "content": prompt}])
                    return str(out)
                except Exception as e_chat:
                    return f"Error calling llm.chat: {e_chat}"

            return f"Error: ChatGroq available but has no known invocation methods. Client error: {e_client}. llm repr: {repr(llm)}"
        except Exception as e_fallback:
            return f"Error invoking Groq client and ChatGroq fallback failed: {e_client}; {e_fallback}"


# Sidebar for resource management
with st.sidebar:
    st.title("Resource Navigator")
    st.divider()

    # GROQ API key input (runtime prompt)
    if not GROQ_API_KEY:
        groq_input = st.text_input("GROQ API Key (optional)", type="password")
        if groq_input:
            os.environ["GROQ_API_KEY"] = groq_input
            GROQ_API_KEY = groq_input
            st.success("GROQ API key set for this session")
    else:
        st.caption("GROQ key loaded from environment")

    # Document uploader
    uploaded_file = st.file_uploader(
        "Upload a document",
        type=["pdf"],
        help="Upload a PDF file to analyze its content"
    )

    if uploaded_file is not None:
        # Process PDF
        with st.spinner("Extracting text from document..."):
            st.session_state.pdf_text = extract_text_from_pdf(uploaded_file)
            st.session_state.pdf_name = uploaded_file.name
            st.session_state.active_resource = {
                "type": "document",
                "name": uploaded_file.name,
                "content": st.session_state.pdf_text[:10000]  # Store first 10k chars
            }

        st.success(f"Document loaded: {uploaded_file.name}")
        st.caption(f"Text characters extracted: {len(st.session_state.pdf_text)}")

        # Show document info
        with st.expander("Document Preview"):
            if st.session_state.pdf_text:
                st.text_area(
                    "Extracted Text",
                    value=st.session_state.pdf_text[:2000] + (
                        "..." if len(st.session_state.pdf_text) > 2000 else ""),
                    height=300,
                    disabled=True
                )
            else:
                st.warning("No text could be extracted from this document")

# Main chat interface
current_resource = st.session_state.active_resource[
    "name"] if st.session_state.active_resource else "No resource selected"
st.title(f"📚 Resource AI Assistant - {current_resource}")

# Display resource info if selected
if st.session_state.active_resource:
    with st.expander("Current Resource Details", expanded=False):
        if st.session_state.active_resource["type"] == "document":
            st.write(f"**Document:** {st.session_state.active_resource['name']}")
            st.caption(f"{len(st.session_state.active_resource['content'])} characters available for context")
        else:
            st.write(f"**Link:** {st.session_state.active_resource['name']}")
            st.write(f"**URL:** {st.session_state.active_resource['url']}")
            st.write(f"**Category:** {st.session_state.active_resource['category']}")

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input(f"Ask about {current_resource}..."):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)

    # Get context based on active resource
    context = ""
    if st.session_state.active_resource:
        if st.session_state.active_resource["type"] == "document":
            context = st.session_state.active_resource["content"]
        else:
            context = f"Link: {st.session_state.active_resource['name']}\nURL: {st.session_state.active_resource['url']}"

    # Display assistant response
    with st.chat_message("assistant"):
        with st.spinner("Analyzing..."):
            response = get_ai_response(prompt, context)

        st.markdown(response)

    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response})

# Instructions when no resource is selected
if not st.session_state.active_resource:
    st.info("Please upload a document or select a link in the sidebar to begin chatting with the AI")

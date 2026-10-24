import streamlit as st
from openai import OpenAI, AuthenticationError, OpenAIError
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

st.set_page_config(page_title="Nova AI", page_icon="✨", layout="wide")

st.markdown("""
<style>


/* Force the entire bottom area to dark */
[data-testid="stBottom"],
[data-testid="stBottom"] > div,
[data-testid="stBottomBlockContainer"],
[data-testid="stBottomBlockContainer"] > div,
.stBottom,
.stBottom > div {
    background: #0B0E17 !important;
    background-color: #0B0E17 !important;
    background-image: none !important;
}

/* Chat input outer container */
[data-testid="stChatInput"],
[data-testid="stChatInput"] > div {
    background: #1B2233 !important;
    background-color: #1B2233 !important;
    border-radius: 16px !important;
}

/* Chat input text */
[data-testid="stChatInput"] textarea {
    background: transparent !important;
    color: #F4F4FF !important;
    -webkit-text-fill-color: #F4F4FF !important;
}

/* Chat input placeholder */
[data-testid="stChatInput"] textarea::placeholder {
    color: #9CA3AF !important;
    -webkit-text-fill-color: #9CA3AF !important;
}

/* Bottom fade/overlay */
[data-testid="stBottom"]::before,
[data-testid="stBottom"]::after {
    background: #0B0E17 !important;
    background-image: none !important;
}



/* Page and sidebar */
.stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] {background:#0B0E17 !important;color:#F4F4FF !important;}
[data-testid="stHeader"] {background:#0B0E17 !important;}
[data-testid="stSidebar"] {background:#151A29 !important;border-right:1px solid #2B3245;}
.block-container {max-width:950px;padding-top:2.2rem;padding-bottom:7rem;}
/* Fixed bottom input: both the sticky container and its inner layers */
[data-testid="stBottom"], [data-testid="stBottom"] > div,
[data-testid="stBottomBlockContainer"], [data-testid="stChatInputContainer"] {
 background:#0B0E17 !important;
}
[data-testid="stBottom"] {border-top:0 !important;}
[data-testid="stChatInput"] {background:#1B2233 !important;border:1px solid #46516D !important;border-radius:18px !important;box-shadow:0 8px 30px #0005;}
[data-testid="stChatInput"] textarea, [data-testid="stChatInput"] textarea:focus {background:#1B2233 !important;color:#F4F4FF !important;caret-color:#C3A9FF !important;}
[data-testid="stChatInput"] textarea::placeholder {color:#A4AEC5 !important;}
[data-testid="stChatInput"] button {color:#C6B3FF !important;}
/* Inputs, widgets and buttons */
.stTextInput input,.stTextArea textarea {background:#222A3D !important;color:#F4F4FF !important;border-radius:12px !important;}
.stButton > button, .stFormSubmitButton > button {border-radius:13px;background:#242B3D;color:#F4F4FF;border:1px solid #3A4561;min-height:44px;}
.stButton > button:hover,.stFormSubmitButton > button:hover {background:#353C56;color:white;border-color:#9B83FF;}
button[kind="primary"] {background:linear-gradient(100deg,#6559F4,#9A66FA) !important;color:white !important;border:none !important;}
[data-testid="stChatMessage"] {background:#171D2C;border:1px solid #2B344A;border-radius:16px;padding:15px;margin-bottom:10px;}
/* Accent typography */
.nova-welcome {text-align:center;padding:65px 0 26px;}
.nova-welcome h1 {font-size:clamp(2.1rem,4vw,3.1rem);font-weight:800;letter-spacing:-.04em;background:linear-gradient(90deg,#B9A1FF,#7BCBFF);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:12px;}
.nova-welcome p,.nova-subtitle {color:#A3ABC1;font-size:1rem;}
.nova-brand {font-size:1.6rem;font-weight:800;letter-spacing:-.03em;}
.login-head {text-align:center;margin:65px auto 32px;}
.login-head h1 {font-size:3rem;color:#B5A0FF;}
.login-head p {color:#A3ABC1;}
@media(max-width:650px){.nova-welcome{padding:35px 0 15px;}.block-container{padding-top:1rem;}}
</style>
""", unsafe_allow_html=True)

# Session state survives Streamlit reruns (not server restarts).
if "api_key" not in st.session_state:
    st.session_state.api_key = None
if "chats" not in st.session_state:
    st.session_state.chats = {1: {"title": "New Chat", "messages": []}}
if "current_chat" not in st.session_state:
    st.session_state.current_chat = 1
if "next_chat_id" not in st.session_state:
    st.session_state.next_chat_id = 2

# API key gate
if not st.session_state.api_key:
    st.markdown('<div class="login-head"><h1>✦ Nova AI</h1><p>Your personal intelligent workspace</p><h2>Welcome back 👋</h2><p>Enter your OpenAI API key to continue</p></div>', unsafe_allow_html=True)
    _, center, _ = st.columns([1, 1.5, 1])
    with center:
        with st.form("login_form"):
            key = st.text_input("OpenAI API key", type="password", placeholder="sk-...")
            login = st.form_submit_button("🔐 Verify and continue", type="primary", use_container_width=True)
        if login:
            if not key.strip():
                st.warning("Enter an API key first.")
            else:
                with st.spinner("Checking your API key..."):
                    try:
                        OpenAI(api_key=key.strip(), timeout=15).models.list()
                        st.session_state.api_key = key.strip()
                        st.rerun()
                    except AuthenticationError:
                        st.error("OpenAI rejected this API key.")
                    except OpenAIError:
                        st.error("Could not verify the key. Check your connection or API account and retry.")
                    except Exception:
                        st.error("Connection failed. Please try again.")
        st.caption("The key is kept in this Streamlit session, not saved to a file. Verification does not guarantee model access or available credits.")
    st.stop()

with st.sidebar:
    st.markdown('<div class="nova-brand">✨ Nova AI</div>', unsafe_allow_html=True)
    st.caption("Your personal AI workspace")
    st.divider()
    if st.button("＋ New Chat", type="primary", use_container_width=True):
        new_id = st.session_state.next_chat_id
        st.session_state.chats[new_id] = {"title": "New Chat", "messages": []}
        st.session_state.current_chat = new_id
        st.session_state.next_chat_id += 1
        st.rerun()

    st.markdown("#### 🕘 Recent chats")
    for chat_id, data in reversed(list(st.session_state.chats.items())):
        title = data["title"]
        if st.button("💬 " + title, key=f"chat_{chat_id}", use_container_width=True):
            st.session_state.current_chat = chat_id
            st.rerun()

    st.divider()
    with st.expander("⚙️ Settings"):
        model_name = st.selectbox("Model", ["gpt-4o-mini", "gpt-4o"])
        system_role = st.text_area("System instructions", "You are a helpful and friendly AI assistant.", height=100)

    if st.button("🧹 Clear conversation", use_container_width=True):
        data = st.session_state.chats[st.session_state.current_chat]
        data["messages"] = []
        data["title"] = "New Chat"
        st.rerun()

    if st.button("🗑️ Delete chat", use_container_width=True):
        del st.session_state.chats[st.session_state.current_chat]
        if not st.session_state.chats:
            new_id = st.session_state.next_chat_id
            st.session_state.chats[new_id] = {"title": "New Chat", "messages": []}
            st.session_state.next_chat_id += 1
        st.session_state.current_chat = list(st.session_state.chats)[-1]
        st.rerun()

    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.api_key = None
        # Clear private conversations on logout too.
        st.session_state.chats = {1: {"title": "New Chat", "messages": []}}
        st.session_state.current_chat = 1
        st.session_state.next_chat_id = 2
        st.rerun()

chat_data = st.session_state.chats[st.session_state.current_chat]
messages = chat_data["messages"]

st.markdown("## ✨ Nova AI")
st.caption("Your intelligent assistant, powered by OpenAI")
st.divider()

suggested_prompt = None
if not messages:
    st.markdown('<div class="nova-welcome"><h1>How can I help you today?</h1><p>Ask anything. Create something amazing.</p></div>', unsafe_allow_html=True)
    st.markdown("#### ✨ Try asking")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("💡 Explain Agentic AI", use_container_width=True):
            suggested_prompt = "Explain Agentic AI in simple words."
        if st.button("🐍 Help me learn Python", use_container_width=True):
            suggested_prompt = "Help me learn Python programming."
    with col2:
        if st.button("📚 Explain RAG", use_container_width=True):
            suggested_prompt = "Explain RAG and vector databases."
        if st.button("🚀 Suggest AI project ideas", use_container_width=True):
            suggested_prompt = "Suggest beginner-friendly AI project ideas."

for message in messages:
    if isinstance(message, HumanMessage):
        with st.chat_message("user", avatar="👤"):
            st.markdown(message.content)
    elif isinstance(message, AIMessage):
        with st.chat_message("assistant", avatar="✨"):
            st.markdown(message.content)

user_prompt = st.chat_input("Message Nova AI...") or suggested_prompt
if user_prompt:
    if not messages:
        chat_data["title"] = user_prompt[:35] + ("..." if len(user_prompt) > 35 else "")
    user_message = HumanMessage(content=user_prompt)
    with st.chat_message("user", avatar="👤"):
        st.markdown(user_prompt)
    with st.chat_message("assistant", avatar="✨"):
        with st.spinner("Nova is thinking..."):
            try:
                llm = ChatOpenAI(model=model_name, api_key=st.session_state.api_key, temperature=0.5)
                response = llm.invoke([SystemMessage(content=system_role)] + messages + [user_message])
                st.markdown(response.content)
                messages.extend([user_message, AIMessage(content=response.content)])
            except AuthenticationError:
                st.error("Your API key was rejected. Log out and verify a new key.")
            except Exception as error:
                st.error(f"Could not generate a response: {error}")
    st.rerun()

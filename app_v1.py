import streamlit as st
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent
from langchain_openai import AzureChatOpenAI
import os

# ==========================================
# 1. CONFIGURATION
# ==========================================

# SET YOUR AZURE KEYS HERE OR IN ENVIRONMENT VARIABLES
# You can find these in your Azure Portal -> OpenAI Resource -> Keys and Endpoint
os.environ["AZURE_OPENAI_API_KEY"] = "4pF9FhQyfFU3YCRo0tWl5fuTyOksoK3wSXRQXznk6YazyikAoODCJQQJ99BJACfhMk5XJ3w3AAABACOGVMXX"
os.environ["AZURE_OPENAI_ENDPOINT"] = "https://sherrie-gpt4.cognitiveservices.azure.com/"
os.environ["OPENAI_API_VERSION"] = "2024-12-01-preview"   # 可根据你 Azure Portal 上的版本调整
DEPLOYMENT_NAME = "gpt-4o"  # 比如 gpt-4o-mini 或 gpt-4o

# Page Config
st.set_page_config(page_title="CompAI - Level Insights", page_icon="💰")

# ==========================================
# 2. INITIALIZE AI ENGINE
# ==========================================

@st.cache_resource
def get_agent():
    # Connect to the local SQLite database
    db = SQLDatabase.from_uri("sqlite:///salaries.db")

    # Initialize Azure OpenAI
    llm = AzureChatOpenAI(
        deployment_name=DEPLOYMENT_NAME,
        temperature=0,
        verbose=True
    )

    # Create the SQL Agent (The Brain)
    # agent_type="openai-tools" is optimized for tool calling
    agent_executor = create_sql_agent(
        llm=llm,
        db=db,
        agent_type="openai-tools",
        verbose=True
    )
    
    return agent_executor

try:
    agent = get_agent()
except Exception as e:
    st.error(f"Error connecting to Azure OpenAI: {e}")
    st.stop()

# ==========================================
# 3. USER INTERFACE
# ==========================================

st.title("💰 Tech Compensation AI")
st.markdown("Ask about salaries, compare companies, or find level details. (Powered by Azure OpenAI)")

# Sidebar with schema info
with st.sidebar:
    st.header("Data available for:")
    st.write("- Google, Meta, Amazon, Apple, Microsoft")
    st.write("- Locations: Seattle, SF, NY, Austin")
    st.info("Example Query:\n'Compare the average total comp for Google L5 vs Meta E5 in Seattle.'")

# Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display previous messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat Input
if prompt := st.chat_input("Ask about compensation..."):
    # 1. Display user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. AI "Thinking" and Response
    with st.chat_message("assistant"):
        with st.spinner("Analyzing salary database..."):
            try:
                # This is where the magic happens: Text -> SQL -> Data -> Text
                response = agent.invoke(prompt)
                output_text = response["output"]
                st.markdown(output_text)
                
                # Save to history
                st.session_state.messages.append({"role": "assistant", "content": output_text})
            except Exception as e:
                st.error(f"I couldn't fetch that data. Error: {str(e)}")
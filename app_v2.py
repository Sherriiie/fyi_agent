import streamlit as st
import pandas as pd
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent
from langchain_openai import AzureChatOpenAI
from langchain_core.tools import tool
import os

# ==========================================
# 1. CONFIGURATION
# ==========================================

# --- UPDATE YOUR KEYS HERE ---
os.environ["AZURE_OPENAI_API_KEY"] = "4pF9FhQyfFU3YCRo0tWl5fuTyOksoK3wSXRQXznk6YazyikAoODCJQQJ99BJACfhMk5XJ3w3AAABACOGVMXX"
os.environ["AZURE_OPENAI_ENDPOINT"] = "https://sherrie-gpt4.cognitiveservices.azure.com/"
os.environ["OPENAI_API_VERSION"] = "2024-12-01-preview"   # 可根据你 Azure Portal 上的版本调整
DEPLOYMENT_NAME = "gpt-4o"  # 比如 gpt-4o-mini 或 gpt-4o

st.set_page_config(page_title="CompAI - Level Insights", page_icon="💰")

# ==========================================
# 2. DEFINE THE CHARTING TOOL
# ==========================================

# We define the DB connection globally so the tool can access it
db_path = "sqlite:///salaries.db"
db = SQLDatabase.from_uri(db_path)


@tool
def generate_bar_chart(query: str):
    """
    Useful when the user asks to compare companies or levels visually.
    Input: A valid SQL query that selects a Label column (like company or level) and a Numerical column (like average salary).
    Example Input: "SELECT company, AVG(total_comp) as avg_comp FROM compensation GROUP BY company"
    """
    try:
        # 1. Execute the SQL query into a Pandas DataFrame
        # We use SQLAlchemy engine from the LangChain DB object
        import sqlalchemy
        engine = sqlalchemy.create_engine(db_path)
        df = pd.read_sql(query, engine)

        # 2. Check if data exists
        if df.empty:
            return "No data found to chart."

        # 3. Clean up column names for the chart
        # We assume the first column is the Category (X-axis) and the last is Value (Y-axis)
        x_col = df.columns[0]
        y_col = df.columns[-1]

        # 4. Render the chart in Streamlit immediately
        st.write(f"### 📊 Comparison Chart: {x_col} vs {y_col}")
        st.bar_chart(df.set_index(x_col)[y_col])

        return "Chart successfully displayed to the user."
    except Exception as e:
        return f"Error generating chart: {e}"


# ==========================================
# 3. INITIALIZE AI ENGINE
# ==========================================

@st.cache_resource
def get_agent():
    llm = AzureChatOpenAI(
        deployment_name=DEPLOYMENT_NAME,
        temperature=0,
        verbose=True
    )

    # We pass the extra tool to the agent
    agent_executor = create_sql_agent(
        llm=llm,
        db=db,
        agent_type="openai-tools",
        verbose=True,
        extra_tools=[generate_bar_chart]  # <--- This adds the charting capability
    )

    return agent_executor


try:
    agent = get_agent()
except Exception as e:
    st.error(f"Error connecting to Azure OpenAI: {e}")
    st.stop()

# ==========================================
# 4. USER INTERFACE
# ==========================================

st.title("💰 Tech Compensation AI")
st.caption("Powered by Azure OpenAI + SQL + Streamlit")

# Sidebar
with st.sidebar:
    st.header("Capabilities")
    st.markdown("""
    - **Search:** Find specific salaries.
    - **Compare:** "Compare Google L5 vs Meta E5"
    - **Visualize:** "Show me a chart of average salaries by company"
    """)

# Chat History Initialization
if "messages" not in st.session_state:
    st.session_state.messages = []

# Redisplay Chat History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        # If the content was a chart, we can't easily "re-render" the dynamic chart from history string alone
        # in this simple version, so we just show the text.
        # (To persist charts, we'd need complex session state management, but this works for the active turn).
        st.markdown(message["content"])

# Chat Input
if prompt := st.chat_input("Ask about compensation..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                # Custom instructions to force chart usage on specific keywords
                final_prompt = prompt
                if "compare" in prompt.lower() or "chart" in prompt.lower() or "visualize" in prompt.lower():
                    final_prompt += " (If this involves comparing numbers or visualizing data, please use the generate_bar_chart tool.)"

                response = agent.invoke(final_prompt)
                output_text = response["output"]
                st.markdown(output_text)

                st.session_state.messages.append({"role": "assistant", "content": output_text})
            except Exception as e:
                st.error(f"Error: {str(e)}")
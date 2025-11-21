import streamlit as st
import pandas as pd
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent
from langchain_openai import AzureChatOpenAI
from langchain_core.tools import tool
from langchain_core.prompts import SystemMessagePromptTemplate, ChatPromptTemplate
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
# 2. CUSTOM INSTRUCTIONS (THE "CONSTITUTION")
# ==========================================

# This is the most important part for your request.
# We tell the AI how to behave before it even sees the user's question.
SYSTEM_INSTRUCTIONS = """
You are an expert Compensation Analyst AI. Your job is to provide insights, not raw data dumps.

CRITICAL RULES:
1. **AGGREGATION ONLY:** NEVER return a list of raw individual records (rows). If the user asks for "offers" or "salaries", you must calculate the AVERAGE (AVG), MEDIAN, or RANGE (MIN/MAX).
2. **GROUPING:** If the user asks a broad question like "Microsoft offers", group the results by 'Level_Name' or 'Level_Code' and return the average Total Compensation for each level.
3. **ABBREVIATIONS:** Understand these mappings:
   - 'ms', 'msft' -> Microsoft
   - 'goog' -> Google
   - 'fb', 'meta' -> Meta
   - 'amzn' -> Amazon
   - '阿里' -> 阿里巴巴
   - '字节' -> 字节跳动
   - 'tencent' -> 腾讯
   - 'baidu' -> 百度
   - 'meituan' -> 美团
   - 'huawei' -> 华为
   - 'pinduoduo' -> 拼多多
   - 'jd' -> 京东

4. **FORMATTING:** Format money with the appropriate currency symbol based on the location/currency column. Use '$' for USD/CAD, '¥' for CNY. Do not convert currencies unless asked.
5. **PRIVACY:** If a query would return a specific individual's data, refuse and offer an aggregate instead.
6. **Available companies**: Microsoft, 字节跳动，腾讯，阿里巴巴，百度，美团，华为，拼多多，京东。

When using the 'generate_bar_chart' tool, ensure the SQL query creates a summary table (e.g., Group By Level), not raw rows.
"""

# ==========================================
# 3. TOOLS & DATABASE
# ==========================================

db_path = "sqlite:///salaries.db"
db = SQLDatabase.from_uri(db_path)

@tool
def generate_bar_chart(query: str):
    """
    Useful when the user wants to see a visual comparison (charts/graphs).
    Input: A valid SQL query that creates a summary (e.g., SELECT company, AVG(total_comp) FROM ... GROUP BY company).
    """
    try:
        import sqlalchemy
        engine = sqlalchemy.create_engine(db_path)
        df = pd.read_sql(query, engine)
        
        if df.empty:
            return "No data found to chart."

        # Heuristic: If the dataframe is too big (raw rows), we warn the agent
        if len(df) > 20:
            return "Error: The query returned too many rows. Please group the data (e.g., by Level or Company) before charting."

        x_col = df.columns[0] 
        y_col = df.columns[-1]
        
        st.write(f"### 📊 {x_col} vs {y_col}")
        st.bar_chart(df.set_index(x_col)[y_col])
        
        return "Chart displayed successfully."
    except Exception as e:
        return f"Error generating chart: {e}"

# ==========================================
# 4. INITIALIZE AI ENGINE
# ==========================================

@st.cache_resource
def get_agent():
    llm = AzureChatOpenAI(
        deployment_name=DEPLOYMENT_NAME,
        temperature=0,
        verbose=True
    )

    # We inject our Custom System Instructions into the agent's prompt suffix
    agent_executor = create_sql_agent(
        llm=llm,
        db=db,
        agent_type="openai-tools",
        verbose=True,
        extra_tools=[generate_bar_chart],
        # 'suffix' is appended to the system prompt instructions
        suffix=SYSTEM_INSTRUCTIONS
    )
    
    return agent_executor

try:
    agent = get_agent()
except Exception as e:
    st.error(f"Error connecting to Azure OpenAI: {e}")
    st.stop()

# ==========================================
# 5. USER INTERFACE
# ==========================================

# Remove the "Deploy" and standard menu items for a cleaner look
# st.markdown("""
#     <style>
#     #MainMenu {visibility: hidden;}
#     footer {visibility: hidden;}
#     header {visibility: hidden;}
#     </style>
#     """, unsafe_allow_html=True)

st.title("💰 Tech Compensation AI")
st.caption("Market Intelligence | Aggregated Insights")

# Sidebar
with st.sidebar:
    st.header("Capabilities")
    st.markdown("""
    - **Search:** Find specific salaries.
    - **Compare:** "Compare Google L5 vs Meta E5"
    - **Visualize:** "Show me a chart of average salaries by company"
    """)

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hello! I can compare compensation packages across companies. Ask me anything about salaries!"}]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ex: 'Compare ms and google average pay'"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Analyzing market data..."):
            try:
                # Pass the prompt to the agent
                response = agent.invoke(prompt)
                output_text = response["output"]
                st.markdown(output_text)
                
                st.session_state.messages.append({"role": "assistant", "content": output_text})
            except Exception as e:
                st.error(f"Error: {str(e)}")
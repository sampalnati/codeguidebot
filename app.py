import streamlit as st
import json
import os
import openai
from analyze_repo import clone_repo, analyze_codebase

# Configure Groq OpenAI-compatible client
client = openai.OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key="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"
)

# Streamlit UI setup
st.set_page_config(page_title="CodeGuide (Groq)", layout="wide")
st.title("🧠 CodeGuide: Understand Any Codebase (Fast via Groq)")

repo_url = st.text_input("Enter a public GitHub repository URL:")

if st.button("Analyze Repository"):
    if repo_url:
        with st.spinner("⏳ Cloning and analyzing the repository..."):
            try:
                repo_path = clone_repo(repo_url)
                tree = analyze_codebase(repo_path, max_functions=25)

                # Save to reuse across sessions
                with open("generated_tree.json", "w") as f:
                    json.dump(tree, f, indent=2)

                st.success("✅ Repository analyzed successfully!")
            except Exception as e:
                st.error(f"❌ Error during analysis: {e}")
    else:
        st.warning("⚠️ Please enter a valid GitHub URL.")

# Load the documentation tree if it exists
if os.path.exists("generated_tree.json"):
    with open("generated_tree.json") as f:
        tree = json.load(f)

    # Flatten tree into text context
    def flatten_tree(node, path=None):
        path = path or []
        entries = []
        full_path = " > ".join(path + [node["name"]])
        entries.append((full_path, node["description"]))
        for child in node.get("children", []):
            entries.extend(flatten_tree(child, path + [node["name"]]))
        return entries

    entries = flatten_tree(tree)

    st.divider()
    st.markdown("### 💬 Ask Questions About the Codebase")

    user_input = st.text_input("Your question:")

    if user_input:
        # Build context string
        context_block = "\n\n".join([f"{path}: {desc}" for path, desc in entries])
        prompt = f"""
You are an assistant helping non-technical users understand a software codebase.

Here is the system overview:

{context_block}

Now answer this question clearly and simply:

User Question: {user_input}
Answer:
        """

        with st.spinner("💡 Thinking..."):
            try:
                response = client.chat.completions.create(
                    model="qwen/qwen3-32b",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.4
                )
                answer = response.choices[0].message.content.strip()
                st.markdown("#### ✅ Answer:")
                st.write(answer)
            except Exception as e:
                st.error(f"❌ Groq API error: {e}")

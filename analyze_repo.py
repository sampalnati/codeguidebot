import os
import git
import ast
import json
import openai

# Create a client for Groq (OpenAI-compatible endpoint)
client = openai.OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key="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"
)

def clone_repo(repo_url, clone_dir="cloned_repo"):
    if os.path.exists(clone_dir):
        os.system(f"rm -rf {clone_dir}")
    git.Repo.clone_from(repo_url, clone_dir)
    return clone_dir

def extract_python_functions(file_path):
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            code = f.read()
        tree = ast.parse(code)
    except Exception:
        return []

    functions = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            try:
                source = ast.get_source_segment(code, node) or ""
            except:
                source = ""
            functions.append({
                "name": node.name,
                "lineno": node.lineno,
                "source": source.strip()
            })
    return functions

def describe_function(name, code_snippet):
    prompt = f"""
You are an assistant helping non-programmers understand code.

Explain this Python function in plain English:
- What it does
- What inputs it takes
- What it returns

Function: {name}
Code:
{code_snippet}
"""

    try:
        response = client.chat.completions.create(
            model="qwen/qwen3-32b",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"[Error generating description: {str(e)}]"

def analyze_codebase(repo_path, max_functions=25):
    doc_tree = {
        "name": "Repository",
        "description": f"Up to {max_functions} Python functions analyzed.",
        "children": []
    }

    ignored_dirs = {"tests", "__pycache__", "venv", "env", ".git", "docs", "examples"}
    count = 0

    for root, dirs, files in os.walk(repo_path):
        if any(ignored in root for ignored in ignored_dirs):
            continue

        for file in files:
            if not file.endswith(".py"):
                continue
            if count >= max_functions:
                break

            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, repo_path)
            funcs = extract_python_functions(full_path)

            for func in funcs:
                if count >= max_functions:
                    break
                description = describe_function(func["name"], func["source"])
                doc_tree["children"].append({
                    "name": f"{rel_path}:{func['name']}",
                    "description": description
                })
                count += 1

    if count == 0:
        doc_tree["description"] = "No Python functions found in the repository."

    return doc_tree

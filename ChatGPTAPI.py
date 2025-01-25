import json
from openai import OpenAI

# Configure sua chave da API
KEY = "##"
client = OpenAI(
    api_key=KEY,
)

class Node:
    def __init__(self, content, children=None):
        self.content = content if isinstance(content, list) else [content]
        self.children = children if children else []
        self.parent = None
        
        for child in self.children:
            child.parent = self

def get_formatted_response(hierarchy_text):
    try:
        messages = [
                {"role": "system", 
                "content": """Você é um assistente que gera quatro 
                perguntas para criar um dataset de textos legais e 
                regulatórios no formato JSON, incluindo contexto, 
                pergunta e resposta."""},
                {"role": "user", "content": f"""
                                    Formato desejado:
                                    {{"instruction": "...", "question": "...", "answer": "..."}}

                                    Texto para processar:
                                    {hierarchy_text}
                """}
        ]
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
        )
        r = response.choices[0].message.content.replace("```json","").replace("```","")
        return r
    except Exception as e:
        print(f"Erro ao acessar a API: {e}")
        return None

def build_tree(data):
    if not isinstance(data, dict):
        return Node(data)
    
    content = data.get('content', [])
    children = []
    
    if 'children' in data:
        children = [build_tree(child) for child in data['children']]
    
    node = Node(content, children)
    for child in node.children:
        child.parent = node
    return node

def get_all_leaf_nodes(root, leaves=None):
    if leaves is None:
        leaves = []
    
    if not root.children:
        leaves.append(root)
    else:
        for child in root.children:
            get_all_leaf_nodes(child, leaves)
    
    return leaves

def get_hierarchy_path(node):
    path = []
    current = node
    
    while current:
        content = ' '.join(str(c) for c in current.content)
        if content:
            path.append(content)
        current = current.parent
        
    return path

def process_regulation_hierarchy(input_file, output_file):
    # Clear the output file before starting
    open(output_file, 'w', encoding='utf-8').close()
    
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    all_leaf_nodes = []
    for root_item in data:
        root = build_tree(root_item)
        leaf_nodes = get_all_leaf_nodes(root)
        all_leaf_nodes.extend(leaf_nodes)
    
    for i, leaf in enumerate(all_leaf_nodes, 1):
        path = get_hierarchy_path(leaf)
        hierarchy_text = "\nConsiderando ".join(reversed(path))
        full_text = "REGULAMENTO INTERNO DE SERVIÇOS GERAIS (RISG)\n" + hierarchy_text
        formatted_response = get_formatted_response(full_text)
        if formatted_response:
            try:
                with open(output_file, 'a', encoding='utf-8') as f:
                    f.write(formatted_response + "\n\n")  # Add two newlines for separation
            except Exception as file_error:
                print(f"Erro ao escrever no arquivo: {file_error}")
        else:
            print(f"Falha ao processar o nó {i}.")
    
        print("Last Node:" + str(i))


if __name__ == "__main__":
    input_file = "regulation_with_hierarchy.json"
    output_file = "dataset_traning2.json"
    
    try:
        process_regulation_hierarchy(input_file, output_file)
        print(f"Responses have been written to {output_file}")
    except FileNotFoundError:
        print(f"Error: Could not find the input file '{input_file}'")
    except json.JSONDecodeError:
        print("Error: Invalid JSON format in the input file")
    except Exception as e:
        print(f"An error occurred: {str(e)}")

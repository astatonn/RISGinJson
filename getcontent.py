import json
from bs4 import BeautifulSoup
import re
import requests

def fetch_regulation(url):
    """Fetch the HTML content from the given URL."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers, verify=False)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching URL: {e}")
        return None

def clean_text(text):
    """Clean and normalize text content."""
    return ' '.join(text.strip().split())

def get_section_content(start_elem):
    """Get all p tags until the next indice-assunto div."""
    content = []
    current = start_elem
    
    while current is not None:
        current = current.find_next_sibling()
        if current is None or (current.name == 'div' and 'indice-assunto' in current.get('class', [])):
            break
            
        if current.name == 'p':
            text = clean_text(current.get_text())
            if text and 'artigo' in current.get('class', []):
                # This is an article paragraph
                content.append({
                    'type': 'article',
                    'content': text
                })
            elif text:
                # This is a regular paragraph
                content.append({
                    'type': 'text',
                    'content': text
                })
    
    return content

def parse_regulation_with_children(html_content):
    """Parse the HTML content into structured JSON with articles grouped as children."""
    soup = BeautifulSoup(html_content, 'html.parser')
    structure = []

    for section_div in soup.find_all('div', class_='indice-assunto'):
        section = {
            'header': [],
            'children': []
        }


        for p in section_div.find_all('p'):
            text = clean_text(p.get_text())
            if text:
                section['header'].append(text)


        content = get_section_content(section_div)
        current_article = None

        article_pattern = re.compile(r'^Art\. \d+.*')

        for item in content:
            if article_pattern.match(item['content']):
                current_article = {
                    'article': item['content'],
                    'content': []
                }
                section['children'].append(current_article)
            elif current_article:
                current_article['content'].append(item)

        structure.append(section)

    return structure


def update_content_types(data):
    roman_pattern = re.compile(
        r"^(?=[IVXLCDM])M{0,1}(CM|CD|D?C{0,3})(XC|XL|L?X{0,3})(IX|IV|V?I{0,3}) -"
    )
    #1940, 1941, 1942
    
    for section in data:
        for child in section.get('children', []):
            for content in child.get('content', []):
                text = content['content']
                if roman_pattern.match(text):
                    content["type"] = "roman"
                elif re.match(r"^§ \d+", text):
                    content["type"] = "paragraph"
                elif text.startswith("Parágrafo único"):
                    content["type"] = "paragraph"
                elif re.match(r"^[a-z]\)", text):
                    content["type"] = "letter"
    return data


def main_with_children(url):
    html_content = fetch_regulation(url)
    if html_content:
        regulation = parse_regulation_with_children(html_content)
        updated_regulation = update_content_types(regulation)

        with open('regulation_with_children.json', 'w', encoding='utf-8') as f:
            json.dump(updated_regulation, f, ensure_ascii=False, indent=2)

        print("Regulation with children has been parsed and saved to regulation_with_children.json")
    else:
        print("Failed to fetch the regulation")


if __name__ == "__main__":
    url = "https://www.sgex.eb.mil.br/sg8/001_estatuto_regulamentos_regimentos/02_regulamentos/port_n_816_cmdo_eb_19dez2003.html"
    main_with_children(url)

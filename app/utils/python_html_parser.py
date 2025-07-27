from bs4 import BeautifulSoup, NavigableString, Tag
import json
import re
from typing import Dict, List, Any, Optional

class HTMLToStructuredContent:
    def __init__(self):
        self.image_counter = 0
        self.link_counter = 0
        
    def parse_html_to_structure(self, html_content: str) -> Dict[str, Any]:
        """
        Convert HTML to a structured format that's LLM-friendly
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        result = {
            'content': [],
            'images': [],
            'links': [],
            'metadata': {
                'total_paragraphs': 0,
                'total_headings': 0,
                'total_images': 0,
                'total_links': 0
            }
        }
        
        # Process the HTML structure
        if soup.body:
            content = self._process_element(soup.body, level=0)
        else:
            content = self._process_element(soup, level=0)
            
        result['content'] = content if isinstance(content, list) else [content]
        
        # Update metadata
        result['metadata'].update({
            'total_images': len(result['images']),
            'total_links': len(result['links']),
        })
        
        return result
    
    def _process_element(self, element, level: int = 0) -> Any:
        """Recursively process HTML elements"""
        if isinstance(element, NavigableString):
            text = str(element).strip()
            if text and not text.isspace():
                return {
                    'type': 'text',
                    'content': text,
                    'level': level
                }
            return None
            
        if isinstance(element, Tag):
            tag_name = element.name.lower()
            
            # Handle images
            if tag_name == 'img':
                return self._process_image(element, level)
            
            # Handle links
            if tag_name == 'a':
                return self._process_link(element, level)
            
            # Handle block elements
            if tag_name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'div', 'section', 'article', 'blockquote']:
                return self._process_block_element(element, level)
            
            # Handle formatting elements
            if tag_name in ['strong', 'b', 'em', 'i', 'span', 'mark', 'u']:
                return self._process_inline_element(element, level)
            
            # Handle lists
            if tag_name in ['ul', 'ol', 'li']:
                return self._process_list_element(element, level)
            
            # Process children for other elements
            return self._process_children(element, level)
        
        return None
    
    def _process_image(self, img_element: Tag, level: int) -> Dict[str, Any]:
        """Extract image information"""
        self.image_counter += 1
        image_id = f"img_{self.image_counter}"
        
        image_data = {
            'id': image_id,
            'type': 'image',
            'src': img_element.get('src', ''),
            'alt': img_element.get('alt', ''),
            'title': img_element.get('title', ''),
            'width': img_element.get('width'),
            'height': img_element.get('height'),
            'class': img_element.get('class'),
            'level': level,
            'original_html': str(img_element)
        }
        
        # Store for metadata
        self.result_images.append(image_data)
        
        return image_data
    
    def _process_link(self, link_element: Tag, level: int) -> Dict[str, Any]:
        """Extract link information"""
        self.link_counter += 1
        link_id = f"link_{self.link_counter}"
        
        # Get link text
        link_text = link_element.get_text().strip()
        
        link_data = {
            'id': link_id,
            'type': 'link',
            'text': link_text,
            'href': link_element.get('href', ''),
            'title': link_element.get('title', ''),
            'target': link_element.get('target', ''),
            'class': link_element.get('class'),
            'level': level,
            'original_html': str(link_element)
        }
        
        # Store for metadata
        self.result_links.append(link_data)
        
        return link_data
    
    def _process_block_element(self, element: Tag, level: int) -> Dict[str, Any]:
        """Process block-level elements"""
        tag_name = element.name.lower()
        
        # Get direct text content and children
        children = self._process_children(element, level + 1)
        
        # If only text content, simplify structure
        if len(children) == 1 and children[0] and children[0].get('type') == 'text':
            return {
                'type': tag_name,
                'content': children[0]['content'],
                'level': level,
                'attributes': self._extract_attributes(element),
                'tag_info': {
                    'original_tag': tag_name,
                    'is_heading': tag_name.startswith('h'),
                    'heading_level': int(tag_name[1]) if tag_name.startswith('h') else None
                }
            }
        
        return {
            'type': tag_name,
            'content': children,
            'level': level,
            'attributes': self._extract_attributes(element),
            'tag_info': {
                'original_tag': tag_name,
                'is_heading': tag_name.startswith('h'),
                'heading_level': int(tag_name[1]) if tag_name.startswith('h') else None
            }
        }
    
    def _process_inline_element(self, element: Tag, level: int) -> Dict[str, Any]:
        """Process inline formatting elements"""
        text_content = element.get_text().strip()
        
        if not text_content:
            return None
            
        return {
            'type': 'text',
            'content': text_content,
            'level': level,
            'formatting': element.name.lower(),
            'attributes': self._extract_attributes(element)
        }
    
    def _process_list_element(self, element: Tag, level: int) -> Dict[str, Any]:
        """Process list elements (ul, ol, li)"""
        tag_name = element.name.lower()
        
        if tag_name in ['ul', 'ol']:
            items = []
            for li in element.find_all('li', recursive=False):
                item_content = self._process_element(li, level + 1)
                if item_content:
                    items.append(item_content)
            
            return {
                'type': 'list',
                'list_type': 'ordered' if tag_name == 'ol' else 'unordered',
                'items': items,
                'level': level,
                'attributes': self._extract_attributes(element)
            }
        
        elif tag_name == 'li':
            children = self._process_children(element, level)
            
            # If single text content
            if len(children) == 1 and children[0] and children[0].get('type') == 'text':
                return {
                    'type': 'list_item',
                    'content': children[0]['content'],
                    'level': level
                }
            
            return {
                'type': 'list_item',
                'content': children,
                'level': level
            }
    
    def _process_children(self, element: Tag, level: int) -> List[Any]:
        """Process all children of an element"""
        children = []
        
        for child in element.children:
            processed = self._process_element(child, level)
            if processed:
                if isinstance(processed, list):
                    children.extend(processed)
                else:
                    children.append(processed)
        
        return [child for child in children if child is not None]
    
    def _extract_attributes(self, element: Tag) -> Optional[Dict[str, str]]:
        """Extract relevant attributes from an element"""
        relevant_attrs = ['id', 'class', 'href', 'target', 'title', 'data-*']
        attrs = {}
        
        for attr_name, attr_value in element.attrs.items():
            if (attr_name in relevant_attrs or 
                attr_name.startswith('data-') or
                attr_name in ['id', 'class']):
                attrs[attr_name] = attr_value if not isinstance(attr_value, list) else ' '.join(attr_value)
        
        return attrs if attrs else None
    
    def structure_to_html(self, structured_content: Dict[str, Any]) -> str:
        """Convert structured content back to HTML"""
        return self._render_content_items(structured_content['content'])
    
    def _render_content_items(self, items: List[Dict[str, Any]]) -> str:
        """Render a list of content items to HTML"""
        html_parts = []
        
        for item in items:
            html_parts.append(self._render_single_item(item))
        
        return '\n'.join(filter(None, html_parts))
    
    def _render_single_item(self, item: Dict[str, Any]) -> str:
        """Render a single content item to HTML"""
        if not item:
            return ''
            
        item_type = item.get('type', '')
        
        if item_type == 'text':
            content = item['content']
            formatting = item.get('formatting')
            
            if formatting:
                attrs = self._render_attributes(item.get('attributes', {}))
                return f'<{formatting}{attrs}>{content}</{formatting}>'
            return content
        
        elif item_type == 'image':
            attrs = []
            if item.get('src'): attrs.append(f'src="{item["src"]}"')
            if item.get('alt'): attrs.append(f'alt="{item["alt"]}"')
            if item.get('title'): attrs.append(f'title="{item["title"]}"')
            if item.get('width'): attrs.append(f'width="{item["width"]}"')
            if item.get('height'): attrs.append(f'height="{item["height"]}"')
            
            return f'<img {" ".join(attrs)} />'
        
        elif item_type == 'link':
            attrs = []
            if item.get('href'): attrs.append(f'href="{item["href"]}"')
            if item.get('title'): attrs.append(f'title="{item["title"]}"')
            if item.get('target'): attrs.append(f'target="{item["target"]}"')
            
            return f'<a {" ".join(attrs)}>{item.get("text", "")}</a>'
        
        elif item_type == 'list':
            list_tag = 'ol' if item.get('list_type') == 'ordered' else 'ul'
            attrs = self._render_attributes(item.get('attributes', {}))
            
            items_html = []
            for list_item in item.get('items', []):
                items_html.append(self._render_single_item(list_item))
            
            items_content = '\n'.join(f'  {item}' for item in items_html)
            return f'<{list_tag}{attrs}>\n{items_content}\n</{list_tag}>'
        
        elif item_type == 'list_item':
            content = item.get('content', '')
            if isinstance(content, list):
                content = self._render_content_items(content)
            return f'<li>{content}</li>'
        
        # Handle block elements
        elif item_type in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'div', 'section', 'article', 'blockquote']:
            attrs = self._render_attributes(item.get('attributes', {}))
            content = item.get('content', '')
            
            if isinstance(content, list):
                content = self._render_content_items(content)
            
            return f'<{item_type}{attrs}>{content}</{item_type}>'
        
        return ''
    
    def _render_attributes(self, attributes: Dict[str, str]) -> str:
        """Render attributes dictionary to HTML attribute string"""
        if not attributes:
            return ''
        
        attr_parts = []
        for key, value in attributes.items():
            attr_parts.append(f'{key}="{value}"')
        
        return ' ' + ' '.join(attr_parts) if attr_parts else ''

# Usage example for FastAPI
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class TranslationRequest(BaseModel):
    html_content: str
    target_language: str = "spanish"

class TranslationResponse(BaseModel):
    original_structure: dict
    translated_structure: dict
    translated_html: str

@app.post("/api/translate-article", response_model=TranslationResponse)
async def translate_article(request: TranslationRequest):
    try:
        # Initialize parser
        parser = HTMLToStructuredContent()
        
        # Parse HTML to structure
        structured_content = parser.parse_html_to_structure(request.html_content)
        
        # Create LLM-friendly prompt
        translation_prompt = create_translation_prompt(structured_content, request.target_language)
        
        # Call your LLM service (replace with your actual LLM call)
        translated_structure = await call_llm_for_translation(translation_prompt)
        
        # Convert back to HTML
        translated_html = parser.structure_to_html(translated_structure)
        
        return TranslationResponse(
            original_structure=structured_content,
            translated_structure=translated_structure,
            translated_html=translated_html
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Translation failed: {str(e)}")

def create_translation_prompt(structured_content: dict, target_language: str) -> str:
    """Create a comprehensive prompt for the LLM"""
    
    # Extract context information
    total_images = len(structured_content.get('images', []))
    total_links = len(structured_content.get('links', []))
    
    # Create a readable summary for the LLM
    content_summary = analyze_content_structure(structured_content['content'])
    
    prompt = f"""
You are a professional translator. Please translate this structured article content to {target_language}.

ARTICLE STRUCTURE ANALYSIS:
- Total paragraphs: {content_summary['paragraphs']}
- Total headings: {content_summary['headings']} 
- Total images: {total_images}
- Total links: {total_links}
- Content hierarchy levels: {content_summary['max_level']}

TRANSLATION RULES:
1. Translate ONLY the text content in the 'content' fields
2. NEVER translate: type, level, attributes, formatting, src, href, or any technical fields
3. DO translate: text content, alt text for images, link text, heading content
4. Maintain the exact same JSON structure
5. Preserve all formatting and hierarchy information
6. Keep all technical metadata unchanged

STRUCTURED CONTENT TO TRANSLATE:
{json.dumps(structured_content, indent=2, ensure_ascii=False)}

Please return the translated content in the exact same JSON structure with only the translatable text content changed to {target_language}.
"""
    
    return prompt

def analyze_content_structure(content_items: list) -> dict:
    """Analyze the content structure for better LLM context"""
    analysis = {
        'paragraphs': 0,
        'headings': 0,
        'max_level': 0,
        'content_types': set()
    }
    
    def analyze_item(item):
        if not isinstance(item, dict):
            return
            
        item_type = item.get('type', '')
        level = item.get('level', 0)
        
        analysis['content_types'].add(item_type)
        analysis['max_level'] = max(analysis['max_level'], level)
        
        if item_type == 'p':
            analysis['paragraphs'] += 1
        elif item_type in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            analysis['headings'] += 1
        
        # Recursively analyze nested content
        content = item.get('content', [])
        if isinstance(content, list):
            for nested_item in content:
                analyze_item(nested_item)
    
    for item in content_items:
        analyze_item(item)
    
    analysis['content_types'] = list(analysis['content_types'])
    return analysis

async def call_llm_for_translation(prompt: str):
    """
    Replace this with your actual LLM service call
    This is just a placeholder
    """
    # Example with OpenAI
    # import openai
    # response = await openai.ChatCompletion.acreate(
    #     model="gpt-4",
    #     messages=[{"role": "user", "content": prompt}]
    # )
    # return json.loads(response.choices[0].message.content)
    
    # Placeholder return
    return {"translated": "content"}

if __name__ == "__main__":
    # Test the parser
    parser = HTMLToStructuredContent()
    
    sample_html = """
    <article>
        <h1>Sample Article</h1>
        <p>This is a paragraph with <strong>bold text</strong> and a <a href="https://example.com">link</a>.</p>
        <img src="image.jpg" alt="Sample image" title="A sample image" />
        <h2>Second Section</h2>
        <ul>
            <li>First item</li>
            <li>Second item</li>
        </ul>
    </article>
    """
    
    result = parser.parse_html_to_structure(sample_html)
    print(json.dumps(result, indent=2, ensure_ascii=False))
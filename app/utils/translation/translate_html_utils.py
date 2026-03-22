"""
Ollama service for handling communication with Ollama container
Manages all interactions with the Ollama translation service with HTML preservation
"""
import httpx
import re
from typing import List, Tuple, Match, Dict, Any
from bs4 import BeautifulSoup, NavigableString, Tag
from config import OLLAMA_BASE_URL, OLLAMA_DEFAULT_MODEL, OLLAMA_BACKUP_MODEL
##//TODO remove app before deploying 
# from app.config import OLLAMA_BASE_URL, OLLAMA_DEFAULT_MODEL

class TranslateHTMLUtils:
    """Service class for translating HTML content while preserving structure using Ollama LLM"""

    def __init__(self):
        self.base_url = OLLAMA_BASE_URL
        self.timeout = 60.0
        self.model = OLLAMA_DEFAULT_MODEL or OLLAMA_BACKUP_MODEL  # Fallback if env var is not set
    
    async def check_health(self) -> bool:
        """
        Check if Ollama service is accessible
        
        Returns:
            True if Ollama is responding, False otherwise
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                return response.status_code == 200
        except Exception:
            return False

    def extract_text_with_structure(self, html_content: str) -> Tuple[List[str], Dict[str, Any]]:
        """
        Extract all translatable text from HTML while preserving complete structure for reconstruction
        
        Args:
            html_content: HTML string with content to translate
            
        Returns:
            Tuple of (list of text segments, structure_map for reconstruction)
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')  # type: ignore
            text_segments: List[str] = []
            structure_map: Dict[str, Any] = {
                'type': 'root',
                'content': [],
                'original_html': html_content
            }  # type: ignore
            
            def process_element(element: Any, parent_structure: Dict[str, Any]) -> None:
                if isinstance(element, NavigableString):
                    text = str(element).strip()
                    if text and not text.isspace():
                        # Store text with placeholder index
                        placeholder_index = len(text_segments)
                        text_segments.append(text)
                        parent_structure['content'].append({
                            'type': 'text',
                            'placeholder_index': placeholder_index,
                            'original_text': text
                        })
                elif isinstance(element, Tag):
                    tag_data: Dict[str, Any] = {
                        'type': 'tag',
                        'tag_name': element.name,
                        'attributes': dict(element.attrs) if element.attrs else {},
                        'content': []
                    }  # type: ignore
                    
                    # Handle special attributes that might contain translatable text
                    if element.name == 'img' and element.get('alt'):
                        alt_text_attr = element.get('alt')
                        if isinstance(alt_text_attr, str):
                            alt_text = alt_text_attr.strip()
                            if alt_text:
                                placeholder_index = len(text_segments)
                                text_segments.append(alt_text)
                                tag_data['alt_placeholder_index'] = placeholder_index
                                tag_data['original_alt'] = alt_text
                    
                    title_attr = element.get('title')
                    if title_attr:
                        if isinstance(title_attr, str):
                            title_text = title_attr.strip()
                            if title_text:
                                placeholder_index = len(text_segments)
                                text_segments.append(title_text)
                                tag_data['title_placeholder_index'] = placeholder_index
                                tag_data['original_title'] = title_text
                    
                    # Process children
                    for child in element.children:
                        process_element(child, tag_data)  # type: ignore
                    
                    parent_structure['content'].append(tag_data)  # type: ignore
            
            # Process the entire document
            if soup.body:
                for child in soup.body.children:
                    process_element(child, structure_map)  # type: ignore
            else:
                for child in list(getattr(soup, "contents", [])):
                    process_element(child, structure_map)  # type: ignore
            
            print(f"DEBUG: Extracted {len(text_segments)} text segments from HTML")
            print(f"DEBUG: Text segments: {text_segments}")
            return text_segments, structure_map
            
        except Exception as e:
            print(f"DEBUG: Error in extract_text_with_structure: {e}")
            # Fallback to old method - convert result to expected format
            text_segments, template = self.extract_text_from_html(html_content)
            fallback_structure_map: Dict[str, Any] = {
                'type': 'fallback',
                'template': template,
                'original_html': html_content
            }
            return text_segments, fallback_structure_map

    def reconstruct_html_from_structure(self, translated_segments: List[str], structure_map: Dict[str, Any]) -> str:
        """
        Reconstruct HTML from structure map with translated text
        
        Args:
            translated_segments: List of translated text segments
            structure_map: Structure map created during extraction
            
        Returns:
            HTML with translated content and preserved structure
        """
        try:
            # Handle fallback case
            if structure_map.get('type') == 'fallback':
                template = structure_map.get('template', '')
                if isinstance(template, str):
                    return self.reconstruct_html(translated_segments, template)
            
            def render_content(content_list: List[Dict[str, Any]]) -> str:
                html_parts: List[str] = []
                for item in content_list:
                    if item['type'] == 'text':
                        # Replace with translated text
                        index = item['placeholder_index']
                        if isinstance(index, int) and index < len(translated_segments):
                            html_parts.append(translated_segments[index])
                        else:
                            html_parts.append(str(item.get('original_text', '')))  # Fallback
                    elif item['type'] == 'tag':
                        # Reconstruct tag
                        tag_name = str(item.get('tag_name', ''))
                        attributes = dict(item.get('attributes', {}))
                        
                        # Handle translated attributes
                        if 'alt_placeholder_index' in item:
                            index = item['alt_placeholder_index']
                            if isinstance(index, int) and index < len(translated_segments):
                                attributes['alt'] = translated_segments[index]
                        
                        if 'title_placeholder_index' in item:
                            index = item['title_placeholder_index']
                            if isinstance(index, int) and index < len(translated_segments):
                                attributes['title'] = translated_segments[index]
                        
                        # Build attribute string
                        attr_str = ''
                        if attributes:
                            attr_parts: List[str] = []
                            for key, attr_value in attributes.items():
                                # Convert attribute value to string regardless of type
                                if isinstance(attr_value, list):
                                    # Handle attribute values that are lists
                                    value_str = ' '.join(str(item) for item in attr_value)  # type: ignore
                                elif attr_value is not None:
                                    value_str = str(attr_value)
                                else:
                                    value_str = ''
                                attr_parts.append(f'{key}="{value_str}"')  # type: ignore
                            attr_str = ' ' + ' '.join(attr_parts)
                        
                        # Self-closing tags
                        if tag_name in ['img', 'br', 'hr', 'input', 'meta', 'link']:
                            html_parts.append(f'<{tag_name}{attr_str} />')
                        else:
                            # Regular tags with content
                            inner_content = render_content(item.get('content', []))
                            html_parts.append(f'<{tag_name}{attr_str}>{inner_content}</{tag_name}>')
                
                return ''.join(html_parts)
            
            result = render_content(structure_map.get('content', []))
            print(f"DEBUG: Reconstructed HTML: {result}")
            return result
            
        except Exception as e:
            print(f"DEBUG: Error in reconstruct_html_from_structure: {e}")
            # Fallback to old method
            return self.reconstruct_html(translated_segments, "")

    # OLD METHODS - COMMENTED BUT PRESERVED FOR FALLBACK AND FUTURE REFERENCE
    def extract_text_from_html(self, html_content: str) -> Tuple[List[str], str]:
        """
        OLD METHOD: Extract translatable text from HTML while preserving structure
        This method uses regex-based extraction with placeholder templates
        
        Args:
            html_content: HTML string with content to translate
            
        Returns:
            Tuple of (list of text segments, template with placeholders)
        """
        # Find all text content between HTML tags (but not within tag attributes)
        # This regex captures text that's not inside < >
        text_pattern = r'>([^<]+)<'
        
        # Find all text segments
        text_segments: List[str] = []
        placeholder_template = html_content
        
        # Replace text content with numbered placeholders
        def replace_text(match: Match[str]) -> str:
            text = match.group(1).strip()
            if text:  # Only process non-empty text
                placeholder = f"{{TEXT_{len(text_segments)}__}}"
                text_segments.append(text)
                return f">{placeholder}<"
            return match.group(0)
        
        placeholder_template = re.sub(text_pattern, replace_text, placeholder_template)
        
        # Also handle text at the beginning and end that might not be wrapped in tags
        # Handle text before first tag
        if not placeholder_template.startswith('<'):
            first_tag_match = re.search(r'<', placeholder_template)
            if first_tag_match:
                start_text = placeholder_template[:first_tag_match.start()].strip()
                if start_text:
                    placeholder = f"{{TEXT_{len(text_segments)}__}}"
                    text_segments.append(start_text)
                    placeholder_template = placeholder + placeholder_template[first_tag_match.start():]
        
        # Handle text after last tag
        if not placeholder_template.endswith('>'):
            last_tag_match = None
            for match in re.finditer(r'>', placeholder_template):
                last_tag_match = match
            if last_tag_match:
                end_text = placeholder_template[last_tag_match.end():].strip()
                if end_text:
                    placeholder = f"{{TEXT_{len(text_segments)}__}}"
                    text_segments.append(end_text)
                    placeholder_template = placeholder_template[:last_tag_match.end()] + placeholder
        
        print(f"DEBUG: OLD METHOD - Extracted text segments: {text_segments}")
        print(f"DEBUG: OLD METHOD - Placeholder template: {placeholder_template}")
        return text_segments, placeholder_template

    def reconstruct_html(self, translated_segments: List[str], template: str) -> str:
        """
        OLD METHOD: Reconstruct HTML by replacing placeholders with translated text
        This method uses simple string replacement with numbered placeholders
        
        Args:
            translated_segments: List of translated text segments
            template: HTML template with placeholders
            
        Returns:
            HTML with translated content
        """
        result = template
        for i, translated_text in enumerate(translated_segments):
            placeholder = f"{{TEXT_{i}__}}"
            result = result.replace(placeholder, translated_text)
        
        print(f"DEBUG: OLD METHOD - Reconstructed HTML: {result}")
        return result
    def split_html_into_chunks(self, html: str, max_chars: int = 2000) :
        """
        Split HTML content into smaller chunks for translation.
        
        Strategy:
        1. Primary split by <hr> (semantic boundary).
        2. If any chunk exceeds `max_chars`, further split by <div> tags.
        3. If still too large, fall back to character-based splitting at tag boundaries.

        Args:
            html: Full HTML content to split
            max_chars: Maximum characters per chunk

        Returns:
            List of HTML chunks ready for translation
        """
        final_chunks: list[str] = []

    # Step 1: split by <hr>
        parts = html.split("<hr")
        for i, part in enumerate(parts):
            if i > 0:
            # Reattach <hr> to keep original structure
                part = "<hr" + part
            part = part.strip()
            if not part:
                continue

        # Step 2: enforce max length
            if len(part) <= max_chars:
                final_chunks.append(part)
            else:
            # Try splitting further by </div>
                buffer = ""
                for sub in part.split("</div>"):
                    if not sub.strip():
                        continue
                    candidate = buffer + sub + "</div>"
                    if len(candidate) > max_chars:
                        if buffer:
                            final_chunks.append(buffer)
                        buffer = sub + "</div>"
                    else:
                        buffer = candidate
                if buffer:
                    final_chunks.append(buffer)

    # Step 3: safeguard for any chunks still too large
        safe_final: list[str] = []
        for chunk in final_chunks:
            if len(chunk) > max_chars:
                start = 0
                while start < len(chunk):
                    slice_ = chunk[start:start + max_chars]

                # try not to break inside a tag
                    if slice_.count("<") > slice_.count(">"):
                        cut = slice_.rfind(">")
                        if cut != -1:
                            safe_final.append(slice_[:cut+1])
                        start += cut + 1
                        continue

                    safe_final.append(slice_)
                    start += max_chars
            else:
                safe_final.append(chunk)

        return [c.strip() for c in safe_final if c.strip()]


    def _parse_numbered_translation(self, translation_response: str, expected_count: int) -> List[str]:
        """
        Parse numbered translation response back to list of segments
        """
        segments: List[str] = []
        lines = translation_response.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            # Match patterns like "1. text" or "1) text" or "1- text"
            match = re.match(r'^\d+[\.\)\-]\s*(.+)', line)
            if match:
                segments.append(match.group(1).strip())
            elif line and not re.match(r'^\d+[\.\)\-]', line):
                # If line doesn't start with number but has content, might be continuation
                if segments:  # Add to last segment if exists
                    segments[-1] += " " + line
        
        # Ensure we have expected number of segments
        while len(segments) < expected_count:
            segments.append("")  # Add empty segments if missing
        
        return segments[:expected_count]  # Trim if too many

# Global service instance
translateHTML_utils = TranslateHTMLUtils()

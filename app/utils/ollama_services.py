"""
Ollama service for handling communication with Ollama container
Manages all interactions with the Ollama translation service with HTML preservation
"""
import httpx
import re
from typing import List, Tuple, Match, Optional, Dict, Any
from bs4 import BeautifulSoup, NavigableString, Tag
# from config import OLLAMA_BASE_URL, OLLAMA_DEFAULT_MODEL
##//TODO remove app before deploying 
from app.config import OLLAMA_BASE_URL, OLLAMA_DEFAULT_MODEL

class OllamaService:
    """Service class for interacting with Ollama"""

    def __init__(self):
        self.base_url = OLLAMA_BASE_URL
        self.timeout = 60.0
    
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
                for child in soup.children:
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
         # Parse HTML
        # soup = BeautifulSoup(html, 'html.parser')
        # chunks: List[str] = []
        # current_chunk = []
        # current_length = 0
        
        # def process_node(node: Any):
        #     nonlocal current_chunk, current_length
            
        #     if isinstance(node, NavigableString):
        #         text = str(node).strip()
        #         if text:
        #             # If adding this text would exceed chunk size, create new chunk
        #             if current_length + len(text) > max_chars and current_chunk:
        #                 chunks.append(''.join(current_chunk)) # type: ignore
        #                 current_chunk = []
        #                 current_length = 0
                    
        #             current_chunk.append(text) # type: ignore
        #             current_length += len(text)
            
        #     elif isinstance(node, Tag):
        #         # Start tag
        #         tag_start = f"<{node.name}{' ' + str(node.attrs) if node.attrs else ''}>"
        #         current_chunk.append(tag_start) # type: ignore
                
        #         # Process children
        #         for child in node.children:
        #             process_node(child)
                
        #         # End tag
        #         current_chunk.append(f"</{node.name}>") # type: ignore
        
        # # Process the HTML tree
        # for node in (soup.body.children if soup.body else soup.children):
        #     process_node(node)
        
        # # Don't forget the last chunk       if current_chunk:
        #     chunks.append(''.join(current_chunk)) # type: ignore
        
        # print(f"DEBUG: Split HTML into {len(chunks)} chunks")
        # return chunks
        # chunks: list[str] = []

        # # Step 1: split by <hr>
        # parts = html.split("<hr")
        # for i, part in enumerate(parts):
        #     if i > 0:
        #         # Reattach the <hr> tag at the start of each part (except the first)
        #         part = "<hr" + part
        #     part = part.strip()
        #     if not part:
        #         continue

        #     # Step 2: enforce max length
        #     if len(part) <= max_chars:
        #         chunks.append(part)
        #     else:
        #         # Try splitting further by <div>
        #         subparts = part.split("</div>")
        #         buffer = ""
        #         for sp in subparts:
        #             candidate = buffer + sp + "</div>"
        #             if len(candidate) > max_chars:
        #                 if buffer:
        #                     chunks.append(buffer)
        #                 buffer = sp + "</div>"
        #             else:
        #                 buffer = candidate
        #         if buffer:
        #             chunks.append(buffer)

        #         # Step 3: fallback to character slicing if still too big
        #         safe_chunks: list[str] = []
        #         for c in chunks:
        #             if len(c) > max_chars:
        #                 for j in range(0, len(c), max_chars):
        #                     slice_ = c[j:j+max_chars]
        #                     # try not to break in the middle of a tag
        #                     if slice_.count("<") > slice_.count(">"):
        #                         # cut back to last closing tag
        #                         cut = slice_.rfind(">")
        #                         if cut != -1:
        #                             safe_chunks.append(slice_[:cut+1])
        #                             buffer_rest = slice_[cut+1:]
        #                             if buffer_rest:
        #                                 safe_chunks.append(buffer_rest)
        #                     else:
        #                         safe_chunks.append(slice_)
        #             else:
        #                 safe_chunks.append(c)
        #         chunks = safe_chunks

        # return [c.strip() for c in chunks if c.strip()]

    async def translate_html_content(self, content: str, target_language: str, model: Optional[str] = None) -> str:
        """
        Translate HTML content while preserving structure and tags
        Uses improved text extraction that sends only plain text to Ollama
        
        Args:
            content: HTML content to translate
            target_language: Target language for translation
            model: Ollama model to use for translation (defaults to OLLAMA_DEFAULT_MODEL)
            
        Returns:
            Translated HTML content with preserved structure
        """
        # Ensure we have a valid model
        if model is not None:
            model_to_use: str = model
        else:
            model_to_use = OLLAMA_DEFAULT_MODEL or "llama3.2"  # Fallback if env var is not set
        # Try new structured approach first
        if not content or len(content.strip()) < 5:
            return content
    
        try:
            print(f"DEBUG: Starting HTML translation at translate html contentwith improved structure preservation")
            prompt = ""
            # Extract text segments and structure
            # text_segments, structure_map = self.extract_text_with_structure(content)
            
            # if not text_segments:
            #     print(f"DEBUG: No text segments found, returning original content")
            #     return content  # No text to translate
            # # Create clean text for translation (only the extractable text)
            # clean_text_for_translation = "\n".join([f"{i+1}. {text}" for i, text in enumerate(text_segments)])
            # print("==="*40)
            # # print(f"DEBUG: Clean text for translation:\n{clean_text_for_translation}")
            # print(f"DEBUG: Clean text for translation:\n{clean_text_for_translation}")
            # print("==="*40)
            chunks = self.split_html_into_chunks(content, max_chars=5000)
            translated_chunks: List[str] = []
            for i, chunk in enumerate(chunks):
                try:
                # Extract text and structure from chunk
                    text_segments = self.extract_text_with_structure(chunk)
                
                    if not text_segments:
                        translated_chunks.append(chunk)
                        continue

            # Create prompt for translation with numbered segments
                    prompt = f"""You are an AI specialized in translating to {target_language}, accordingly translate the below text by following the next list of rules:
                    Rules:
                    - Do not add explanations or extra text, no alternatives or explanations
                    - Maintain the exact same structure
                    - Use neutral, formal, and clear {target_language} style
                    - In case the text is a list, translate ONLY the text content after each number, once done keep the same numbering if any (1., 2., 3., etc.)
                    - Preserve the HTML structure and tags exactly as they are.
                    - Translate literally the visible text between the tags.
                    - Use style suitable for an educational or explanatory talk. Avoid slang or regional idioms.
                    - Return only the translated. Do not wrap it in extra mark  down, do not explain, do not say "Here is your translation".
                    - Do not return any context array numbers.
                    The text to translate is:
                    {chunk}"""

                    print(f"DEBUG: Generated prompt for structured translation")
                
                # Get translation
                    translated_response = await self.generate_translation(prompt, model_to_use)
                    print("==="*40)
                    print(f"DEBUG: Raw translation response: {translated_response}")
                    print("==="*40)
            # Parse numbered response back to list
            # translated_segments = self._parse_numbered_translation(translated_response, len(text_segments))
                # Validate translation
                    if not translated_response or len(translated_response.strip()) < 5:
                        print(f"WARNING: Empty or invalid translation for chunk {i+1}")
                        translated_chunks.append(chunk)  # Keep original if translation failed
                        continue
                    
                    translated_chunks.append(translated_response.strip())
                    
                except Exception as chunk_error:
                    print(f"ERROR: Failed to translate chunk {i+1}: {str(chunk_error)}")
                    translated_chunks.append(chunk)  # Keep original on error
                    continue
            # if len(translated_segments) != len(text_segments):
            #     # print(f"DEBUG: Segment count mismatch. Expected {len(text_segments)}, got {len(translated_segments)}. Falling back to individual translation.")
            #     # Fallback: translate each segment individually
            #     translated_segments_fallback: List[str] = []
            #     for segment in text_segments:
            #         individual_prompt = f"Translate this text to {target_language} (return only the translation): {segment}"
            #         translated_segment = await self.generate_translation(individual_prompt, model_to_use)
            #         translated_segments_fallback.append(translated_segment.strip())
            #     translated_segments = translated_segments_fallback
            
            # # Reconstruct HTML with translated text using structure
            # result = self.reconstruct_html_from_structure(translated_segments, structure_map)
                # translated_chunks.append(translated_response)
            result = "\n".join(translated_chunks)
            print("==="*40)
            print(f"DEBUG: Final translated HTML result: {result}")
            print("==="*40)
            return result
            
        except Exception as e:
            print(f"DEBUG: Error in new structured translation: {e}. Falling back to old method.")
            # Fallback to old method if new approach fails
            return await self._translate_html_content_old_method(content, target_language, model_to_use)

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

    # OLD METHOD - PRESERVED FOR FALLBACK
    async def _translate_html_content_old_method(self, content: str, target_language: str, model: str) -> str:
        """
        OLD METHOD: Translate HTML content while preserving structure and tags
        This method uses the original segment-based approach with ---SEGMENT--- separators
        """
        # Extract text segments and create template
        text_segments, placeholder_template = self.extract_text_from_html(content)
        
        if not text_segments:
            return content  # No text to translate
        
        # Create prompt for batch translation
        text_to_translate = "---SEGMENT---".join(text_segments)
        print(f"DEBUG: OLD METHOD - text for translation: {text_to_translate}")
        
        # OLD PROMPT - PRESERVED FOR REFERENCE
        prompt = f"""Translate the following text segments to {target_language}. 
Translate the following HTML content into Spanish.

- Use only one translation, no alternatives or explanations.
- Preserve the HTML structure and tags exactly as they are.
- Translate literally the visible text between the tags.
- Use a neutral, formal, and clear Spanish style — suitable for an educational or explanatory talk. Avoid slang or regional idioms.
- Return only the translated HTML. Do not wrap it in extra markdown, do not explain, do not say "Here is your translation".
{text_to_translate}"""
        
        # COMMENTED OLD PROMPT IDEAS - PRESERVED FOR FUTURE REFERENCE
        # print(f"DEBUG: Generated prompt for translation: {prompt}")
        # TODO possible new prompt
        # Instructions:
        # - Translate only the text content, not HTML tags or image information
        # - Maintain the exact structure and hierarchy
        # - Preserve all formatting indicators and attributes
        # - For images, translate only the 'alt' and 'title' text if present
        # - Return the result in the exact same JSON structure
        # Get translation
        translated_combined = await self.generate_translation(prompt, model)
        
        # OLD DEBUG - PRESERVED FOR REFERENCE
        # print(f"DEBUG: Raw translation response: {translated_combined}")
        
        # Split back into segments
        translated_segments = translated_combined.split("---SEGMENT---")
        translated_segments = [seg.strip() for seg in translated_segments]
        
        # Ensure we have the same number of segments
        if len(translated_segments) != len(text_segments):
            # Fallback: translate each segment individually
            translated_segments: List[str] = []
            for segment in text_segments:
                individual_prompt = f"Translate this text to {target_language}: {segment}"
                translated_segment = await self.generate_translation(individual_prompt, model)
                translated_segments.append(translated_segment.strip())
        
        # Reconstruct HTML with translated text
        print(f"DEBUG: OLD METHOD - HTML with translated content: {self.reconstruct_html(translated_segments, placeholder_template)}")
        return self.reconstruct_html(translated_segments, placeholder_template)

    async def generate_translation(self, prompt: str, model: str) -> str:
        """
        Generate translation using Ollama
        
        Args:
            prompt: Translation prompt
            model: Ollama model to use
            
        Returns:
            Generated translation text
            
        Raises:
            Exception: If translation fails
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                payload: object = {}
                # print(f"DEBUG: PROMPT: {prompt}")
                payload = {
                    "model": OLLAMA_DEFAULT_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "temperature": 0.3  # Lower temperature for consistent translations
                }
                
                response = await client.post(
                    f"{self.base_url}/api/generate",
                    json=payload
                ) 
                # //TODO change app before deploying
                # response = await client.post("http://localhost:11434/api/generate", json=payload)

                # print(f"DEBUG: Response status code: {response}")
                response.raise_for_status()
                # print(f"DEBUG: Response status code: {response.status_code}")
                # print(f"DEBUG: Response headers: {response.headers}")
                # print(f"DEBUG: Response content: {response.content}...")
                data = response.json()
                return data.get("response", "").strip()
                
        except httpx.HTTPStatusError as e:
            raise Exception(f"Ollama API error: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            raise Exception(f"Translation service error: {str(e)}")

    async def resume_article(self, title: str, body: str, model: str, language: str) -> str:
        """
        Generate a resume for the given article text.
        """
        resume = ""
        try:
            if language == "en":
                    print(f"DEBUG: Original article text: {title}")
                    prompt = f"""You are an AI specialized in creating engaging article descriptions. Given the below blog title and slice of article body, generate a description that provides a clear idea of its content while encouraging readers to explore further. Rules: 
                    Always write in the same language as the original article. 
                    Style: neutral, professional, and clear. Avoid slang, exaggeration, or personal commentary.
                    Purpose: create a teaser that sparks curiosity without fully revealing the article.
                    Output only the description text (no titles, labels, or explanations). 
                    Length: A single paragraph of 30 to 40 words.
                {"Title: " + title if title else "", " Article: " + body if body else ""}"""
                    resume = await self.generate_translation(prompt, model)
                    print(f"DEBUG: Generated resume english: {resume}")
            else:
                   print(f"DEBUG: Original article text (ES): {title}")
                   prompt = f"""Eres una IA especializada en crear descripciones atractivas de artículos. En función del título y el fragmento del cuerpo del artículo de blog al final de las instrucciones, genera una descripción que proporcione una idea clara de su contenido mientras anima a los lectores a explorar más. Reglas:
                   Siempre escribe en el mismo idioma que el artículo original.
                   Estilo: neutral, profesional y claro. Evita la jerga, la exageración o los comentarios personales.
                   Propósito: crear una pequeña introducción que despierte la curiosidad sin revelar completamente el artículo.
                   Salida: solo el texto de la descripción (sin títulos, etiquetas ni explicaciones).
                   Longitud: un solo párrafo de 30 a 40 palabras.
               {"Titulo: " + title if title else "", " Artículo: " + body if body else ""}"""
                   resume = await self.generate_translation(prompt, model)
                   print(f"DEBUG: Generated resume spanish: {resume}")
        except httpx.HTTPStatusError as e:
            raise Exception(f"Ollama API error: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            # Optionally log the error here
            print(f"DEBUG: Error occurred while generating resume: {str(e)}")
        return resume

# Global service instance
ollama_service = OllamaService()

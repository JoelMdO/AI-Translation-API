#!/usr/bin/env python3
"""
Test script for improved HTML translation functionality
Tests the new structure-preserving translation approach
"""
import asyncio
import sys
import os

# Add the app directory to the path
sys.path.append('/Users/joelmontesdeoca/Documents/Bafik/OllamaAPI/app')

# Set environment variables for testing
os.environ['DEV_MODE'] = 'true'
os.environ['OLLAMA_BASE_URL'] = 'http://localhost:11434'
os.environ['OLLAMA_DEFAULT_MODEL'] = 'llama3.2'

async def test_html_translation():
    """Test the improved HTML translation functionality"""
    
    try:
        # Import after setting environment
        from utils.generate_translation import ollama_service
        
        # Test HTML content
        test_html = """
        <div class="article">
            <h1>Welcome to our website</h1>
            <p>This is a <strong>sample paragraph</strong> with some text.</p>
            <img src="image.jpg" alt="A beautiful landscape" title="Mountain view" />
            <p>Another paragraph with a <a href="https://example.com" title="Visit our homepage">link to our site</a>.</p>
            <ul>
                <li>First item in the list</li>
                <li>Second item with <em>emphasis</em></li>
            </ul>
        </div>
        """
        
        print("=== TESTING IMPROVED HTML TRANSLATION ===")
        print(f"Original HTML:\n{test_html}\n")
        
        # Test the new translation method
        print("Starting translation...")
        
        result = await ollama_service.translate_html_content(
            content=test_html,
            target_language="Spanish",
            model="llama3.2"
        )
        
        print(f"\nTranslated HTML:\n{result}\n")
        print("=== TEST COMPLETED ===")
        
        return result
        
    except Exception as e:
        print(f"ERROR during test: {e}")
        import traceback
        traceback.print_exc()
        return None

async def test_text_extraction():
    """Test just the text extraction part"""
    
    try:
        from utils.generate_translation import ollama_service
        
        test_html = """
        <div>
            <h1>Hello World</h1>
            <p>This is a test <strong>paragraph</strong>.</p>
            <img src="test.jpg" alt="Test image" />
        </div>
        """
        
        print("=== TESTING TEXT EXTRACTION ===")
        print(f"Original HTML:\n{test_html}\n")
        
        # Test text extraction
        try:
            text_segments, structure_map = ollama_service.extract_text_with_structure(test_html)
            print(f"Extracted text segments: {text_segments}")
            print(f"Structure map keys: {list(structure_map.keys())}")
            
            # Test reconstruction with same text (no translation)
            reconstructed = ollama_service.reconstruct_html_from_structure(text_segments, structure_map)
            print(f"\nReconstructed HTML:\n{reconstructed}")
            
        except Exception as e:
            print(f"New method failed: {e}")
            print("Falling back to old method...")
            
            # Test old method
            text_segments, template = ollama_service.extract_text_from_html(test_html)
            print(f"Old method - Text segments: {text_segments}")
            print(f"Old method - Template: {template}")
            
            reconstructed = ollama_service.reconstruct_html(text_segments, template)
            print(f"Old method - Reconstructed: {reconstructed}")
        
        print("=== EXTRACTION TEST COMPLETED ===")
        
    except Exception as e:
        print(f"ERROR during extraction test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Starting HTML translation tests...")
    
    # Test extraction first
    asyncio.run(test_text_extraction())
    
    print("\n" + "="*50 + "\n")
    
    # Test full translation
    asyncio.run(test_html_translation())

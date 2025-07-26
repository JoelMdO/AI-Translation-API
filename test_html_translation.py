#!/usr/bin/env python3
"""
Quick test script to verify HTML translation functionality works correctly
"""
import asyncio
import sys
import os

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from utils.generate_translation import OllamaService

async def test_html_extraction():
    """Test HTML text extraction and reconstruction"""
    
    # Test HTML content from user
    html_content = '<div>Vamos por un test</div><br><div>Todos juntos</div><img src="url.jpg"><span>bold text</span><div>bye</div>'
    
    print("🧪 Testing HTML text extraction...")
    print(f"Original HTML: {html_content}")
    
    service = OllamaService()
    
    # Extract text segments and template
    text_segments, template = service.extract_text_from_html(html_content)
    
    print(f"\n📝 Extracted text segments: {text_segments}")
    print(f"📄 Template with placeholders: {template}")
    
    # Simulate translated segments (manual translation for testing)
    translated_segments = [
        "Let's go for a test",  # "Vamos por un test"
        "All together",         # "Todos juntos"  
        "bold text",           # "bold text" (already in English)
        "bye"                  # "bye" (already in English)
    ]
    
    print(f"\n🔄 Simulated translated segments: {translated_segments}")
    
    # Reconstruct HTML
    result = service.reconstruct_html(translated_segments, template)
    
    print(f"\n✅ Reconstructed HTML: {result}")
    
    # Verify structure is preserved
    print(f"\n🔍 Structure verification:")
    print(f"   Original has <div> tags: {'<div>' in html_content}")
    print(f"   Result has <div> tags: {'<div>' in result}")
    print(f"   Original has <br> tag: {'<br>' in html_content}")
    print(f"   Result has <br> tag: {'<br>' in result}")
    print(f"   Original has <img> tag: {'<img' in html_content}")
    print(f"   Result has <img> tag: {'<img' in result}")
    print(f"   Original has <span> tag: {'<span>' in html_content}")
    print(f"   Result has <span> tag: {'<span>' in result}")

if __name__ == "__main__":
    asyncio.run(test_html_extraction())

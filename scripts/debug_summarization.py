#!/usr/bin/env python3
"""Debug script to show posts, prompts, and summaries."""

import asyncio
import sys
import json
from pathlib import Path
from dotenv import dotenv_values

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
env_vars = dotenv_values(project_root / ".env")
import os
os.environ.update(env_vars)

from src.infrastructure.llm.summarizer import summarize_posts
from src.infrastructure.clients.llm_client import ResilientLLMClient
from src.infrastructure.monitoring.logger import get_logger

logger = get_logger(name="debug_summarization")

async def debug_summarization():
    """Debug summarization with detailed output."""
    
    # Sample posts (similar to what would come from channel)
    posts = [
        {
            "text": "В канале xor_journal обсуждаются новости о новых технологиях и разработке. Представлены результаты тестирования и анализа производительности последних обновлений в xor_journal.",
            "date": "2025-10-29T20:00:00Z"
        },
        {
            "text": "Пользователи xor_journal делятся опытом и советами по оптимизации работы с новыми инструментами.",
            "date": "2025-10-29T21:00:00Z"
        },
        {
            "text": "Обсуждаются последние обновления в области разработки и их влияние на производительность.",
            "date": "2025-10-29T22:00:00Z"
        }
    ]
    
    print("=" * 80)
    print("📋 INPUT POSTS")
    print("=" * 80)
    for i, post in enumerate(posts, 1):
        print(f"\nPost {i}:")
        print(f"  Text: {post['text']}")
        print(f"  Date: {post.get('date', 'N/A')}")
    
    print("\n" + "=" * 80)
    print("🔧 LLM CLIENT SETUP")
    print("=" * 80)
    llm_client = ResilientLLMClient()
    print(f"LLM URL from env: {os.getenv('LLM_URL', 'NOT SET')}")
    
    # Monkey patch to capture prompt
    original_generate = llm_client.generate
    captured_prompt = None
    
    async def capture_generate(prompt, temperature=0.2, max_tokens=256):
        nonlocal captured_prompt
        captured_prompt = prompt
        print("\n" + "=" * 80)
        print("📝 SENT PROMPT")
        print("=" * 80)
        print(prompt)
        print("=" * 80)
        return await original_generate(prompt, temperature, max_tokens)
    
    llm_client.generate = capture_generate
    
    print("\n" + "=" * 80)
    print("🚀 CALLING SUMMARIZE_POSTS")
    print("=" * 80)
    
    summary = await summarize_posts(posts, max_sentences=3, llm=llm_client)
    
    print("\n" + "=" * 80)
    print("📄 SUMMARY RESULT")
    print("=" * 80)
    print(summary)
    print("=" * 80)
    
    # Also test with actual channel posts
    print("\n" + "=" * 80)
    print("🔍 TESTING WITH REAL CHANNEL POSTS")
    print("=" * 80)
    
    try:
        from src.presentation.mcp.tools.digest_tools import get_channel_digest
        
        user_id = 204047849
        digest = await get_channel_digest(user_id, hours=24)
        
        print(f"\nUser ID: {user_id}")
        print(f"Channels found: {len(digest.get('channels', []))}")
        
        for channel in digest.get('channels', []):
            channel_name = channel.get('name', 'unknown')
            posts = channel.get('posts', [])
            summary = channel.get('summary', '')
            
            print(f"\n{'='*80}")
            print(f"📌 Channel: {channel_name}")
            print(f"{'='*80}")
            print(f"\nPosts ({len(posts)}):")
            for i, post in enumerate(posts[:3], 1):  # Show first 3
                text = post.get('text', '')[:200]
                print(f"  {i}. {text}...")
            
            print(f"\nSummary:")
            print(f"  {summary}")
            
    except Exception as e:
        print(f"\nError fetching real channel posts: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_summarization())


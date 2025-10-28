"""Streaming CLI for Mistral agent chat with real-time response display.

Following Python Zen: "Beautiful is better than ugly"
"""

import asyncio
import sys
import time
from pathlib import Path
from typing import Optional

# Add project root to path
_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(_root))
shared_path = _root / "shared"
sys.path.insert(0, str(shared_path))

from shared_package.clients.unified_client import UnifiedModelClient
from src.application.orchestrators.mistral_orchestrator import MistralChatOrchestrator
from src.infrastructure.repositories.json_conversation_repository import (
    JsonConversationRepository,
)
from src.presentation.mcp.orchestrators.mcp_mistral_wrapper import MCPMistralWrapper


class StreamingMistralChat:
    """Streaming chat interface for Mistral agent."""

    def __init__(self) -> None:
        """Initialize chat interface."""
        self.conversation_id = "default"
        self.orchestrator: Optional[MistralChatOrchestrator] = None
        self.wrapper: Optional[MCPMistralWrapper] = None
        self.running = True

    async def initialize(self) -> None:
        """Initialize orchestrator and MCP wrapper."""
        from pathlib import Path

        conversations_path = Path("data/conversations/conversations.json")
        conversation_repo = JsonConversationRepository(conversations_path)

        unified_client = UnifiedModelClient()

        self.wrapper = MCPMistralWrapper(
            server_script="src/presentation/mcp/server.py",
            orchestrator=None,
            use_docker=True,  # Use Docker MCP server via HTTP
        )
        await self.wrapper.initialize()

        self.orchestrator = MistralChatOrchestrator(
            unified_client=unified_client,
            conversation_repo=conversation_repo,
            model_name="mistral",
            mcp_wrapper=self.wrapper,
        )

        await self.orchestrator.initialize()

    def print_help(self) -> None:
        """Print help message."""
        print("\nAvailable commands:")
        print("  /help     - Show this help")
        print("  /tools    - List available MCP tools")
        print("  /history  - Show conversation history")
        print("  /clear    - Clear conversation")
        print("  /exit     - Exit chat")

    async def run(self) -> None:
        """Run streaming chat loop."""
        await self.initialize()

        print("=" * 70)
        print("Mistral Agent - Streaming Chat Mode")
        print("=" * 70)
        print("Type /help for commands")
        print("=" * 70)

        while self.running:
            try:
                user_input = input("\nYou: ").strip()

                if not user_input:
                    continue

                if user_input == "/exit":
                    print("Goodbye!")
                    break
                elif user_input == "/help":
                    self.print_help()
                elif user_input == "/tools":
                    await self.print_tools()
                elif user_input == "/history":
                    await self.print_history()
                elif user_input == "/clear":
                    self.conversation_id = f"conv_{asyncio.get_event_loop().time()}"
                    print("Conversation cleared.")
                else:
                    await self.process_message_streaming(user_input)

            except KeyboardInterrupt:
                print("\n\nGoodbye!")
                break
            except Exception as e:
                print(f"\nError: {e}")

    async def process_message_streaming(self, message: str) -> None:
        """Process user message with streaming display.

        Args:
            message: User message
        """
        if not self.orchestrator:
            print("Not initialized")
            return

        print("\nAssistant: ", end="", flush=True)
        
        # Display "thinking" indicator
        print("⠋ Thinking...", end="", flush=True)
        
        # Start processing in background
        response_task = asyncio.create_task(
            self.orchestrator.handle_message(message, self.conversation_id)
        )
        
        # Show spinner while waiting
        await self._display_thinking_indicator(response_task)
        
        # Wait for response
        response = await response_task
        
        # Clear thinking indicator
        print("\r" + " " * 30 + "\rAssistant: ", end="", flush=True)
        
        # Display response with typing effect
        await self._display_typing_effect(response)

    async def _display_thinking_indicator(self, task: asyncio.Task) -> None:
        """Display animated thinking indicator.
        
        Args:
            task: Async task to wait for
        """
        spinner_chars = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
        idx = 0
        
        while not task.done():
            await asyncio.sleep(0.1)
            print(f"\rAssistant: {spinner_chars[idx % len(spinner_chars)]} Thinking...", end="", flush=True)
            idx += 1

    async def _display_typing_effect(self, text: str) -> None:
        """Display text with typing effect.
        
        Args:
            text: Text to display
        """
        for char in text:
            print(char, end="", flush=True)
            await asyncio.sleep(0.01)  # Small delay for typing effect
        print()  # Newline after completion

    async def print_tools(self) -> None:
        """Print available tools."""
        if not self.wrapper:
            print("Not initialized")
            return

        tools = self.wrapper.get_available_tools()
        print(f"\nAvailable tools ({len(tools)}):")
        for tool in tools:
            print(f"  - {tool}")

    async def print_history(self) -> None:
        """Print conversation history."""
        if not self.orchestrator:
            print("Not initialized")
            return

        history = await self.orchestrator.conversation_repo.get_recent_messages(
            self.conversation_id, limit=10
        )

        if not history:
            print("No history yet")
            return

        print("\nConversation history:")
        for msg in history:
            role = msg["role"].capitalize()
            content = msg["content"][:100] + "..." if len(msg["content"]) > 100 else msg["content"]
            print(f"{role}: {content}")


async def main():
    """Main entry point."""
    chat = StreamingMistralChat()
    await chat.run()


if __name__ == "__main__":
    asyncio.run(main())


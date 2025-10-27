#!/usr/bin/env python3
"""
Day 08 Enhanced: Comprehensive Compression Testing.

This enhanced demo tests models with large queries, all compression strategies,
and displays detailed generator and reviewer outputs.

Following the Zen of Python:
- Beautiful is better than ugly
- Explicit is better than implicit
- Simple is better than complex
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

# Add shared to path
sys.path.insert(0, str(Path(__file__).parent.parent / "shared"))

from src.domain.services.compression.compressor import CompressionService
from src.domain.services.token_analyzer import TokenAnalyzer
from scripts.day_07_workflow import ModelClientAdapter
from src.domain.agents.code_generator import CodeGeneratorAgent
from src.domain.agents.code_reviewer import CodeReviewerAgent
from src.application.orchestrators.multi_agent_orchestrator import MultiAgentOrchestrator
from src.domain.messaging.message_schema import OrchestratorRequest


class Day08EnhancedDemo:
    """Enhanced compression demo with comprehensive testing."""
    
    def __init__(self):
        """Initialize the enhanced demo."""
        self.token_analyzer = TokenAnalyzer()
        self.compression_service = CompressionService()
        self.available_strategies = self.compression_service.get_available_strategies()
        self.results = {
            "models_tested": [],
            "compression_results": {},
            "generation_results": {},
            "reviewer_results": {}
        }
    
    async def run_demo(self) -> Dict[str, Any]:
        """Run the enhanced compression demo.
        
        Returns:
            Dictionary containing all demo results
        """
        print("\n" + "="*80)
        print("🗜️  DAY 08 ENHANCED: COMPREHENSIVE COMPRESSION TESTING")
        print("="*80)
        print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        # Import unified client
        try:
            from shared_package.clients.unified_client import UnifiedModelClient
        except ImportError as e:
            print(f"❌ Error: Could not import UnifiedModelClient: {e}")
            return self.results
        
        unified_client = UnifiedModelClient()
        
        try:
            # Check available models
            print("🔍 Checking model availability...")
            available_models = await self._check_model_availability(unified_client)
            
            if not available_models:
                print("❌ No models available")
                return self.results
            
            # Test each model
            for model_name in available_models:
                await self._test_model_comprehensively(model_name, unified_client)
            
            # Generate summary
            self._generate_summary()
            self._print_summary()
            
        finally:
            await unified_client.close()
        
        return self.results
    
    async def _check_model_availability(self, client) -> list:
        """Check which models are available.
        
        Args:
            client: UnifiedModelClient instance
            
        Returns:
            List of available model names
        """
        available = []
        models_to_check = ["starcoder", "mistral", "qwen", "tinyllama"]
        
        for model in models_to_check:
            try:
                is_available = await client.check_availability(model)
                if is_available:
                    print(f"   ✅ {model} is available")
                    available.append(model)
                else:
                    print(f"   ❌ {model} is not available")
            except Exception as e:
                print(f"   ⚠️  {model} check failed: {e}")
        
        return available
    
    async def _test_model_comprehensively(self, model_name: str, unified_client) -> None:
        """Test a model with all compression strategies.
        
        Args:
            model_name: Name of the model to test
            unified_client: UnifiedModelClient instance
        """
        print(f"\n{'='*80}")
        print(f"🔧 TESTING MODEL: {model_name.upper()}")
        print(f"{'='*80}")
        
        # Create three-stage queries
        queries = self._create_three_stage_queries()
        
        # Test each query size
        for stage, query in queries.items():
            print(f"\n📊 Testing {stage.upper()} query ({len(query)} chars)")
            
            # Count tokens
            tokens = self.token_analyzer.count_tokens(query)
            print(f"   Tokens: {int(tokens)}")
            
            # Test compression on all queries to demonstrate compression strategies
            await self._test_compression_with_generation(
                query, model_name, unified_client
            )
        
        self.results["models_tested"].append(model_name)
    
    def _create_three_stage_queries(self) -> Dict[str, str]:
        """Create three-stage queries of different sizes.
        
        Returns:
            Dictionary with short, medium, long queries
        """
        base_task = "Create a comprehensive Python authentication system"
        
        short = f"""{base_task} with password hashing using bcrypt, JWT token generation, 
        role-based access control, session management with secure cookies, and rate limiting 
        to prevent abuse. Include audit logging for security events, OAuth integration for 
        third-party login, and multi-factor authentication."""
        
        medium = f"""{base_task} with password hashing using bcrypt, JWT token generation and validation, 
        role-based access control (RBAC), session management with secure cookies, rate limiting to 
        prevent abuse, audit logging for security events, OAuth integration for third-party login, 
        multi-factor authentication (MFA), encryption for sensitive data, permission checking middleware, 
        password reset functionality, account lockout after failed attempts, secure password strength 
        validation, token refresh mechanism, CORS and CSRF protection, and API versioning support. 
        Ensure the system handles concurrent requests, implements secure password storage, supports 
        session invalidation, and provides comprehensive error handling."""
        
        long = f"""{base_task} that includes the following comprehensive features:
        
Password Security:
- Password hashing using bcrypt with appropriate salt rounds
- Secure password storage and validation
- Password strength validation with configurable requirements
- Password reset functionality with email verification
- Account lockout after multiple failed login attempts
- Secure password recovery flow

Authentication & Authorization:
- JWT token generation, validation, and refresh
- Role-based access control (RBAC) with hierarchical permissions
- Multi-factor authentication (MFA) support
- OAuth2 integration for third-party login (Google, GitHub, etc.)
- Session management with secure HTTP-only cookies
- Permission checking middleware for API endpoints
- API key management for service-to-service auth

Security Features:
- Rate limiting to prevent abuse and DDoS attacks
- CORS and CSRF protection
- Input validation and sanitization
- SQL injection prevention
- XSS (Cross-Site Scripting) protection
- Security headers implementation
- Audit logging for all security events
- Encryption for sensitive data at rest and in transit

User Management:
- User registration with email verification
- User profile management
- User account deletion and data export (GDPR compliance)
- Admin panel for user management
- User activity tracking and analytics

Session & Token Management:
- Secure session creation and invalidation
- Token refresh mechanism with configurable expiry
- Remember me functionality
- Concurrent session management
- Session hijacking prevention

API Features:
- API versioning support
- Comprehensive error handling and logging
- Request/response logging
- Health check endpoints
- API documentation generation
- Rate limiting per user/IP
- Webhook support for events

Infrastructure:
- Database connection pooling
- Redis caching for sessions and tokens
- Background job processing
- Email notification system
- Log aggregation and monitoring
- Health checks for all dependencies

The implementation should follow Python best practices including type hints, comprehensive docstrings, 
unit tests with pytest, integration tests, proper error handling, clean architecture principles, 
SOLID design patterns, and comprehensive logging."""
        
        return {
            "short": short,
            "medium": medium,
            "long": long
        }
    
    async def _test_compression_with_generation(
        self, query: str, model_name: str, unified_client
    ) -> None:
        """Test compression and code generation.
        
        Args:
            query: Original query
            model_name: Model to use
            unified_client: UnifiedModelClient instance
        """
        # Test each compression strategy
        for strategy in self.available_strategies:
            print(f"\n  🗜️  Testing {strategy.upper()} compression")
            
            try:
                # Compress the query
                # Use adaptive max_tokens based on query size
                query_tokens = self.token_analyzer.count_tokens(query)
                max_tokens = min(500, max(100, int(query_tokens * 0.5)))
                
                compression_result = self.compression_service.compress(
                    text=query,
                    max_tokens=max_tokens,
                    strategy=strategy
                )
                
                compressed_query = compression_result["compressed_text"]
                original_tokens = compression_result["original_tokens"]
                compressed_tokens = compression_result["compressed_tokens"]
                compression_ratio = compression_result["compression_ratio"]
                reduction = (1 - compression_ratio) * 100
                
                print(f"     Original: {original_tokens} tokens")
                print(f"     Compressed: {compressed_tokens} tokens")
                print(f"     Reduction: {reduction:.1f}%")
                
                # Generate code using compressed query
                await self._generate_and_review_code(
                    compressed_query, model_name, unified_client
                )
                
                # Store results
                if model_name not in self.results["compression_results"]:
                    self.results["compression_results"][model_name] = {}
                
                stage = self._determine_stage(len(query))
                if stage not in self.results["compression_results"][model_name]:
                    self.results["compression_results"][model_name][stage] = {}
                
                self.results["compression_results"][model_name][stage][strategy] = {
                    "success": True,
                    "original_tokens": original_tokens,
                    "compressed_tokens": compressed_tokens,
                    "compression_ratio": compression_ratio,
                    "reduction": reduction
                }
                
            except Exception as e:
                print(f"     ❌ Failed: {e}")
    
    async def _generate_and_review_code(
        self, prompt: str, model_name: str, unified_client
    ) -> None:
        """Generate and review code.
        
        Args:
            prompt: Compressed prompt
            model_name: Model to use
            unified_client: UnifiedModelClient instance
        """
        print(f"     🤖 Generating code with {model_name}...")
        
        # Create adapter and agents
        generator_adapter = ModelClientAdapter(unified_client, model_name=model_name)
        reviewer_adapter = ModelClientAdapter(unified_client, model_name="mistral")
        
        generator = CodeGeneratorAgent(model_client=generator_adapter)
        reviewer = CodeReviewerAgent(model_client=reviewer_adapter)
        
        # Create orchestrator
        orchestrator = MultiAgentOrchestrator(
            generator_agent=generator,
            reviewer_agent=reviewer
        )
        
        # Create request
        request = OrchestratorRequest(
            task_description=prompt,
            requirements=[
                "Include type hints",
                "Include docstrings",
                "Follow PEP8"
            ],
            language="python",
            model_name=model_name,
            reviewer_model_name="mistral"
        )
        
        try:
            # Process task
            result = await orchestrator.process_task(request)
            
            if result.success:
                print(f"     ✅ Code generated successfully")
                
                # Show preview
                if result.generation_result:
                    code_preview = result.generation_result.generated_code[:200]
                    print(f"     Code preview: {code_preview}...")
                
                # Show reviewer score
                if result.review_result:
                    score = result.review_result.code_quality_score
                    print(f"     Quality score: {score:.1f}/10")
                
                # Store results
                if model_name not in self.results["generation_results"]:
                    self.results["generation_results"][model_name] = []
                
                self.results["generation_results"][model_name].append({
                    "prompt": prompt[:100],
                    "success": True,
                    "quality_score": result.review_result.code_quality_score if result.review_result else 0
                })
            else:
                print(f"     ❌ Generation failed")
                
        except Exception as e:
            print(f"     ❌ Error: {e}")
    
    def _determine_stage(self, query_length: int) -> str:
        """Determine query stage based on length.
        
        Args:
            query_length: Length of query in characters
            
        Returns:
            Stage name (short/medium/long)
        """
        if query_length < 200:
            return "short"
        elif query_length < 500:
            return "medium"
        else:
            return "long"
    
    def _generate_summary(self) -> None:
        """Generate summary of results."""
        total_compressions = 0
        successful_compressions = 0
        
        for model, stages in self.results["compression_results"].items():
            for stage, strategies in stages.items():
                for strategy, result in strategies.items():
                    total_compressions += 1
                    if result.get("success"):
                        successful_compressions += 1
        
        self.results["summary"] = {
            "models_tested": len(self.results["models_tested"]),
            "total_compressions": total_compressions,
            "successful_compressions": successful_compressions,
            "success_rate": (successful_compressions / max(1, total_compressions)) * 100,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    
    def _print_summary(self) -> None:
        """Print comprehensive summary."""
        summary = self.results["summary"]
        
        print("\n" + "="*80)
        print("📊 COMPRESSION TESTING SUMMARY")
        print("="*80)
        print(f"Models tested: {summary['models_tested']}")
        print(f"Total compressions: {summary['total_compressions']}")
        print(f"Successful compressions: {summary['successful_compressions']}")
        print(f"Success rate: {summary['success_rate']:.1f}%")
        print(f"Completed at: {summary['timestamp']}")
        
        if summary['success_rate'] >= 80:
            print("\n🎉 Excellent! Compression strategies working well!")
        elif summary['success_rate'] >= 50:
            print("\n✅ Good! Most compressions successful.")
        else:
            print("\n⚠️  Some compressions failed. Check output above.")
        
        print("\n✅ Day 08 Enhanced demo completed!\n")


async def main():
    """Main entry point."""
    demo = Day08EnhancedDemo()
    results = await demo.run_demo()
    
    return 0 if results.get("summary", {}).get("success_rate", 0) >= 50 else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))


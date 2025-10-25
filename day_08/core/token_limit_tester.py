"""
Token Limit Tester for three-stage query testing.

This module provides the TokenLimitTester class that generates and tests
queries at three different stages (short/medium/long) that adapt to
different model capabilities.
"""

import logging
from typing import Dict, List, Optional

from core.token_analyzer import SimpleTokenCounter
from models.data_models import ThreeStageResult
from utils.logging import LoggerFactory

# Configure logging
logger = LoggerFactory.create_logger(__name__)


class TokenLimitTester:
    """
    Tester for three-stage token limit experiments.
    
    Generates queries of different lengths and complexities to test
    model behavior at various token limit stages.
    
    Attributes:
        token_counter: TokenCounter instance for counting tokens
        model_capabilities: Dictionary mapping model names to their capabilities
        logger: Logger instance for structured logging
        
    Example:
        ```python
        from core.token_limit_tester import TokenLimitTester
        from core.token_analyzer import SimpleTokenCounter
        
        # Initialize tester
        token_counter = SimpleTokenCounter()
        tester = TokenLimitTester(token_counter)
        
        # Run three-stage test
        result = await tester.run_three_stage_test("starcoder")
        
        print(f"Short query tokens: {result.short_query_tokens}")
        print(f"Medium query tokens: {result.medium_query_tokens}")
        print(f"Long query tokens: {result.long_query_tokens}")
        ```
    """
    
    def __init__(self, token_counter: Optional[SimpleTokenCounter] = None):
        """
        Initialize the token limit tester.
        
        Args:
            token_counter: Optional TokenCounter instance
            
        Example:
            ```python
            from core.token_limit_tester import TokenLimitTester
            from core.token_analyzer import SimpleTokenCounter
            
            token_counter = SimpleTokenCounter()
            tester = TokenLimitTester(token_counter)
            ```
        """
        self.token_counter = token_counter or SimpleTokenCounter()
        self.logger = LoggerFactory.create_logger(__name__)
        
        # Model-specific capabilities and limits
        self.model_capabilities = {
            "starcoder": {
                "max_tokens": 8192,
                "recommended": 7000,
                "short_target": 100,
                "medium_target": 500,
                "long_target": 1500,
                "complexity_multiplier": 1.0
            },
            "mistral": {
                "max_tokens": 32768,
                "recommended": 30000,
                "short_target": 80,
                "medium_target": 400,
                "long_target": 1200,
                "complexity_multiplier": 0.8
            },
            "qwen": {
                "max_tokens": 32768,
                "recommended": 30000,
                "short_target": 90,
                "medium_target": 450,
                "long_target": 1300,
                "complexity_multiplier": 0.9
            },
            "tinyllama": {
                "max_tokens": 2048,
                "recommended": 1500,
                "short_target": 50,
                "medium_target": 200,
                "long_target": 800,
                "complexity_multiplier": 0.5
            }
        }
        
        self.logger.info("Initialized TokenLimitTester")
    
    def generate_short_query(self, model_name: str) -> str:
        """
        Generate a short query suitable for the model.
        
        Args:
            model_name: Name of the model
            
        Returns:
            Short query string
            
        Example:
            ```python
            short_query = tester.generate_short_query("starcoder")
            print(f"Short query: {short_query}")
            ```
        """
        capabilities = self.model_capabilities.get(model_name, self.model_capabilities["starcoder"])
        
        # Enhanced short query with more detailed requirements
        query = """Write a comprehensive Python function to calculate the factorial of a number with advanced features.

Detailed Requirements:
- Function name: factorial
- Input: integer n (must be non-negative)
- Output: factorial of n as integer
- Handle edge cases: n=0 (return 1), n=1 (return 1), negative numbers (raise ValueError)
- Include comprehensive type hints using typing module
- Add detailed docstring following Google style
- Include input validation with meaningful error messages
- Add performance optimization for large numbers
- Include unit tests using pytest
- Add example usage in docstring
- Handle potential overflow for very large numbers
- Include logging for debugging purposes
- Add support for memoization to improve performance
- Include benchmark timing functionality
- Add support for different calculation methods (iterative, recursive, math.gamma)

Example usage:
```python
# Basic usage
result = factorial(5)  # Should return 120

# Edge cases
factorial(0)  # Should return 1
factorial(1)  # Should return 1

# Error handling
factorial(-1)  # Should raise ValueError

# Performance testing
factorial(1000)  # Should handle large numbers efficiently
```

Additional Requirements:
- The function should be production-ready
- Include proper error handling and logging
- Add comprehensive unit tests
- Include performance benchmarks
- Support for different calculation algorithms
- Memory-efficient implementation
- Thread-safe implementation
- Include documentation and examples
- Add type checking with mypy compatibility
- Include code coverage analysis setup"""
        
        # Adjust complexity based on model capabilities
        if capabilities["complexity_multiplier"] < 0.7:
            # Simplify for smaller models like TinyLlama
            query = """Write a Python function to calculate factorial with basic features.

def factorial(n):
    # Calculate factorial of n
    # Handle edge cases
    # Include type hints
    # Add docstring
    # Return the result

Include basic error handling and example usage."""
        
        return query
    
    def generate_medium_query(self, model_name: str) -> str:
        """
        Generate a medium complexity query suitable for the model.
        
        Args:
            model_name: Name of the model
            
        Returns:
            Medium complexity query string
            
        Example:
            ```python
            medium_query = tester.generate_medium_query("mistral")
            print(f"Medium query: {medium_query}")
            ```
        """
        capabilities = self.model_capabilities.get(model_name, self.model_capabilities["starcoder"])
        
        # Enhanced medium complexity coding task with comprehensive requirements
        query = """Implement a comprehensive Binary Search Tree (BST) class in Python with advanced features and complete functionality.

DETAILED REQUIREMENTS:

1. Class Structure and Design:
   - Class name: BinarySearchTree
   - Node class: BSTNode with value, left, right, parent attributes
   - Include comprehensive type hints using typing module
   - Add detailed docstrings following Google style
   - Implement proper encapsulation and data hiding
   - Add support for generic types (BSTNode[T])
   - Include proper __repr__ and __str__ methods

2. Core Methods Implementation:
   - insert(value): Insert a new value into the BST with duplicate handling
   - search(value): Search for a value, return True if found, False otherwise
   - delete(value): Delete a value from the BST with proper rebalancing
   - find(value): Find and return the node containing the value
   - inorder_traversal(): Return list of values in sorted order
   - preorder_traversal(): Return list of values in preorder
   - postorder_traversal(): Return list of values in postorder
   - level_order_traversal(): Return list of values in level order (BFS)

3. Advanced Methods:
   - find_min(): Find minimum value in the tree
   - find_max(): Find maximum value in the tree
   - height(): Calculate height of the tree
   - size(): Return number of nodes in the tree
   - is_empty(): Check if tree is empty
   - is_valid_bst(): Validate if the tree maintains BST property
   - balance_factor(): Calculate balance factor for each node
   - get_successor(value): Get successor of a given value
   - get_predecessor(value): Get predecessor of a given value
   - range_query(min_val, max_val): Get all values in range
   - kth_smallest(k): Find kth smallest element
   - kth_largest(k): Find kth largest element

4. Error Handling and Validation:
   - Handle duplicate insertions gracefully with custom exception
   - Handle deletion of non-existent values with informative messages
   - Validate input parameters with type checking
   - Handle edge cases (empty tree, single node, etc.)
   - Add custom exceptions: BSTEmptyError, BSTValueNotFoundError
   - Include input validation for all public methods

5. Performance and Optimization:
   - Implement iterative versions of recursive methods
   - Add memoization for expensive operations
   - Include performance benchmarking methods
   - Add memory usage tracking
   - Implement efficient range queries
   - Add support for bulk operations

6. Testing and Documentation:
   - Include comprehensive unit tests using pytest
   - Add integration tests for complex scenarios
   - Include performance benchmarks
   - Add example usage in docstring
   - Include edge case testing
   - Add property-based testing with hypothesis

7. Additional Features:
   - Serialization/deserialization support (JSON, pickle)
   - Iterator protocol implementation
   - Support for custom comparison functions
   - Thread-safe operations (if applicable)
   - Memory-efficient implementation
   - Support for different data types

8. Example Usage:
```python
# Basic usage
bst = BinarySearchTree()
bst.insert(50)
bst.insert(30)
bst.insert(70)
bst.insert(20)
bst.insert(40)
bst.insert(60)
bst.insert(80)

# Traversal methods
print(bst.inorder_traversal())    # [20, 30, 40, 50, 60, 70, 80]
print(bst.preorder_traversal())   # [50, 30, 20, 40, 70, 60, 80]
print(bst.postorder_traversal())  # [20, 40, 30, 60, 80, 70, 50]

# Search and delete
print(bst.search(40))  # True
bst.delete(40)
print(bst.search(40))  # False

# Advanced operations
print(bst.find_min())  # 20
print(bst.find_max())  # 80
print(bst.height())    # 3
print(bst.size())      # 6

# Range queries
print(bst.range_query(30, 70))  # [30, 40, 50, 60, 70]
print(bst.kth_smallest(3))      # 40
```

9. Implementation Requirements:
   - Use proper object-oriented design principles
   - Follow PEP 8 style guidelines
   - Include comprehensive error handling
   - Add logging for debugging
   - Implement efficient algorithms
   - Include proper documentation
   - Add type annotations throughout
   - Include performance optimizations
   - Handle edge cases properly
   - Make the implementation production-ready

Please provide a complete, well-documented implementation with all methods working correctly and comprehensive test coverage."""
        
        # Adjust complexity based on model capabilities
        if capabilities["complexity_multiplier"] < 0.7:
            # Simplify for smaller models
            query = """Implement a Binary Search Tree class with essential operations:

class BinarySearchTree:
    def __init__(self):
        self.root = None
    
    def insert(self, value):
        # Insert value into BST
    
    def search(self, value):
        # Search for value, return True if found
    
    def delete(self, value):
        # Delete value from BST
    
    def inorder_traversal(self):
        # Return sorted list of values
    
    def find_min(self):
        # Find minimum value
    
    def find_max(self):
        # Find maximum value
    
    def height(self):
        # Calculate tree height
    
    def size(self):
        # Return number of nodes

Include proper docstrings, type hints, and basic error handling."""
        
        return query
    
    def generate_long_query(self, model_name: str) -> str:
        """
        Generate a long, complex query that exceeds model limits.
        
        Args:
            model_name: Name of the model
            
        Returns:
            Long, complex query string
            
        Example:
            ```python
            long_query = tester.generate_long_query("starcoder")
            print(f"Long query: {long_query}")
            ```
        """
        capabilities = self.model_capabilities.get(model_name, self.model_capabilities["starcoder"])
        
        # Extremely comprehensive and detailed coding task that will exceed limits
        base_query = """Implement a comprehensive, production-ready REST API server using FastAPI with advanced features, microservices architecture, and enterprise-grade functionality.

COMPREHENSIVE REQUIREMENTS:

1. PROJECT STRUCTURE AND SETUP:
   - Use FastAPI framework with proper project structure following Clean Architecture
   - Include requirements.txt with all dependencies and version pinning
   - Add proper error handling, logging, and monitoring throughout
   - Implement CORS middleware with configurable origins
   - Add request/response validation using Pydantic models with comprehensive schemas
   - Include API documentation with Swagger UI and ReDoc
   - Add OpenAPI 3.0 specification with detailed examples
   - Implement proper project structure with separation of concerns
   - Add configuration management with environment variables
   - Include Docker containerization with multi-stage builds
   - Add Kubernetes deployment configurations
   - Implement CI/CD pipeline with GitHub Actions
   - Add comprehensive testing setup with pytest and coverage

2. DATABASE INTEGRATION AND ORM:
   - Use SQLAlchemy ORM with PostgreSQL database
   - Implement database models for User, Product, Order, Category, Review, Payment, Shipping
   - Add database migrations using Alembic with proper versioning
   - Include proper foreign key relationships and constraints
   - Implement database connection pooling with async support
   - Add database health check endpoint with detailed metrics
   - Include database backup and restore functionality
   - Add database performance monitoring and query optimization
   - Implement database sharding for scalability
   - Add database replication setup for high availability
   - Include database security with encryption at rest
   - Add database audit logging for compliance

3. AUTHENTICATION AND AUTHORIZATION:
   - Implement JWT-based authentication with refresh tokens
   - Add user registration and login endpoints with email verification
   - Include password hashing using bcrypt with salt rounds
   - Implement role-based access control (admin, user, moderator, vendor)
   - Add token refresh mechanism with automatic renewal
   - Include logout functionality with token blacklisting
   - Implement OAuth2 integration (Google, GitHub, Microsoft)
   - Add two-factor authentication (2FA) with TOTP
   - Include password reset functionality with secure tokens
   - Add account lockout after failed attempts
   - Implement session management with Redis
   - Add API key authentication for external services
   - Include audit logging for all authentication events

4. USER MANAGEMENT SYSTEM:
   - User CRUD operations with comprehensive validation
   - User profile management with avatar upload
   - Password change functionality with security checks
   - User search and filtering with advanced queries
   - User activity logging and analytics
   - Email verification system with templates
   - User preferences and settings management
   - User notification system (email, SMS, push)
   - User privacy controls and GDPR compliance
   - User account deactivation and deletion
   - User social features (followers, following)
   - User reputation and rating system
   - User support ticket system

5. PRODUCT MANAGEMENT SYSTEM:
   - Product CRUD operations with rich metadata
   - Product categorization with hierarchical structure
   - Product search with advanced filters (price, category, rating, availability)
   - Product image upload and management with CDN integration
   - Inventory tracking with real-time updates
   - Product reviews and ratings system with moderation
   - Product recommendation engine using ML
   - Product comparison functionality
   - Product wishlist and favorites
   - Product variants (size, color, material)
   - Product bundles and packages
   - Product analytics and reporting
   - Product SEO optimization

6. ORDER MANAGEMENT SYSTEM:
   - Shopping cart functionality with persistence
   - Order creation and processing with validation
   - Order status tracking with real-time updates
   - Order history for users with detailed views
   - Order cancellation and refunds with approval workflow
   - Payment integration with multiple providers (Stripe, PayPal, Square)
   - Order fulfillment and shipping integration
   - Order returns and exchanges management
   - Order analytics and reporting
   - Order notification system
   - Order fraud detection and prevention
   - Order tax calculation and compliance
   - Order discount and coupon system

7. COMPREHENSIVE API ENDPOINTS:
   - Authentication endpoints: /auth/login, /auth/register, /auth/refresh, /auth/logout
   - User endpoints: /users/, /users/{id}, /users/profile, /users/preferences
   - Product endpoints: /products/, /products/{id}, /products/search, /products/categories
   - Order endpoints: /orders/, /orders/{id}, /orders/cart, /orders/history
   - Admin endpoints: /admin/users, /admin/products, /admin/orders, /admin/analytics
   - Payment endpoints: /payments/, /payments/methods, /payments/process
   - Shipping endpoints: /shipping/, /shipping/rates, /shipping/tracking
   - Review endpoints: /reviews/, /reviews/{id}, /reviews/ratings
   - Notification endpoints: /notifications/, /notifications/preferences
   - Analytics endpoints: /analytics/, /analytics/dashboard, /analytics/reports
   - Health check endpoints: /health/, /health/db, /health/redis, /health/external

8. DATA VALIDATION AND ERROR HANDLING:
   - Comprehensive input validation with custom validators
   - Custom exception classes with proper inheritance
   - Proper HTTP status codes with meaningful messages
   - Error response formatting with consistent structure
   - Request logging and monitoring with correlation IDs
   - Rate limiting per user/IP with configurable limits
   - Input sanitization and XSS protection
   - SQL injection prevention with parameterized queries
   - CSRF protection with token validation
   - Request size limits and timeout handling
   - Graceful degradation for external service failures
   - Circuit breaker pattern for external dependencies

9. TESTING AND QUALITY ASSURANCE:
   - Unit tests for all endpoints with high coverage
   - Integration tests for database operations
   - API documentation with comprehensive examples
   - Postman collection for testing and development
   - Performance testing with load testing tools
   - Security testing with vulnerability scanning
   - End-to-end testing with automated test suites
   - Contract testing for API compatibility
   - Property-based testing with hypothesis
   - Mutation testing for code quality
   - Code coverage analysis with reporting
   - Static code analysis with linting tools

10. ADVANCED FEATURES:
    - File upload handling with virus scanning
    - Email notification system with templates
    - Caching with Redis for performance
    - Background task processing with Celery
    - API rate limiting with Redis
    - Health check endpoints with detailed metrics
    - Metrics and monitoring with Prometheus
    - Logging with structured JSON format
    - Distributed tracing with OpenTelemetry
    - Service mesh integration with Istio
    - Event-driven architecture with message queues
    - Microservices communication patterns

11. BUSINESS LOGIC AND FEATURES:
    - Discount and coupon system with complex rules
    - Loyalty program implementation with points
    - Recommendation engine using collaborative filtering
    - Analytics and reporting with dashboards
    - Multi-currency support with real-time rates
    - Tax calculation system with compliance
    - Shipping cost calculation with carriers
    - Inventory management system with alerts
    - Supplier management with vendor portal
    - Customer support integration with ticketing
    - Marketing automation with campaigns
    - A/B testing framework for features
    - Personalization engine for user experience

12. SECURITY AND COMPLIANCE:
    - SQL injection prevention with ORM
    - XSS protection with input sanitization
    - CSRF protection with token validation
    - Input sanitization and validation
    - Rate limiting per user/IP with Redis
    - API key management with rotation
    - Audit logging for compliance
    - Data encryption at rest and in transit
    - Secure communication with HTTPS/TLS
    - Security headers implementation
    - Content Security Policy (CSP)
    - OWASP security guidelines compliance
    - GDPR compliance with data protection
    - PCI DSS compliance for payments
    - SOC 2 compliance for security

13. PERFORMANCE AND SCALABILITY:
    - Database query optimization with indexing
    - Caching strategies with Redis
    - Load balancing with multiple instances
    - Horizontal scaling with microservices
    - CDN integration for static assets
    - Database connection pooling
    - Async/await for I/O operations
    - Memory optimization and profiling
    - CPU optimization with profiling
    - Network optimization with compression
    - Caching layers with invalidation
    - Performance monitoring and alerting
    - Auto-scaling based on metrics

14. MONITORING AND OBSERVABILITY:
    - Application metrics with Prometheus
    - Logging with structured JSON
    - Distributed tracing with Jaeger
    - Health checks with detailed status
    - Performance monitoring with APM
    - Error tracking with Sentry
    - Uptime monitoring with alerts
    - Resource monitoring with Grafana
    - Custom dashboards for business metrics
    - Alerting with PagerDuty integration
    - SLA monitoring and reporting
    - Capacity planning with metrics

15. DEPLOYMENT AND DEVOPS:
    - Docker containerization with multi-stage builds
    - Kubernetes deployment with Helm charts
    - CI/CD pipeline with GitHub Actions
    - Infrastructure as Code with Terraform
    - Configuration management with Ansible
    - Secret management with Vault
    - Environment management (dev, staging, prod)
    - Blue-green deployment strategy
    - Canary deployment with monitoring
    - Rollback procedures with automation
    - Disaster recovery with backups
    - High availability with redundancy

This is a comprehensive e-commerce API that should handle all aspects of a modern online shopping platform with enterprise-grade features, security, scalability, and maintainability. The implementation should be production-ready with proper error handling, logging, monitoring, testing, and documentation throughout the entire codebase."""
        
        # Make it even longer for models with higher limits
        if capabilities["max_tokens"] > 16000:
            query = base_query + """

16. MICROSERVICES ARCHITECTURE:
    - Service decomposition with domain boundaries
    - Inter-service communication with gRPC
    - Service discovery with Consul
    - API Gateway with Kong
    - Event-driven architecture with Kafka
    - Saga pattern for distributed transactions
    - Circuit breaker pattern for resilience
    - Bulkhead pattern for isolation
    - Retry pattern with exponential backoff
    - Timeout pattern for responsiveness
    - Service mesh with Istio
    - Distributed configuration management
    - Service monitoring and health checks

17. DATA ANALYTICS AND MACHINE LEARNING:
    - Real-time analytics with Apache Kafka
    - Data warehousing with PostgreSQL
    - Business intelligence with dashboards
    - Machine learning pipeline with scikit-learn
    - Recommendation engine with collaborative filtering
    - Fraud detection with anomaly detection
    - Customer segmentation with clustering
    - Predictive analytics with time series
    - A/B testing framework with statistical analysis
    - Data visualization with interactive charts
    - Report generation with automated scheduling
    - Data export with multiple formats

18. INTERNATIONALIZATION AND LOCALIZATION:
    - Multi-language support with i18n
    - Currency conversion with real-time rates
    - Timezone handling with proper conversion
    - Localized content with region-specific data
    - Cultural adaptation for different markets
    - Legal compliance with regional laws
    - Payment methods by region
    - Shipping options by country
    - Tax calculation by jurisdiction
    - Address validation by country
    - Phone number formatting by region
    - Date/time formatting by locale

19. ADVANCED INTEGRATION FEATURES:
    - Third-party API integration with rate limiting
    - Webhook system for real-time notifications
    - GraphQL API alongside REST
    - Real-time communication with WebSockets
    - Server-sent events for live updates
    - Message queue integration with RabbitMQ
    - Event sourcing with CQRS pattern
    - CQRS with separate read/write models
    - Domain events with event store
    - Integration testing with test containers
    - Contract testing with Pact
    - API versioning with backward compatibility

20. ENTERPRISE FEATURES:
    - Multi-tenancy with data isolation
    - White-label solution with customization
    - Enterprise SSO with SAML/OAuth
    - Role-based permissions with fine-grained control
    - Audit trail with comprehensive logging
    - Data retention policies with automation
    - Backup and disaster recovery procedures
    - Compliance reporting with automated generation
    - SLA monitoring with performance metrics
    - Support ticket system with escalation
    - Knowledge base with search functionality
    - Training materials and documentation

The implementation should be enterprise-ready with proper architecture, security, scalability, maintainability, and comprehensive testing coverage."""
        
        else:
            query = base_query
        
        return query
    
    async def run_three_stage_test(self, model_name: str) -> ThreeStageResult:
        """
        Run three-stage token limit test for a model.
        
        Args:
            model_name: Name of the model to test
            
        Returns:
            ThreeStageResult containing all test results
            
        Example:
            ```python
            result = await tester.run_three_stage_test("starcoder")
            print(f"Test completed: {result.success}")
            print(f"Short query tokens: {result.short_query_tokens}")
            ```
        """
        try:
            self.logger.info(f"Starting three-stage test for {model_name}")
            
            # Generate queries for each stage
            short_query = self.generate_short_query(model_name)
            medium_query = self.generate_medium_query(model_name)
            long_query = self.generate_long_query(model_name)
            
            # Count tokens for each query
            short_tokens = self.token_counter.count_tokens(short_query, model_name).count
            medium_tokens = self.token_counter.count_tokens(medium_query, model_name).count
            long_tokens = self.token_counter.count_tokens(long_query, model_name).count
            
            # Get model limits
            model_limits = self.token_counter.get_model_limits(model_name)
            
            # Determine if queries exceed limits
            short_exceeds = short_tokens > model_limits.max_input_tokens
            medium_exceeds = medium_tokens > model_limits.max_input_tokens
            long_exceeds = long_tokens > model_limits.max_input_tokens
            
            self.logger.info(f"Token counts - Short: {short_tokens}, Medium: {medium_tokens}, Long: {long_tokens}")
            self.logger.info(f"Model limit: {model_limits.max_input_tokens}")
            
            return ThreeStageResult(
                model_name=model_name,
                short_query=short_query,
                medium_query=medium_query,
                long_query=long_query,
                short_query_tokens=short_tokens,
                medium_query_tokens=medium_tokens,
                long_query_tokens=long_tokens,
                model_limits=model_limits,
                short_exceeds_limit=short_exceeds,
                medium_exceeds_limit=medium_exceeds,
                long_exceeds_limit=long_exceeds,
                success=True
            )
            
        except Exception as e:
            self.logger.error(f"Three-stage test failed for {model_name}: {e}")
            return ThreeStageResult(
                model_name=model_name,
                short_query="",
                medium_query="",
                long_query="",
                short_query_tokens=0,
                medium_query_tokens=0,
                long_query_tokens=0,
                model_limits=self.token_counter.get_model_limits(model_name),
                short_exceeds_limit=False,
                medium_exceeds_limit=False,
                long_exceeds_limit=False,
                success=False,
                error_message=str(e)
            )
    
    def get_model_capabilities(self, model_name: str) -> Dict[str, any]:
        """
        Get capabilities information for a specific model.
        
        Args:
            model_name: Name of the model
            
        Returns:
            Dictionary containing model capabilities
            
        Example:
            ```python
            capabilities = tester.get_model_capabilities("starcoder")
            print(f"Max tokens: {capabilities['max_tokens']}")
            ```
        """
        return self.model_capabilities.get(model_name, self.model_capabilities["starcoder"]).copy()
    
    def get_all_model_capabilities(self) -> Dict[str, Dict[str, any]]:
        """
        Get capabilities information for all supported models.
        
        Returns:
            Dictionary mapping model names to their capabilities
            
        Example:
            ```python
            all_capabilities = tester.get_all_model_capabilities()
            for model, caps in all_capabilities.items():
                print(f"{model}: {caps['max_tokens']} max tokens")
            ```
        """
        return {model: caps.copy() for model, caps in self.model_capabilities.items()}

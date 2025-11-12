# Day 12 - PDF Digest Architecture Documentation

## Overview

This document describes the architecture of the PDF Digest system, including post collection workflow, PDF generation flow, caching strategy, error handling, and database schema.

## System Architecture

### High-Level Overview

```
┌─────────────────┐
│  Telegram Bot   │
│   (User Input)   │
└────────┬─────────┘
         │
         ▼
┌─────────────────┐
│  Bot Handler    │
│ callback_digest  │
└────────┬─────────┘
         │
         ├──► Cache Check
         │    ├─ Hit: Return cached PDF
         │    └─ Miss: Generate PDF
         │
         ▼
┌─────────────────┐
│   MCP Client    │
│  (Tool Calls)   │
└────────┬─────────┘
         │
         ├──► get_posts_from_db
         ├──► summarize_posts (per channel)
         ├──► format_digest_markdown
         ├──► combine_markdown_sections
         └──► convert_markdown_to_pdf
         │
         ▼
┌─────────────────┐
│   MongoDB       │
│  (Post Storage) │
└─────────────────┘
```

## Post Collection Flow

### Hourly Collection Process

```mermaid
graph TD
    A[PostFetcherWorker Starts] --> B{Time to Run?}
    B -->|No| C[Wait 60 seconds]
    C --> B
    B -->|Yes| D[Query MongoDB for Active Channels]
    D --> E{Channels Found?}
    E -->|No| F[Log: No channels]
    E -->|Yes| G[For Each Channel]
    G --> H[Get last_fetch timestamp]
    H --> I[Fetch Posts from Telegram]
    I --> J[Save Posts via Repository]
    J --> K{Duplicate Check}
    K -->|Duplicate| L[Skip Post]
    K -->|New| M[Save to MongoDB]
    M --> N[Update last_fetch]
    N --> O{More Channels?}
    O -->|Yes| G
    O -->|No| P[Log Statistics]
    P --> Q[Wait for Next Interval]
    Q --> B
    L --> O
```

### Deduplication Strategy

```mermaid
graph TD
    A[New Post Received] --> B{Check message_id<br/>in last 24h?}
    B -->|Found| C[Skip: Duplicate by message_id]
    B -->|Not Found| D{Check content_hash<br/>in last 7 days?}
    D -->|Found| E[Skip: Duplicate by content_hash]
    D -->|Not Found| F[Save Post to MongoDB]
    F --> G[Add message_id index]
    G --> H[Add content_hash index]
    H --> I[Set TTL: 7 days]
```

**Hybrid Deduplication:**
1. **Primary check**: `message_id` + `channel_username` (24h window) - Fast lookup
2. **Secondary check**: `content_hash` (SHA256) (7-day window) - Catches edits/reposts

## PDF Generation Flow

### Complete Workflow

```mermaid
sequenceDiagram
    participant User
    participant Bot
    participant Cache
    participant MCP
    participant DB
    participant LLM
    participant PDF

    User->>Bot: Click "Digest" button
    Bot->>Bot: Show upload_document action
    Bot->>Cache: Check cache (user_id + date_hour)
    
    alt Cache Hit
        Cache->>Bot: Return cached PDF
        Bot->>User: Send PDF immediately
    else Cache Miss
        Bot->>MCP: get_posts_from_db(user_id, hours=24)
        MCP->>DB: Query posts by user subscriptions
        DB->>MCP: Return posts grouped by channel
        MCP->>Bot: Return posts_by_channel
        
        loop For each channel
            Bot->>MCP: summarize_posts(posts, channel)
            MCP->>LLM: Generate summary
            LLM->>MCP: Return summary text
            MCP->>Bot: Return summary dict
        end
        
        Bot->>MCP: format_digest_markdown(summaries, metadata)
        MCP->>Bot: Return formatted markdown
        
        Bot->>MCP: combine_markdown_sections(sections)
        MCP->>Bot: Return combined markdown
        
        Bot->>MCP: convert_markdown_to_pdf(markdown)
        MCP->>PDF: Convert markdown to PDF
        PDF->>MCP: Return PDF bytes (base64)
        MCP->>Bot: Return PDF result
        
        Bot->>Cache: Store PDF (1 hour TTL)
        Bot->>User: Send PDF document
    end
```

### Error Handling Flow

```mermaid
graph TD
    A[User Requests Digest] --> B[Check Cache]
    B -->|Hit| C[Send Cached PDF]
    B -->|Miss| D[Generate PDF]
    D --> E{get_posts_from_db}
    E -->|No Posts| F[Send: No posts message]
    E -->|Error| G{Fallback Available?}
    E -->|Success| H[Summarize Channels]
    H --> I{summarize_posts}
    I -->|Error| J[Use Fallback Summary]
    I -->|Success| K[Format Markdown]
    K --> L{format_digest_markdown}
    L -->|Error| M[Return Error Markdown]
    L -->|Success| N[Combine Sections]
    N --> O{combine_markdown_sections}
    O -->|Error| P[Return Empty Combined]
    O -->|Success| Q[Convert to PDF]
    Q --> R{convert_markdown_to_pdf}
    R -->|Error| S[Fallback to Text Digest]
    R -->|Success| T[Cache PDF]
    T --> U[Send PDF]
    G -->|Yes| S
    G -->|No| V[Send Error Message]
    J --> K
    M --> Q
    P --> Q
```

## Caching Strategy

### Cache Architecture

```mermaid
graph LR
    A[PDF Generation] --> B{Cache Check}
    B -->|Hit| C[Return Cached PDF]
    B -->|Miss| D[Generate PDF]
    D --> E[Cache PDF]
    E --> F[Return PDF]
    
    G[Cache Key] --> H[user_id:date_hour]
    H --> I[Example: 123456789:2024-01-15-20]
    
    J[TTL: 1 hour] --> K[Automatic Expiration]
    K --> L[Cache Miss After Expiry]
```

**Cache Key Format:**
```
digest_pdf:{user_id}:{date_hour}
Example: digest_pdf:123456789:2024-01-15-20
```

**Cache Implementation:**
- In-memory cache (simple, fast)
- TTL: 1 hour (configurable via `pdf_cache_ttl_hours`)
- User-specific keys
- Automatic expiration check on get

**Cache Benefits:**
- Instant PDF delivery on cache hit
- Reduced MCP tool calls
- Lower LLM usage
- Improved user experience

## Database Schema

### Posts Collection

```mermaid
erDiagram
    POSTS {
        ObjectId _id PK
        string channel_username "indexed"
        string message_id "indexed"
        string content_hash "indexed"
        int user_id "indexed"
        string text
        datetime date "indexed, TTL: 7 days"
        datetime fetched_at
        int views "nullable"
        object metadata
    }
    
    CHANNELS {
        ObjectId _id PK
        string channel_username
        int user_id "indexed"
        bool active "indexed"
        datetime last_fetch
    }
```

**MongoDB Schema:**

```json
{
  "_id": ObjectId("507f1f77bcf86cd799439011"),
  "channel_username": "channel1",
  "message_id": "12345",
  "content_hash": "sha256_hash_here",
  "user_id": 123456789,
  "text": "Post text content",
  "date": ISODate("2024-01-15T20:00:00Z"),
  "fetched_at": ISODate("2024-01-15T20:00:00Z"),
  "views": 100,
  "metadata": {
    "edit_date": null,
    "media_type": null
  }
}
```

**Indexes:**
1. `(channel_username, message_id)` - Fast message_id lookup
2. `(content_hash, date)` - Content hash deduplication
3. `(user_id, date)` - Subscription-based queries
4. `date` - TTL index (7 days expiration)

**TTL (Time To Live):**
- Posts expire after 7 days automatically
- MongoDB automatically removes expired documents

## Error Handling Strategy

### Error Recovery Levels

```mermaid
graph TD
    A[PDF Generation Request] --> B{Level 1: Cache}
    B -->|Error| C[Log Error, Continue]
    B -->|Success| D[Return Cached PDF]
    B -->|Miss| E{Level 2: get_posts_from_db}
    E -->|No Posts| F[Return: No posts message]
    E -->|Error| G[Return Empty Result]
    E -->|Success| H{Level 3: summarize_posts}
    H -->|Error| I[Return Fallback Summary]
    H -->|Success| J{Level 4: format_markdown}
    J -->|Error| K[Return Error Markdown]
    J -->|Success| L{Level 5: combine_sections}
    L -->|Error| M[Return Empty Combined]
    L -->|Success| N{Level 6: convert_to_pdf}
    N -->|Error| O[Fallback to Text Digest]
    N -->|Success| P[Cache and Return PDF]
```

**Error Handling Principles:**
1. **Graceful Degradation**: Never fail completely, always provide fallback
2. **Logging**: All errors logged with context
3. **User-Friendly Messages**: Clear error messages for users
4. **Continue Processing**: Errors in one channel don't stop others

## Component Interactions

### Post Repository

```mermaid
graph LR
    A[PostFetcherWorker] --> B[PostRepository]
    C[MCP Tools] --> B
    B --> D[MongoDB]
    B --> E[Deduplication Logic]
    E --> F[message_id Check]
    E --> G[content_hash Check]
```

### MCP Tools Integration

```mermaid
graph TD
    A[Bot Handler] --> B[MCP Client]
    B --> C[get_posts_from_db]
    B --> D[summarize_posts]
    B --> E[format_digest_markdown]
    B --> F[combine_markdown_sections]
    B --> G[convert_markdown_to_pdf]
    
    C --> H[PostRepository]
    D --> I[LLM Summarizer]
    E --> J[Markdown Formatter]
    F --> K[Template Engine]
    G --> L[weasyprint]
```

## Configuration

### Settings Hierarchy

```mermaid
graph TD
    A[Environment Variables] --> B[Settings Class]
    B --> C[Post Fetcher Settings]
    B --> D[PDF Digest Settings]
    
    C --> E[post_fetch_interval_hours: 1]
    C --> F[post_ttl_days: 7]
    
    D --> G[pdf_cache_ttl_hours: 1]
    D --> H[pdf_summary_sentences: 5]
    D --> I[pdf_summary_max_chars: 3000]
    D --> J[pdf_max_posts_per_channel: 100]
    D --> K[digest_max_channels: 10]
```

## Performance Considerations

### Optimization Strategies

1. **Caching**: PDFs cached for 1 hour to reduce regeneration
2. **Indexes**: MongoDB indexes for fast queries
3. **Limits**: Post and channel limits prevent token overflow
4. **Async Processing**: All operations are async for better concurrency
5. **Deduplication**: Hybrid deduplication prevents duplicate processing

### Resource Usage

- **Memory**: In-memory cache for PDFs (configurable size)
- **Database**: MongoDB with TTL indexes for automatic cleanup
- **CPU**: PDF generation uses weasyprint (moderate CPU usage)
- **Storage**: Posts stored for 7 days, then auto-deleted

## Monitoring and Metrics

### Key Metrics (Future Implementation)

- `post_fetcher_posts_saved_total` (Counter)
- `post_fetcher_channels_processed_total` (Counter)
- `post_fetcher_errors_total` (Counter)
- `post_fetcher_duration_seconds` (Histogram)
- `pdf_generation_duration_seconds` (Histogram)
- `pdf_generation_errors_total` (Counter)
- `pdf_file_size_bytes` (Histogram)
- `bot_digest_requests_total` (Counter)
- `bot_digest_cache_hits_total` (Counter)
- `bot_digest_errors_total` (Counter)

## Security Considerations

1. **User Isolation**: Each user only sees their own posts
2. **Input Validation**: All inputs validated before processing
3. **Error Sanitization**: Error messages don't expose internal details
4. **Cache Keys**: User-specific cache keys prevent cross-user access

## Future Improvements

1. **Redis Cache**: Replace in-memory cache with Redis for multi-instance deployment
2. **PDF Templates**: Support for custom PDF templates
3. **Batch Processing**: Optimize for bulk PDF generation
4. **Metrics**: Prometheus metrics integration (Phase 8)
5. **Health Checks**: Worker health check endpoints (Phase 8)

## Related Documentation

- [API Documentation](api.md) - MCP tools API reference
- [User Guide](USER_GUIDE.md) - User-facing documentation
- [Phase Summary](../tasks/day_12/day_12-phase-06-summary.md) - Implementation summary


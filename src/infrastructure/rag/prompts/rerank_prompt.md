# Task
You are a relevance scorer. Given a query and candidate text chunks, score each chunk's relevance on a scale from 0.0 to 1.0. Prefer chunks with concrete, query-specific information.

# Input
Query: {query}

Chunks:
{chunks}

# Evaluation Criteria
- Does the chunk directly answer the query?
- Does it provide specific technical details relevant to the query?
- Does it avoid generic or unrelated content?

# Output Format (JSON only)
{{"scores": {{"chunk_id": float}}, "reasoning": "brief explanation of the ranking"}}

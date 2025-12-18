# Requirements Analysis Extraction Prompt

## Role
You are a Requirements Engineer AI.

## Task
Analyze the provided SRS context and extract the high-level domain structure required for an MVC application.

## Goal
Extract ALL fundamental domain entities (Model layer) and ALL high-level system functionalities/workflows (Controller layer).

## Clarification Phase
If the SRS context is ambiguous regarding:
- **Entity definitions**: Ask for clarification on what data needs to be stored
- **System boundaries**: Ask which features are in-scope vs out-of-scope
- **User roles**: Ask if there are different user types with different permissions

If the context is clear, proceed with extraction.

## Very Important Rules
- The output MUST strictly adhere to the provided JSON Schema
- Entities should focus on *data* that needs to be stored or managed (e.g., User, Product)
- System Functions should focus on *actions* the system performs (e.g., registerUser, updateStock)
- DO NOT invent entities or functions
- Extract ONLY what is clearly mentioned or implied in the context

## Strict JSON Format
**NO COMMENTS, NO EXTRA TEXT, NO CODE FENCES**

```json
{
  "project_name": "Short, single-word project identifier (e.g., ECommerce)",
  "domain_entities": [
    {
      "name": "Core Entity Name (e.g., User, Product, Order)",
      "purpose": "The primary role of the entity and data it represents (1 sentence)"
    }
  ],
  "system_functions": [
    {
      "name": "High-Level Function Name (e.g., placeOrder, loginUser)",
      "description": "The high-level business workflow performed by this function (1 sentence)"
    }
  ]
}
```

## Variables
- `{{context}}`: Retrieved SRS chunks formatted as:
  ```
  --- SRS Chunk 1 ---
  [content]
  
  --- SRS Chunk 2 ---
  [content]
  ```

## SRS Context
{{context}}

## Output
Return ONLY the JSON. No explanation, no introduction.


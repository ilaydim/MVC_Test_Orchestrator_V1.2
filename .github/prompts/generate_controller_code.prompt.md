# Controller Code Generation Prompt

## Role
You are an expert Python developer.

## Task
Complete the Controller class skeleton based on the SRS requirements.

## Clarification Phase
If business logic is unclear from SRS:
- **Use Architecture Information**: The architecture information ({{arch_info}}) contains essential details about this controller, including actions and responsibilities
- **Use Related Models/Views**: The related models ({{related_models}}) and views ({{related_views}}) provide context for interactions
- **Infer from context**: Use the class name, description, and action names to infer business logic
- **Create reasonable defaults**: If specific details are missing, create a standard implementation based on common MVC patterns

**IMPORTANT**: Do NOT ask for clarification or complain about missing SRS details. Instead, use the available information (architecture, actions, related models/views) to generate a complete, functional controller implementation.

## Implementation Requirements

Fill in the `{{class_name}}` class with:

1. **Action methods**: Implement all action methods from the skeleton with full business logic
2. **Request handling**: Add request validation and parameter extraction
3. **Business logic**: Implement the core business logic for each action based on SRS
4. **Model integration**: Use model classes to interact with data
5. **View integration**: Return appropriate responses/views
6. **Error handling**: Add try-except blocks and proper error responses
7. **Validation**: Add input validation for all methods

## Architecture Information
{{arch_info}}

## Related Models (for reference)
{{related_models}}

## Related Views (for reference)
{{related_views}}

## Relevant SRS Content
{{srs_context}}

## Current Skeleton
```python
{{skeleton}}
```

## Code Requirements
- Return ONLY valid Python code, no explanations
- Keep the class name exactly as: `{{class_name}}`
- Implement ALL methods from the skeleton
- Add comprehensive docstrings explaining what each method does
- Use proper Python conventions (PEP 8)
- Include type hints
- Add error handling
- Make the code production-ready and complete

## Output
Return the complete, final Python code.


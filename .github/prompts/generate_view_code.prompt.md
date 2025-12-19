# View Code Generation Prompt

## Role
You are an expert Python developer.

## Task
Complete the View class skeleton based on the SRS requirements.

## Clarification Phase
If UI details are missing from SRS:
- **Use Architecture Information**: The architecture information ({{arch_info}}) contains essential details about this view
- **Infer from context**: Use the class name, description, and related models/controllers to infer UI requirements
- **Create reasonable defaults**: If specific details are missing, create a standard implementation based on the view type (list, detail, form, etc.)

**IMPORTANT**: Do NOT ask for clarification or complain about missing SRS details. Instead, use the available information (architecture, class name, related components) to generate a complete, functional view implementation.

## Implementation Requirements

Fill in the `{{class_name}}` class with:

1. **Render method**: Implement the main rendering logic
2. **UI components**: Add methods for rendering different UI elements (forms, lists, details, etc.)
3. **Data binding**: Add methods to bind data to UI elements
4. **Event handlers**: Add placeholder methods for user interactions
5. **Template/HTML structure**: If web-based, include structure for the view

## Architecture Information
{{arch_info}}

## Relevant SRS Content
{{srs_context}}

## Current Skeleton
```python
{{skeleton}}
```

## Code Requirements
- Return ONLY valid Python code, no explanations
- Keep the class name exactly as: `{{class_name}}`
- Framework-agnostic (can be adapted to Flask, Django, React, etc.)
- Include comprehensive docstrings
- Use proper Python conventions (PEP 8)
- Make the code production-ready and complete

## Output
Return the complete, final Python code.


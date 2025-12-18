# Model Code Generation Prompt

## Role
You are an expert Python developer.

## Task
Complete the Model class skeleton based on the SRS requirements.

## Clarification Phase
If information is missing:
- **Attributes**: Ask which fields/properties this entity should have
- **Data types**: Ask about the type of each attribute (string, int, date, etc.)
- **Validation rules**: Ask about required fields, constraints, formats
- **Relationships**: Ask how this model relates to other models

If the skeleton and context provide enough information, proceed with code generation.

## Implementation Requirements (KEEP IT SIMPLE!)

Fill in the `{{class_name}}` class with **MINIMAL** code:

1. **Attributes**: 3-7 key fields only (id always included)
2. **__init__ method**: Simple initialization
3. **1-2 helper methods max**: Only if absolutely necessary
4. **NO complex logic**: This is a learning project
5. **Type hints**: Basic types only (str, int, bool, Optional)

## Architecture Information
{{arch_info}}

## Relevant SRS Content
{{srs_context}}

## Current Skeleton
```python
{{skeleton}}
```

## Code Requirements (SIMPLE & CLEAN!)
- Return ONLY valid Python code
- Keep class name exactly: `{{class_name}}`
- Simple docstring (1-2 lines)
- Basic Python conventions
- 20-40 lines of code max
- NO complex logic or validation
- Focus on clarity over completeness

## Output
Return the complete, final Python code.


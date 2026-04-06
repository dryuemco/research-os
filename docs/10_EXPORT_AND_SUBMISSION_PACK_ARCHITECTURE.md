# 10 - Export and Submission-Pack Architecture

## Scope
- export package lifecycle with explicit transitions
- renderer abstraction and markdown renderer implementation
- persisted export artifacts with checksums
- submission-pack assembler endpoint
- operator-focused UI detail views and approval action surface

## Key rules
- no external submission side effects
- approval gate required before `approved` export status
- every persisted transition emits audit events
- renderer logic remains modular and swappable

## Artifacts (current)
- proposal narrative markdown
- reviewer log markdown
- reusable evidence summary markdown
- decomposition summary markdown
- export manifest markdown

## Next extension points
- DOCX renderer adapter
- PDF renderer adapter
- template-specific render policies
- artifact storage backends (filesystem/object storage)

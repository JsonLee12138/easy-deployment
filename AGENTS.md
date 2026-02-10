<!-- OPENSPEC:START -->
# OpenSpec Instructions

These instructions are for AI assistants working in this project.

Always open `@/openspec/AGENTS.md` when the request:
- Mentions planning or proposals (words like proposal, spec, change, plan)
- Introduces new capabilities, breaking changes, architecture shifts, or big performance/security work
- Sounds ambiguous and you need the authoritative spec before coding

Use `@/openspec/AGENTS.md` to learn:
- How to create and apply change proposals
- Spec format and conventions
- Project structure and guidelines

Keep this managed block so 'openspec update' can refresh the instructions.

<!-- OPENSPEC:END -->

<!-- GHREPO:START -->
# ghrepo

This project is configured to work with the GitHub repository: JsonLee12138/rag

## Commands

```bash
# List directory contents
ghrepo ls JsonLee12138/rag .

# Read file content
ghrepo cat JsonLee12138/rag <path>

# Show file metadata
ghrepo stat JsonLee12138/rag <path>

# Download files
ghrepo get JsonLee12138/rag <path> --out <local-path>

# Create or update a file
ghrepo put JsonLee12138/rag <path> -m "message" --file <local-file>

# Delete a file
ghrepo rm JsonLee12138/rag <path> -m "message"
```
<!-- GHREPO:END -->

<!-- DEPLOYMENT:START -->
# Deployment Skills Tips

- Run `deployment-config-validate` only for config-dependent stages such as `remote-deploy` or compose push.
- Use `deployment-config-create` to patch `Makefile` first and maintain `.deploy.env.<ENV_MODE>` files for environment data.
- Use `deployment-execute` with `--dry-run` before real deploy in sensitive environments.
- Run `deployment-post-checks` and `deployment-observability-smoke` after deploy to gate rollback decisions.
- Use `makefile-contract-lint` and `compose-security-lint` before release to catch contract and safety issues early.
- Archive deployment evidence with `deployment-record-archive` for audit and rollback traceability.
<!-- DEPLOYMENT:END -->

## Task linkage
- TASK ID: TASK-XXXX
- Closes: #<issue>
- FR/NFR refs: FR-xxx, NFR-xxx

## Scope
- What was changed:
- What was not changed:

## Verification evidence
- [ ] `python -m py_compile <changed_python_files>`
- [ ] `odoo-bin -d test_db -i <module_name> --stop-after-init`
- [ ] `odoo-bin -d test_db --test-tags /<module_name>`
- [ ] `ruff check <module_path>`
- [ ] `pre-commit run --all-files`

## Notes for reviewers
- Risks:
- Follow-ups:

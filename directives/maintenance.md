# Maintenance & Development

## Code Principles (Layer 3)
- **Deterministic**: Scripts should do one thing predictably.
- **Stateless**: Scripts should rely on inputs/files, not internal memory between runs.
- **Logged**: Always log important actions to stdout or log files.

## Common Tasks

### 1. Update Strategy
Modify `execution/trading_system/config/trading_rules.json`.
- Adjust `stop_loss_pct`, `target_pct`, or scanning parameters.
- No restart required for `market_scanner.py` (it reloads config).
- `trading_orchestrator.py` may need a restart.

### 2. Update Dependencies
```bash
pip install -r execution/trading_system/requirements.txt
# OR
pip install <package_name>
```

### 3. Add New Feature
1. **Check `directives/`**: Is there an SOP for this?
2. **Check `execution/`**: Is there a script that already does this?
3. **Draft Plan**: Create a new script in `execution/trading_system/scripts/` if needed.
4. **Update Directive**: If the workflow changes, update the relevant markdown file.

### 4. Integrated Skills
- **Excel Recalculation**: Use `execution/utils/xlsx/recalc.py` to fix formula errors in reports.
- See `directives/using_skills.md` for more details.

### 5. Debugging
- Backend Logs: Check the terminal where `dashboard_api.py` is running.
- Live Sync Logs: Check the terminal where `live_sync.py` is running.
- System Logs: Check `execution/trading_system/journals/`.

## Git Workflow
1. Make changes.
2. `git add .`
3. `git commit -m "Description"`
4. `git push`

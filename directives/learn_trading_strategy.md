# Learn Trading Strategy from Web

## Goal
Research a trading concept or strategy from the web and codify it into the system.

## Process
1.  **Search**: Use `search_web` to find authoritative sources (blogs, documentation, forums) on the requested strategy (e.g., "ICT Silver Bullet", "Wyckoff Schematic", "VWAP Reversion").
2.  **Extract Rules**:
    - **Conditions**: What must happen for a valid setup? (e.g., "Price crosses above VWAP")
    - **Entry**: When exactly to enter? (e.g., "Candle close above high of previous candle")
    - **Stop Loss**: Where is the invalidation point?
    - **Take Profit**: What is the target?
    - **Timeframe**: What chart timeframe is best?
3.  **Document**: Create a new file in `execution/trading_system/config/strategies/` or update `trading_rules.json`.
4.  **Codify (Optional)**: If the user requests implementation, write a Python detection function in `execution/trading_system/scripts/market_scanner.py`.

## Template for Knowledge Item
When you learn a new strategy, create a markdown file `directives/knowledge/strategy_name.md`:

```markdown
# [Strategy Name]

## Concept
Brief explanation of why this works.

## Rules
- **Setup**: ...
- **Trigger**: ...
- **Stop**: ...
- **Target**: ...

## Source
- [Title](URL)
```

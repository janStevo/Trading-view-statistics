# OpenPositionsStatistics_04

## Overview
This module analyzes and visualizes trading strategy performance statistics from TradingView export files. It processes multiple strategy trade data, calculates cumulative profits, tracks open positions over time, and generates performance visualizations with drawdown analysis.

## Key Features
- **Multi-file Support**: Reads trade data from multiple Excel files in a folder
- **Trade Tracking**: Processes Entry/Exit signals for both Long and Short positions
- **Profit Calculation**: Computes cumulative profits with optional trading fees
- **Position Monitoring**: Tracks the number of open positions throughout the trading period
- **Drawdown Analysis**: Calculates maximum drawdown and drawdown history
- **Dual Visualization**: Generates 2-subplot charts showing profit trajectory and open positions
- **Capital Management**: Supports position sizing based on available capital
- **Flexible Modes**: Normal mode and Martingale scaling mode for position sizing
- **Position Limits**: Optional maximum open positions constraint

## Data Format

### Expected Excel Structure
Files should be exported from TradingView with the following columns:
- **Trade#** (Column 0): Trade identifier
- **Type** (Column 1): Entry Long, Exit Long, Entry Short, Exit Short
- **Signal** (Column 2): Signal type (not "Open")
- **Date/Time** (Column 3): Trade execution timestamp
- **Price USDT** (Column 4): Entry/exit price
- **Contracts** (Column 5): Position size
- **Profit USDT** (Column 6): Trade profit/loss
- **Profit %** (Column 7): Profit percentage
- **Cum. Profit USDT** (Column 8): Cumulative profit
- **Cum. Profit %** (Column 9): Cumulative profit percentage
- **Run-up USDT** (Column 10): Maximum favorable excursion
- **Run-up %** (Column 11): Run-up percentage
- **Drawdown USDT** (Column 12): Adverse movement
- **Drawdown %** (Column 13): Adverse movement percentage
- **fileId** (Column 14): Added automatically during processing

## Classes and Methods

### CONST Class
Static constants defining trade types and file paths:
- `ENTRY_LONG`: "Entry long"
- `EXIT_LONG`: "Exit long"
- `ENTRY_SHORT`: "Entry short"
- `EXIT_SHORT`: "Exit short"
- `FOLDER_PATH`: Default folder path for trade data
- `FEE`: Transaction fee multiplier (default: 0)

### PARAM Class
Static parameters for strategy analysis:
- `STRAT_VAL`: Investment per strategy (default: 1000)
- `INVESTMENT`: Total investment (number of strategies × STRAT_VAL)
- `ALL_POSITIONS`: Total number of strategies/files processed
- `FOLDERS`: Dictionary mapping folder paths to per-strategy investment amounts

### Statistics Class

#### `mainLoop()`
Main execution method:
- Iterates through all folders in `PARAM.FOLDERS`
- Processes each folder's trade data
- Generates performance charts for each folder
- Displays all charts in separate windows

#### `getChartData(iMaxPos=None, iMartiangle=False, iFolder=CONST.FOLDER_PATH)`
Core analysis method processing trade data and calculating metrics.

**Parameters:**
- `iMaxPos` (int, optional): Maximum allowed concurrent positions
  - If `None`: No position limit
  - If specified: Disables excess positions if limit exceeded
- `iMartingale` (bool): Enable Martingale-style position sizing
  - `True`: Dynamic sizing based on current capital
  - `False`: Static sizing based on trade data (default)
- `iFolder` (Path): Source folder containing Excel trade files

**Position Sizing Logic (Martingale Mode):**
- Strategy 13: 2/3 of normalized capital
- Strategies 7, 8, 9, 17, 18, 19: 1/3 of normalized capital
- Other strategies: 1/2 of normalized capital
- Adjusted by position constraint: `(2 - iMaxPos/PARAM.ALL_POSITIONS)`

**Returns:**
- `lProfits` (list): Profit/loss at each timestamp
- `lPositions` (list): Number of open positions at each timestamp

#### `calcDrawdowns(iProfits)`
Calculates drawdown metrics from profit series.

**Parameters:**
- `iProfits` (list): Cumulative profit values

**Returns:**
- `lDrawdowns` (list): Drawdown at each point
- `lMaxDrawdown` (float): Maximum drawdown encountered

#### `getPlotChart(iData, iMaxPos=None, iInvestment=None)`
Generates 2-subplot performance visualization.

**Parameters:**
- `iData` (list): [profits_list, positions_list]
- `iMaxPos` (int, optional): Maximum positions for chart title
- `iInvestment` (float, optional): Custom investment amount (uses PARAM.INVESTMENT if None)

**Output Chart:**
- **Subplot 1 (Top)**: 
  - Line plot: Cumulative portfolio value over time
  - Orange bars: Drawdown at each trade
  - Title shows: Total Profit, Max Drawdown, Return/Drawdown Ratio
  
- **Subplot 2 (Bottom)**:
  - Bar chart: Number of open positions per trade
  - Shows position management over time

**Returns:**
- `fig` (matplotlib.figure.Figure): Figure object for display

## Data Processing Pipeline

1. **File Reading**: Reads all `.xlsx` files from specified folder
2. **Data Validation**: 
   - Converts Price column from string (with commas) to float
   - Ensures Date/Time is datetime format
   - Filters out "Open" signals and NaN contracts
3. **Trade Sorting**: Orders trades by Date/Time and trade type priority
4. **Trade Sequencing**: Processes Entry/Exit pairs in chronological order
5. **Profit Aggregation**: Accumulates P&L by timestamp
6. **Position Tracking**: Counts open positions at each timestamp
7. **Visualization**: Generates performance charts

## Configuration Example

```python
from OpenPositionsStatistics_04 import Statistics, PARAM

# Configure strategies and investments
PARAM.FOLDERS = {
    Path("test_sharing_capital"): 1000,      # 1 strategy with $1,000
    Path("other_strategies"): 500            # Another strategy with $500
}

# Run analysis
main = Statistics()
main.mainLoop()
```

## Usage Example

```python
from pathlib import Path
from OpenPositionsStatistics_04 import Statistics, PARAM

# Setup parameters
PARAM.FOLDERS = {
    Path("trades_data02"): 1000
}

# Create analyzer
stats = Statistics()

# Get chart data for specific folder
profits, positions = stats.getChartData(
    iFolder=Path("trades_data02"),
    iMaxPos=5,              # Max 5 concurrent positions
    iMartingale=False       # Standard position sizing
)

# Generate visualization
fig = stats.getPlotChart(
    iData=[profits, positions],
    iMaxPos=5
)

# Display
import matplotlib.pyplot as plt
plt.show(block=True)
```

## Output Metrics

### Profit Metrics
- **Total Profit**: Final portfolio value minus initial investment
- **Cumulative Profit**: Running total of P&L across all trades
- **Trade P&L**: Profit/loss for each individual trade (including fees)

### Risk Metrics
- **Maximum Drawdown**: Largest peak-to-trough decline
- **Drawdown History**: Drawdown at each trade execution
- **Return/Drawdown Ratio**: Performance efficiency metric

### Position Metrics
- **Open Positions**: Current number of active trades
- **Max Positions**: Peak concurrent positions
- **Position Timeline**: How position count evolves

## Data Processing Notes

- **Fee Handling**: Trading fees applied only if `CONST.FEE > 0`
- **Date Conversion**: Handles both `date` and `datetime` formats
- **Capital Allocation**: Divided equally across all strategies
- **Disabled Positions**: When position limit exceeded, excess entries are skipped until exits occur
- **Time Bucketing**: Profits/positions grouped by timestamp (aggregated within same timestamp)

## Dependencies

```
polars              # High-performance data processing
matplotlib          # Visualization and charting
pathlib             # File path handling
datetime            # Time handling
```

## Limitations & Notes

- **Data Assumptions**: Assumes proper TradingView export format
- **No Slippage**: Doesn't model realistic slippage beyond flat fee
- **Perfect Execution**: Assumes all orders fill at specified price
- **Single Entry/Exit**: Assumes simple open/close pairs (no scaling in/out)
- **Capital Model**: Static capital allocation (except in Martingale mode)
- **Fee Implementation**: Simple flat fee on notional value

## Common Issues & Solutions

### Issue: FileNotFoundError
**Solution**: Ensure folder path in `PARAM.FOLDERS` exists and contains `.xlsx` files

### Issue: Column Not Found
**Solution**: Verify TradingView export includes all expected columns; update column indices if format differs

### Issue: Missing "Price" Column
**Solution**: Script automatically renames "Price" to "Price USDT" if needed

## Future Enhancements (TODOs in Code)

- Implement Monte Carlo analysis for trade order randomization
- Add date-based plotting mode
- Support configurable position sizing rules
- Add statistical measures (Sharpe ratio, Sortino ratio)
- Support partial fills and scaling in/out of positions

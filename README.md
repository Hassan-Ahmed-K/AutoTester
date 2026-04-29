# AutoTester (AI Agent Finder)

AutoTester is a comprehensive PyQt5-based desktop application designed for MetaTrader 5 (MT5) algorithmic traders and developers. It provides a robust suite of tools to automate backtesting, optimize Expert Advisors (EAs), manage `.set` files, analyze HTML strategy reports, and build uncorrelated, high-performing trading portfolios.

## Features

- **Auto Batch**: Automate the batch testing and optimization of MT5 Expert Advisors, saving significant time during the strategy discovery phase.
- **Set Finder & Generator**: Discover, parse, and dynamically generate `.set` parameter files for MT5 EAs to streamline optimization and testing workflows.
- **Set Processor**: Batch process and validate large volumes of `.set` files efficiently.
- **Html Hunter**: automatically parse and extract key metrics (Profit Factor, Drawdown, Trades, etc.) from MT5 HTML Strategy Tester reports into manageable, sortable data structures.
- **Set Compare**: Perform side-by-side comparisons of different strategy parameter sets to identify the most robust configurations.
- **Portfolio Picker**: Filter and select the best combinations of strategies or symbols, incorporating correlation analysis to build diversified, high-performing portfolios.
- **Authentication**: Built-in environment-based caching and keyring authentication.

## Prerequisites

Before running the application, ensure you have the following installed:

- **Python 3.8+**
- **MetaTrader 5** terminal installed and logged into an account.
- **Windows OS** (Recommended due to MT5 and PyWin32 dependencies)

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/AutoTester.git
   cd AutoTester
   ```

2. **Set up a virtual environment (optional but recommended):**
   ```bash
   python -m venv venv
   source venv/Scripts/activate  # On Windows PowerShell
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Variables:**
   Create a `.env` file in the root directory (or use the provided `.env`) and configure the required variables for authentication:
   ```env
   SERVICE_NAME=YourServiceName
   CACHE_KEY=YourCacheKey
   ```

## Usage

Start the application by running the main entry point:

```bash
python main.py
```

### Application Navigation

- **Home**: Dashboard overview of the toolset.
- **Auto Batch**: Select your MT5 directory, Data folder, and Report folder to queue and run batch optimizations.
- **Set Generator / Processor**: Load strategy optimization files to analyze estimated profits, build variations, and process them directly into MetaTrader.
- **Html Hunter / Extract Tables**: Utilize the standalone `extract_tables.py` script or the built-in UI to scrape MT5 HTML reports into CSVs for further data science and analysis.

## Project Structure

- `main.py`: The entry point for the PyQt5 application.
- `extract_tables.py`: Standalone beautifulsoup4 script for extracting MT5 HTML report tables into CSV files.
- `aiagentfinder/`: Core application module.
  - `controllers/`: Handles the business logic for each UI page (e.g., `AutoBatch.py`, `SetGenerator.py`, `HtmlHunter.py`).
  - `ui/`: Contains the PyQt5 UI layout configurations and base components.
  - `utils/`: Utilities for MT5 bridging (`mt5_manager.py`), threading (`workerThread.py`), and logging.
- `requirements.txt`: Python package dependencies.
- `data/` & `Examples/`: Directories intended for sample datasets, report outputs, and configuration examples.

## Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the issues page.

## License

This project is licensed under the terms of the license included in the `LICENSE` file.
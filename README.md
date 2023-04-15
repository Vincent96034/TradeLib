# TradeLib

TradeLib is a toolkit designed to simplify the deployment of portfolio strategies. I tried to keep the code general and easily extendable, allowing for the addition of new trading/portfolio strategies, data sources, and trading backends.

## Contents

The following modules are included in the TradeLib project:

- **DataService**: The DataService module provides a service to access various data sources, including stock data, factor data from Fama and French, and any other data sources that you may want to add. This module includes a boilerplate class for respective data sources and can be easily extended to support new data sources.

- **Strategy Service**: The StrategyService module provides a framework for creating and managing trading strategies. The module includes a Strategy class with a factory function that returns a defined strategy, and multiple strategies can be added and created here. Currently, there is a default Buy-and-Hold strategy and a strategy that uses Principal Component Analysis (PCA). This module can be extended to support new trading strategies as needed.

- **TradeHandlerService**: The TradeHandlerService module includes a toolkit to create portfolios and trades from given weights, as well as boilerplate for trading backends. Currently, the backends from Lemon.Market and Alpaca are implemented, but the module can be extended to support other trading backends as well.

- **UserSettings**: The UserSettings module is used to configure all components of TradeLib in one place. This includes configuring the DataService, StrategyService, and TradeHandlerService, as well as any other settings that may be required.

- **Logger**: The Logger module sets up a logger for the entire project, making it easy to log events and errors throughout the system. The logger can be configured to write to a file or to the console, and can be customized to fit your specific logging needs.

- **Streamlit**: The Streamlit module is still under development and is intended to provide a user-friendly interface for interacting with the TradeLib toolkit. Once completed, it will allow users to visualize and access the entire service through a web-based interface.


## Installation

To install TradeLib, simply clone this repository and install the required dependencies using pip.

```bash
git clone https://github.com/Vincent96034/TradeLib.git
cd TradeLib
pip install -r requirements.txt
```

## Usage

After installing the required dependencies, you can import the modules you need and start using TradeLib in your own projects. Here's an example:

```python
print("Hello world")
```

## Contributing

Contributions to TradeLib are welcome and appreciated! If you find a bug, have a feature request, or want to contribute code, please open an issue or pull request on GitHub.

## License

TradeLib is released under the MIT License. See LICENSE file for details.

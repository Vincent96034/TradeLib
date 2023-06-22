# TradeLib

TradeLib is a toolkit designed to simplify the deployment of portfolio strategies. It is built to be easily extendable, allowing for the addition of new trading/portfolio strategies, data sources, and trading backends.

## Contents

The following modules are included in the TradeLib project:

- **DataService**: The DataService module provides a service to access various data sources, including stock data, factor data from Fama and French, and any other data sources that you may want to add. This module includes a boilerplate class for respective data sources and can be easily extended to support new data sources.

- **Strategy Service**: The StrategyService module provides a framework for creating and managing trading strategies. The module includes a Strategy class with a factory function that returns a defined strategy, and multiple strategies can be added and created here. Currently, there is a default Buy-and-Hold strategy and a strategy that uses Principal Component Analysis (PCA). This module can be extended to support new trading strategies as needed.

- **TradeHandlerService**: The TradeHandlerService module is the **heart of this project**. It houses the boilerplate and two implementations of trading backends (1 deprected), which are used for all stock orders. Additionally, the data-model is defined here, which was desined to also used as a database to store trades, stock-positions or even stock price time-series. Lastly (currently still under constuction) it includes a implementation of a portfolio class, that is going to serve as a front-end for the application.

- **UserSettings**: The UserSettings module is used to configure all components of TradeLib in one place. This includes configuring the DataService, StrategyService, and TradeHandlerService, as well as any other settings that may be required.

- **Logger**: The Logger module sets up a logger for the entire project, making it easy to log events and errors throughout the system. The logger can be configured to write to a file or to the console, and can be customized to fit your specific logging needs.


## Installation

To install TradeLib, simply clone this repository and install the required dependencies using pip.

```bash
git clone https://github.com/Vincent96034/TradeLib.git
cd TradeLib
pip install -r requirements.txt
```

## Usage

After installing the required dependencies, you can import the modules you need and start using TradeLib in your own projects. You need an account for one of the implemented trading backends (e.g. alpaca.markets). Here's an example:

```python
# import modules
from UserSettings.configuration import RunConfiguration
from StrategyService.Strategies.pca_strategy import PCA_Strategy
from TradeHandlerService.TradingBackends.alpaca_class import Alpaca
from TradeHandlerService.portfolio import Portfolio
from TradeHandlerService.trade_translator import TradeHandler
from Logger.config_logger import setup_logger


logger = setup_logger(__name__)

# setup the pipeline using the usersettings.json file
settings_source = "usersettings.json"
config = RunConfiguration(settings_source)

# Setup a trading backend. In this case alpaca.markets was used.
# The API keys can be provided via usersettings.json or in an environment file
# Note: all settings are configured with the usersettings.json
alpaca = Alpaca(config.alpaca_secret,
                config.alpaca_key,
                config.alpaca_paper)

# Create the Porfolio object, to operate the trades
portfolio = Portfolio(trading_backend=alpaca)
portfolio.initialize()

# Specify the desired porfolio strategy and run it. This outputs ticker 
# symbols with weights.
strategy = PCA_Strategy(
    ratio=0.12,
    company_pool="NASDAQ100",
    portfolio_type="tail",
    factor_estimate_cov=True
)
strategy.run_strategy()
logger.info("Strategy calculated.")

# The above calculated weights are then translated into actual trade
# instructions to restructure the current portfolio
trade_handler = TradeHandler()
trade_handler.create_rebalance_frame(
    portfolio_dict=portfolio.get_portfolio_weights(),
    portfolio_value=portfolio.total_value,
    w_new=strategy.weights,
    add_value=0
)

trade_handler.create_trade_instructions()
logger.info("Trade instruction calculated.")
logger.info(trade_handler.trade_instructions)

# In the last step, the orders are placed via the trade backend (in this case
# alpaca.markets)
logger.info("Placing orders ...")
alpaca.place_multi_order(trade_handler.trade_instructions)

# A loop could be added to recalculate and restructure the portfolio for
# example every month or every week.
```

## Contributing

Contributions to TradeLib are welcome and appreciated! If you find a bug, have a feature request, or want to contribute code, please open an issue or pull request on GitHub.

## License

TradeLib is released under the MIT License. See LICENSE file for details.

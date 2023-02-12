from StrategyService.Strategies.PCA_Strategy import PCA_Strategy
from StrategyService.Strategies.Hold_Strategy import Hold_Strategy



def strategy_factory(method: str):
    '''
    A factory function that returns an instance of a strategy class, specified by the `method` argument.

    Parameters:
    method (str): The name of the strategy to be returned. 
                  Accepted values are "pca" and "hold".

    Returns:
    class: An instance of the specified strategy class, or None if the `method` is not recognized.

    Example:
    >>> strategy = strategy_factory("pca")
    >>> print(strategy)
    <class '__main__.PCA_Strategy'>
    >>> strategy = strategy_factory("unknown")
    >>> print(strategy)
    None
    '''

    strategy_dict = {
        "pca": PCA_Strategy,
        "hold": Hold_Strategy,
    }

    return strategy_dict.get(method, Hold_Strategy)
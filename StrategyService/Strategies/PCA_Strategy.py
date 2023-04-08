import numpy as np

from Logger.config_logger import setup_logger
logger = setup_logger(__name__)


class PCA_Strategy:

    def __init__(self):
        self.loadings = []
        self.weights = {}
        self.sign_ratio = None


    def strategy_run(self):
        ''' Generic function for every strategy class: runs strategy '''
        print("... run pca strategy")
        pass

    # TODO: implement everything after this:

    def create_portfolio(loadings, col_names, start=0, stop=20):
        '''
        Function creates portfolio based on loadings of PC1.

        Args:
            loadings (list): list of loadings
            col_names (list): column names of loadings 
            start (int): list slicing start value
            stop (int): list slicing stop value

        Returns (dict):
            pf_weights (list): weights of companies (sorted large to small)
            pf_symbols (list): company tickers (sorted by weights)
            pf_loadings (list): loadings of companies (sorted large to small)
            pf_dict (list): list of tuples (weight, ticker)
            hedge_portfolio (list): list of tuples of hedging portfolio (weight, ticker, loading)
        '''
        
        # used to be able to construct a portfolio after components initial sorting is lost
        loadings_dict = {i[0]: i[1] for i in zip(loadings, col_names)}
        
        # detect signs
        sign_ratio = (len(loadings) - sum(np.sign(loadings) > 0))/len(loadings)

        if sign_ratio > 0.5:
            hedge_loadings = loadings[np.where(loadings >= 0)]
            loadings = loadings[np.where(loadings < 0)]
        else:
            hedge_loadings = loadings[np.where(loadings < 0)]
            loadings = loadings[np.where(loadings >= 0)]

        if abs(sign_ratio - 0.5) < 0.2:
            print("!! WARNING - no clear majority sign in PC1")

        # systematic portfolio
        loadings_sorted = sorted(loadings, key=abs, reverse=True)
        pf_loadings = loadings_sorted[start:stop]
        pf_weights = [abs(i) / sum(list(map(abs, pf_loadings))) for i in pf_loadings]
        pf_comps = [loadings_dict[i] for i in pf_loadings]

        # hedge portfolio
        hedge_sorted = sorted(hedge_loadings, key=abs, reverse=True)
        hedge_weights = [abs(i) / sum(list(map(abs, hedge_sorted))) for i in hedge_sorted]
        hedge_comps = [loadings_dict[i] for i in hedge_sorted]

        return {
            "pf_weights": pf_weights,
            "pf_symbols": pf_comps,
            "pf_loadings": pf_loadings,
            "pf_dict": [i for i in zip(pf_weights, pf_comps)], 
            "hedge_portfolio": [i for i in zip(hedge_weights, hedge_comps)]
        }

    @staticmethod
    def factor_estimate_cov(X, F, K):
        """ Estimates the covariance matrix based on the Farma & French Factor Model.

        Args:
            X (np.array): Array of N stock returns of shape (T,N)
            F (np.array): Array of K factors of shape (T,K)
            K (int): Number of factors used

        Returns:
            Covariance Matrix of shape (N,N)

        Sources:
            https://palomar.home.ece.ust.hk/MAFS6010R_lectures/Rsession_factor_models.html
            https://docs.mosek.com/portfolio-cookbook/factormodels.html
        """
        N = X.shape[1] # number of stocks
        T = X.shape[0] # Time
        # Fama French data with intercept
        F_ = np.insert(F, 0, np.ones(T), axis=1)   # (T, K+1)
        # Estimated parameters per company
        Gamma = X.T @ F_ @ np.linalg.inv(F_.T @ F_)   # (N, K+1)
        # Estimated Parameters
        # Alpha = Gamma[:,0]    # (N,)
        Betas = Gamma[:,1:]   # (N, K)
        # Residuals
        E = (X.T - Gamma @ F_.T).T
        # Degrees of freedom (4 estimated parameters)
        free = K+1
        # Covariance matrix of Residuals
        Psi = (1/(T-free)) * E.T @ E    # (N,N)
        # Covariance matrix of data
        Sigma = Betas @ np.cov(F.T) @ Betas.T + np.diag(np.diag(Psi))   # (N, N)

        return Sigma

        

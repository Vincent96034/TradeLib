import logging
logger = logging.getLogger(__name__)


class PCA_Strategy:

    def __init__(self):
        self.loadings = []
        self.weights = {}
        self.sign_ratio = None

    def strategy_run(self):
        ''' Generic function for every strategy class: runs strategy '''
        print("... run pca strategy")
        pass

    def factor_estimate_cov(self):
        pass

    

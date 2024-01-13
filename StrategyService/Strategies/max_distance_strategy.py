from datetime import datetime as dt
from typing import Union
import numpy as np
import pandas as pd
from dateutil.relativedelta import relativedelta
import statsmodels.api as sm
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn_pandas import DataFrameMapper

from StrategyService.strategy_class import Strategy
from DataService.DataServices.y_finance import YFinance
from DataService.DataServices.fama_french import FamaFrench
from Logger.config_logger import setup_logger
logger = setup_logger(__name__)


class MaxDistance_Strategy(Strategy):
    """Class for implementing a PCA-based trading strategy that selects a
    subset of companies in a given company pool to form a portfolio based on
    their sensitivity to the first principal component of their returns.

    Args:
    company_pool (Union[str, list]): The pool of companies from which to
        select a portfolio. Can be either 'S&P500', 'NASDAQ100' or a list
        of company tickers. Default is 'S&P500'.
    data_service: Object for accessing stock data. Default is YFinance.
    famafrench_data: Object for accessing Fama-French data. Default is
        FamaFrench.

    Attributes:
    name (str): Name of the trading strategy.
    _valid_inputs (dict): Dictionary containing valid inputs for the
        company_pool and portfolio_type arguments.
    company_pool (Union[str, list]): The pool of companies from which to
        select a portfolio.
    data_service: Object for accessing stock data.
    famafrench_data: Object for accessing Fama-French data.
    weights (dict): The weights assigned to each company in the portfolio.
    _df_returns (pd.DataFrame): The returns data of the selected companies.
    _df_factors (pd.DataFrame): The Fama-French factors data.

    Methods:
    _get_returns_data: Downloads and returns historical stock returns data
        of companies in the company_pool.
    _get_factor_data: Downloads and returns Fama-French factors data.
    run_strategy: 
    """

    def __init__(self,
                 company_pool: Union[str, list] = "S&P500",
                 data_service=YFinance(),
                 famafrench_data=FamaFrench()) -> None:
        super().__init__()
        self.name = "PCA-Strategy"
        self._valid_inputs = {
            "company_pool": ["S&P500", "NASDAQ100", "MARKET_1663"]
        }
        self.company_pool = company_pool
        self.data_service = data_service
        self.famafrench_data = famafrench_data
        self.weights = {}
        self._df_returns = None
        self._df_factors = None

    def _get_returns_data(self,
                          start_date: str,
                          stop_date: Union[str, None] = None,
                          OHLC_spec: str = "Adj Close"
                          ) -> pd.DataFrame:
        cp = self.company_pool
        if cp == "S&P500":
            companies = self.data_service.get_constituents(cp)
        elif cp == "NASDAQ100":
            companies = self.data_service.get_constituents(cp)
        elif cp == "MARKET_1663":
            companies = ['A', 'AAL', 'AAP', 'AAPL', 'AAT', 'AB', 'ABBV', 'ABCB', 'ABEV', 'ABG',
                         'ABM', 'ABMD', 'ABR', 'ABT', 'ABUS', 'ACAD', 'ACB', 'ACCO', 'ACHC',
                         'ACIW', 'ACLS', 'ACM', 'ACRE', 'ACTG', 'ADBE', 'ADC', 'ADI', 'ADM',
                         'ADMA', 'ADP', 'ADSK', 'ADTN', 'AEE', 'AEG', 'AEHR', 'AEIS', 'AEL',
                         'AEM', 'AEO', 'AEP', 'AER', 'AES', 'AFG', 'AFL', 'AG', 'AGCO', 'AGEN',
                         'AGIO', 'AGO', 'AHH', 'AHT', 'AIG', 'AIR', 'AIT', 'AIV', 'AIZ', 'AJG',
                         'AKAM', 'AKR', 'AL', 'ALB', 'ALE', 'ALEX', 'ALGN', 'ALGT', 'ALKS',
                         'ALL', 'ALLY', 'ALNY', 'ALSN', 'ALV', 'AMAT', 'AMBC', 'AMC', 'AMCX',
                         'AMD', 'AME', 'AMED', 'AMEH', 'AMG', 'AMGN', 'AMH', 'AMKR', 'AMN',
                         'AMP', 'AMPH', 'AMRC', 'AMRK', 'AMRN', 'AMRX', 'AMSC', 'AMT', 'AMTX',
                         'AMX', 'AMZN', 'AN', 'ANDE', 'ANET', 'ANF', 'ANGO', 'ANSS', 'AON',
                         'AOS', 'AOSL', 'APA', 'APAM', 'APD', 'APEI', 'APH', 'APO', 'APPS',
                         'AQN', 'AR', 'ARAY', 'ARCB', 'ARCC', 'ARCO', 'ARCT', 'ARDX', 'ARE',
                         'ARES', 'ARGO', 'ARLP', 'ARMK', 'AROC', 'ARW', 'ARWR', 'ASB', 'ASGN',
                         'ASH', 'ASML', 'ASPN', 'ASX', 'ATEC', 'ATEN', 'ATGE', 'ATHM', 'ATHX',
                         'ATI', 'ATO', 'ATR', 'ATRA', 'ATRC', 'ATSG', 'AU', 'AUB', 'AUPH', 'AVA',
                         'AVAV', 'AVB', 'AVD', 'AVDL', 'AVNS', 'AVNT', 'AVT', 'AVY', 'AWI',
                         'AWK', 'AWR', 'AX', 'AXDX', 'AXGN', 'AXL', 'AXON', 'AXP', 'AXTI', 'AY',
                         'AYI', 'AZN', 'AZO', 'AZPN', 'AZZ', 'B', 'BA', 'BABA', 'BAC', 'BAH',
                         'BAK', 'BAM', 'BANC', 'BANR', 'BAX', 'BB', 'BBD', 'BBVA', 'BBW', 'BBY',
                         'BC', 'BCC', 'BCE', 'BCH', 'BCO', 'BCRX', 'BCS', 'BDC', 'BDN', 'BDX',
                         'BECN', 'BEN', 'BERY', 'BF-B', 'BFAM', 'BGFV', 'BGS', 'BHC', 'BHLB',
                         'BHP', 'BHR', 'BIDU', 'BIG', 'BIIB', 'BIO', 'BJRI', 'BK', 'BKD', 'BKE',
                         'BKH', 'BKNG', 'BKR', 'BKU', 'BLDP', 'BLDR', 'BLFS', 'BLK', 'BLKB',
                         'BLMN', 'BLNK', 'BLUE', 'BMA', 'BMO', 'BMRN', 'BMY', 'BNS', 'BOH',
                         'BOKF', 'BOOM', 'BOOT', 'BPOP', 'BR', 'BRC', 'BRFS', 'BRK-B', 'BRKL',
                         'BRKR', 'BRO', 'BRX', 'BSAC', 'BSBR', 'BSX', 'BTI', 'BUD', 'BURL',
                         'BWA', 'BWXT', 'BX', 'BXP', 'BYD', 'BZH', 'C', 'CAE', 'CAG', 'CAH',
                         'CAKE', 'CAL', 'CALM', 'CALX', 'CAMP', 'CAR', 'CARA', 'CASH', 'CASY',
                         'CAT', 'CATY', 'CB', 'CBAT', 'CBAY', 'CBD', 'CBRE', 'CBRL', 'CBSH',
                         'CBT', 'CBU', 'CBZ', 'CCI', 'CCJ', 'CCK', 'CCO', 'CCOI', 'CCRN', 'CCS',
                         'CCU', 'CDE', 'CDMO', 'CDNA', 'CDNS', 'CDW', 'CDXS', 'CE', 'CELH',
                         'CENTA', 'CENX', 'CERS', 'CF', 'CFFN', 'CFG', 'CFR', 'CG', 'CGC',
                         'CGNX', 'CHD', 'CHDN', 'CHEF', 'CHGG', 'CHH', 'CHRS', 'CHRW', 'CHS',
                         'CHT', 'CHTR', 'CI', 'CIB', 'CIEN', 'CIG', 'CINF', 'CL', 'CLAR', 'CLDX',
                         'CLF', 'CLFD', 'CLH', 'CLMT', 'CLNE', 'CLS', 'CLX', 'CM', 'CMA', 'CMC',
                         'CMCSA', 'CME', 'CMG', 'CMI', 'CMP', 'CMRE', 'CMRX', 'CMS', 'CMTL',
                         'CNA', 'CNC', 'CNHI', 'CNI', 'CNK', 'CNO', 'CNP', 'CNQ', 'CNSL', 'CNX',
                         'CODI', 'COF', 'COHU', 'COLB', 'COLM', 'COMM', 'CONN', 'COO', 'COOP',
                         'COP', 'CORT', 'COST', 'COTY', 'CP', 'CPA', 'CPB', 'CPE', 'CPG', 'CPRI',
                         'CPRT', 'CPRX', 'CPS', 'CPT', 'CR', 'CRH', 'CRI', 'CRK', 'CRL', 'CRM',
                         'CRNT', 'CROX', 'CRS', 'CRTO', 'CRUS', 'CSCO', 'CSGP', 'CSGS', 'CSIQ',
                         'CSL', 'CSTM', 'CSX', 'CTAS', 'CTLP', 'CTLT', 'CTRN', 'CTS', 'CTSH',
                         'CUBE', 'CUBI', 'CUK', 'CUTR', 'CUZ', 'CVBF', 'CVE', 'CVI', 'CVLT',
                         'CVS', 'CVX', 'CW', 'CWEN', 'CWEN-A', 'CWST', 'CWT', 'CX', 'CXW',
                         'CYBR', 'CYH', 'CYTK', 'CZR', 'D', 'DAKT', 'DAL', 'DAN', 'DAR', 'DBD',
                         'DBI', 'DCI', 'DDD', 'DDS', 'DE', 'DECK', 'DEI', 'DENN', 'DEO', 'DFS',
                         'DG', 'DGII', 'DGX', 'DHI', 'DHR', 'DHX', 'DIN', 'DIOD', 'DIS', 'DISH',
                         'DK', 'DKS', 'DLB', 'DLR', 'DLTR', 'DLX', 'DNOW', 'DOC', 'DOV', 'DOX',
                         'DPZ', 'DQ', 'DRD', 'DRI', 'DRQ', 'DRRX', 'DSX', 'DTE', 'DUK', 'DVA',
                         'DVAX', 'DVN', 'DXCM', 'DXLG', 'DY', 'E', 'EA', 'EAT', 'EBAY', 'EBIX',
                         'EBR', 'EBS', 'EC', 'ECL', 'ECPG', 'ED', 'EDU', 'EEFT', 'EFC', 'EFX',
                         'EGHT', 'EGLE', 'EGO', 'EGP', 'EGRX', 'EGY', 'EHC', 'EIGR', 'EIX', 'EL',
                         'ELP', 'ELS', 'EME', 'EMN', 'ENB', 'ENLC', 'ENPH', 'ENS', 'ENSG',
                         'ENTA', 'ENTG', 'ENV', 'ENVA', 'EOG', 'EPAC', 'EPAM', 'EPC', 'EPD',
                         'EPR', 'EQIX', 'EQNR', 'EQR', 'EQT', 'ERF', 'ERIC', 'ERII', 'ERJ', 'ES',
                         'ESI', 'ESNT', 'ESPR', 'ESRT', 'ESS', 'ET', 'ETR', 'EVC', 'EVR', 'EVRG',
                         'EVRI', 'EVTC', 'EW', 'EWBC', 'EXAS', 'EXC', 'EXEL', 'EXK', 'EXLS',
                         'EXP', 'EXPD', 'EXPE', 'EXPI', 'EXPO', 'EXR', 'EXTR', 'EZPW', 'F',
                         'FAF', 'FANG', 'FAST', 'FATE', 'FBP', 'FCEL', 'FCF', 'FCFS', 'FCN',
                         'FCX', 'FDP', 'FDS', 'FDX', 'FE', 'FELE', 'FF', 'FFBC', 'FFIN', 'FFIV',
                         'FFWM', 'FGEN', 'FHI', 'FHN', 'FIBK', 'FICO', 'FIS', 'FITB', 'FIVE',
                         'FIVN', 'FIX', 'FIZZ', 'FL', 'FLEX', 'FLO', 'FLR', 'FLS', 'FLT', 'FLWS',
                         'FMC', 'FMS', 'FMX', 'FN', 'FNB', 'FNF', 'FOLD', 'FORM', 'FOSL', 'FOXF',
                         'FR', 'FRBK', 'FRME', 'FRO', 'FRPT', 'FRT', 'FSLR', 'FSM', 'FSS',
                         'FTNT', 'FTS', 'FUL', 'FULT', 'FUN', 'FWONA', 'FWRD', 'G', 'GASS',
                         'GATX', 'GBCI', 'GBX', 'GCI', 'GCO', 'GD', 'GDEN', 'GDOT', 'GE', 'GEF',
                         'GEL', 'GEO', 'GERN', 'GES', 'GEVO', 'GFF', 'GFI', 'GGAL', 'GGB', 'GGG',
                         'GIII', 'GIL', 'GILD', 'GIS', 'GL', 'GLDD', 'GLOB', 'GLT', 'GLW', 'GM',
                         'GME', 'GMED', 'GNK', 'GNRC', 'GNTX', 'GNW', 'GOGO', 'GOL', 'GOLD',
                         'GOOGL', 'GPC', 'GPI', 'GPK', 'GPN', 'GPRE', 'GPRK', 'GPRO', 'GPS',
                         'GRBK', 'GRFS', 'GRMN', 'GRPN', 'GS', 'GT', 'GTLS', 'GTN', 'GVA',
                         'GWRE', 'GWW', 'H', 'HA', 'HAE', 'HAIN', 'HAL', 'HALO', 'HAS', 'HASI',
                         'HBAN', 'HBI', 'HBM', 'HCA', 'HCSG', 'HD', 'HDSN', 'HE', 'HEAR', 'HEES',
                         'HEI', 'HEI-A', 'HELE', 'HES', 'HFWA', 'HI', 'HIBB', 'HIG', 'HII',
                         'HIMX', 'HIW', 'HL', 'HLF', 'HLIT', 'HLT', 'HLX', 'HMC', 'HMN', 'HMY',
                         'HNI', 'HNRG', 'HOG', 'HOLX', 'HOMB', 'HON', 'HOPE', 'HP', 'HPP', 'HPQ',
                         'HQY', 'HRB', 'HRI', 'HRL', 'HROW', 'HRTX', 'HSBC', 'HSIC', 'HST',
                         'HSY', 'HTGC', 'HTH', 'HTHT', 'HTLD', 'HUBB', 'HUBG', 'HUBS', 'HUM',
                         'HUN', 'HVT', 'HWC', 'HWM', 'HXL', 'HZO', 'IAG', 'IART', 'IBKR', 'IBM',
                         'IBN', 'IBOC', 'IBTX', 'ICE', 'ICL', 'ICLR', 'ICUI', 'IDA', 'IDCC',
                         'IDEX', 'IDXX', 'IEP', 'IEX', 'IFF', 'III', 'ILMN', 'IMAX', 'IMGN',
                         'IMUX', 'INCY', 'INDB', 'INFN', 'INFY', 'ING', 'INGN', 'INGR', 'INN',
                         'INO', 'INSE', 'INSG', 'INSM', 'INTC', 'INTU', 'IONS', 'IOVA', 'IP',
                         'IPG', 'IPGP', 'IPI', 'IQV', 'IRBT', 'IRDM', 'IRM', 'IRT', 'IRWD',
                         'ISRG', 'IT', 'ITCI', 'ITGR', 'ITRI', 'ITT', 'ITUB', 'ITW', 'J', 'JACK',
                         'JAKK', 'JAZZ', 'JBHT', 'JBL', 'JBLU', 'JBT', 'JD', 'JEF', 'JKHY',
                         'JKS', 'JLL', 'JNJ', 'JNPR', 'JOE', 'JPM', 'JRVR', 'JWN', 'K', 'KALU',
                         'KAR', 'KB', 'KBH', 'KBR', 'KDP', 'KELYA', 'KEP', 'KEX', 'KEY', 'KEYS',
                         'KFY', 'KGC', 'KIM', 'KKR', 'KLAC', 'KLIC', 'KMB', 'KMI', 'KMPR', 'KMT',
                         'KMX', 'KN', 'KNDI', 'KNX', 'KO', 'KODK', 'KOF', 'KOS', 'KPTI', 'KR',
                         'KRC', 'KRG', 'KRNY', 'KRO', 'KSS', 'KT', 'KTOS', 'KW', 'L', 'LAC',
                         'LAD', 'LADR', 'LAMR', 'LANC', 'LAND', 'LAZ', 'LBAI', 'LBTYK', 'LC',
                         'LCII', 'LDOS', 'LE', 'LEA', 'LECO', 'LEG', 'LEN', 'LGF-A', 'LGIH',
                         'LH', 'LHX', 'LII', 'LIND', 'LKQ', 'LL', 'LLY', 'LMT', 'LNC', 'LNT',
                         'LOCO', 'LOPE', 'LOW', 'LPG', 'LPL', 'LPLA', 'LPSN', 'LPX', 'LQDT',
                         'LRCX', 'LRN', 'LSCC', 'LSTR', 'LTRPA', 'LTRX', 'LUMN', 'LUV', 'LVS',
                         'LXP', 'LXRX', 'LXU', 'LYG', 'LYV', 'LZB', 'M', 'MA', 'MAA', 'MAC',
                         'MAIN', 'MAN', 'MANH', 'MAR', 'MAS', 'MASI', 'MAT', 'MATX', 'MBI',
                         'MBUU', 'MC', 'MCD', 'MCHP', 'MCK', 'MCO', 'MCS', 'MCY', 'MD', 'MDC',
                         'MDGL', 'MDLZ', 'MDRX', 'MDU', 'MDXG', 'MED', 'MELI', 'MEOH', 'MERC',
                         'MET', 'MFA', 'MFC', 'MFG', 'MGA', 'MGM', 'MGNX', 'MGPI', 'MHK', 'MHO',
                         'MIDD', 'MITK', 'MKC', 'MKSI', 'MKTX', 'MLCO', 'MLI', 'MLM', 'MMC',
                         'MMM', 'MMS', 'MMSI', 'MMYT', 'MNKD', 'MNRO', 'MNST', 'MO', 'MOD',
                         'MODN', 'MOH', 'MOMO', 'MOS', 'MPC', 'MPLX', 'MPW', 'MPWR', 'MRC',
                         'MRCY', 'MRK', 'MRNS', 'MRO', 'MRTN', 'MRTX', 'MRVL', 'MS', 'MSCI',
                         'MSFT', 'MSI', 'MSM', 'MSTR', 'MT', 'MTB', 'MTCH', 'MTDR', 'MTG', 'MTH',
                         'MTLS', 'MTN', 'MTSI', 'MTW', 'MTX', 'MTZ', 'MU', 'MUFG', 'MUR', 'MUSA',
                         'MUX', 'MVIS', 'MWA', 'MX', 'MXL', 'MYGN', 'NAVI', 'NBIX', 'NDAQ',
                         'NDLS', 'NDSN', 'NEGG', 'NEM', 'NEO', 'NEOG', 'NETI', 'NEWT', 'NFG',
                         'NFLX', 'NGG', 'NGL', 'NI', 'NICE', 'NJR', 'NKE', 'NKTR', 'NLY', 'NMIH',
                         'NMM', 'NMR', 'NNN', 'NOAH', 'NOC', 'NOK', 'NOTV', 'NOV', 'NOVT', 'NOW',
                         'NR', 'NRG', 'NS', 'NSC', 'NSIT', 'NSP', 'NSSC', 'NSTG', 'NTAP', 'NTCT',
                         'NTES', 'NTGR', 'NTRS', 'NUE', 'NUS', 'NVAX', 'NVDA', 'NVGS', 'NVO',
                         'NVRO', 'NVS', 'NWBI', 'NWE', 'NWG', 'NWL', 'NWN', 'NWS', 'NXST',
                         'NYCB', 'NYMT', 'NYT', 'O', 'OC', 'OCFC', 'OCGN', 'OCUL', 'ODFL', 'ODP',
                         'OEC', 'OFG', 'OFIX', 'OGE', 'OGI', 'OGS', 'OHI', 'OI', 'OII', 'OIS',
                         'OKE', 'OLED', 'OLN', 'OMC', 'OMCL', 'OMER', 'OMF', 'OMI', 'ON', 'ONB',
                         'ONTO', 'OPCH', 'OPK', 'OPRX', 'ORA', 'ORAN', 'ORCL', 'ORI', 'ORLY',
                         'OSK', 'OSPN', 'OSUR', 'OTEX', 'OTTR', 'OUT', 'OVV', 'OXM', 'OXY',
                         'OZK', 'PAA', 'PAAS', 'PACB', 'PACW', 'PAG', 'PAGP', 'PAHC', 'PANL',
                         'PANW', 'PAR', 'PARR', 'PATK', 'PAYC', 'PAYX', 'PB', 'PBA', 'PBF',
                         'PBH', 'PBI', 'PBR', 'PBYI', 'PCAR', 'PCG', 'PCH', 'PCRX', 'PCTY',
                         'PDCO', 'PDM', 'PEAK', 'PEB', 'PEG', 'PEGA', 'PENN', 'PEP', 'PERI',
                         'PETS', 'PFE', 'PFG', 'PFS', 'PFSI', 'PG', 'PGEN', 'PGR', 'PGRE',
                         'PGTI', 'PH', 'PHG', 'PHM', 'PII', 'PINC', 'PKG', 'PKX', 'PLAB', 'PLAY',
                         'PLCE', 'PLD', 'PLUG', 'PM', 'PNC', 'PNFP', 'PNM', 'PNW', 'PODD',
                         'POOL', 'POR', 'POST', 'POWI', 'PPBI', 'PPC', 'PPG', 'PPL', 'PRA',
                         'PRAA', 'PRDO', 'PRFT', 'PRGS', 'PRI', 'PRIM', 'PRLB', 'PRMW', 'PRO',
                         'PRTA', 'PRTS', 'PRU', 'PSA', 'PSO', 'PSX', 'PTC', 'PTCT', 'PTEN',
                         'PUK', 'PVH', 'PWR', 'PXD', 'PZZA', 'QCOM', 'QDEL', 'QLYS', 'QMCO',
                         'QNST', 'QRTEA', 'QRTEB', 'QRVO', 'QSR', 'QTWO', 'QUAD', 'R', 'RARE',
                         'RBA', 'RBBN', 'RC', 'RCI', 'RDN', 'RDNT', 'RDWR', 'RDY', 'REG', 'REGN',
                         'RELL', 'RELX', 'RES', 'REXR', 'RGA', 'RGEN', 'RGP', 'RH', 'RHI', 'RHP',
                         'RIGL', 'RILY', 'RIO', 'RIOT', 'RJF', 'RL', 'RLJ', 'RMAX', 'RMBS',
                         'RMD', 'RNG', 'RNST', 'ROCK', 'ROG', 'ROIC', 'ROK', 'ROL', 'ROP',
                         'ROST', 'RPM', 'RPT', 'RRC', 'RRGB', 'RS', 'RSG', 'RTX', 'RUSHA',
                         'RVNC', 'RWT', 'RY', 'RYAAY', 'RYAM', 'RYI', 'RYN', 'SABR', 'SAGE',
                         'SAH', 'SAIA', 'SAIC', 'SAN', 'SANM', 'SAP', 'SATS', 'SAVE', 'SBAC',
                         'SBCF', 'SBGI', 'SBH', 'SBNY', 'SBS', 'SBSW', 'SBUX', 'SCCO', 'SCHL',
                         'SCHW', 'SCI', 'SCOR', 'SCS', 'SCVL', 'SEAS', 'SEE', 'SEIC', 'SEM',
                         'SF', 'SFM', 'SFNC', 'SGEN', 'SGMO', 'SHG', 'SHOO', 'SHW', 'SHYF',
                         'SID', 'SIG', 'SIGI', 'SIMO', 'SIRI', 'SITC', 'SIX', 'SJM', 'SKM',
                         'SKT', 'SKX', 'SKY', 'SKYW', 'SLAB', 'SLCA', 'SLF', 'SLG', 'SLGN',
                         'SLM', 'SLNG', 'SM', 'SMCI', 'SMFG', 'SMG', 'SMSI', 'SMTC', 'SNA',
                         'SNBR', 'SNN', 'SNPS', 'SNV', 'SNX', 'SNY', 'SO', 'SOL', 'SON', 'SONY',
                         'SPB', 'SPG', 'SPGI', 'SPH', 'SPLK', 'SPNS', 'SPNT', 'SPR', 'SPTN',
                         'SPWH', 'SPWR', 'SPXC', 'SQM', 'SR', 'SRC', 'SRCL', 'SRE', 'SRPT',
                         'SSB', 'SSD', 'SSL', 'SSNC', 'SSP', 'SSRM', 'SSTK', 'SSYS', 'ST',
                         'STAA', 'STAG', 'STKL', 'STLD', 'STM', 'STT', 'STWD', 'STZ', 'SU',
                         'SUI', 'SUN', 'SUPN', 'SWBI', 'SWK', 'SWKS', 'SWN', 'SWX', 'SXC', 'SXT',
                         'SYF', 'SYK', 'SYNA', 'SYY', 'T', 'TAC', 'TAK', 'TAL', 'TAP', 'TBBK',
                         'TBI', 'TBPH', 'TCBI', 'TCOM', 'TCS', 'TD', 'TDC', 'TDG', 'TDS', 'TDW',
                         'TDY', 'TECH', 'TECK', 'TEF', 'TEL', 'TER', 'TEVA', 'TEX', 'TFC',
                         'TFII', 'TFSL', 'TFX', 'TGH', 'TGI', 'TGNA', 'TGT', 'TGTX', 'THC',
                         'THG', 'THO', 'THRM', 'THS', 'TILE', 'TITN', 'TJX', 'TK', 'TKR', 'TLK',
                         'TLYS', 'TM', 'TMHC', 'TMO', 'TMST', 'TMUS', 'TNDM', 'TNET', 'TNL',
                         'TOL', 'TPC', 'TPH', 'TPR', 'TPX', 'TREE', 'TREX', 'TRGP', 'TRI',
                         'TRIP', 'TRMB', 'TRMK', 'TRN', 'TROW', 'TROX', 'TRP', 'TRUE', 'TRUP',
                         'TRV', 'TS', 'TSCO', 'TSE', 'TSEM', 'TSLA', 'TSM', 'TSN', 'TT', 'TTC',
                         'TTEK', 'TTGT', 'TTI', 'TTMI', 'TTWO', 'TU', 'TUP', 'TV', 'TWI', 'TWO',
                         'TWOU', 'TX', 'TXN', 'TXRH', 'TXT', 'TYL', 'UAA', 'UAL', 'UBSI', 'UCBI',
                         'UCTT', 'UDR', 'UFPI', 'UGI', 'UGP', 'UHS', 'UIS', 'UL', 'ULTA', 'UMBF',
                         'UMC', 'UMH', 'UNFI', 'UNH', 'UNM', 'UNP', 'UPLD', 'UPS', 'URBN', 'URI',
                         'USB', 'UTHR', 'UTI', 'UVE', 'V', 'VAC', 'VALE', 'VBIV', 'VBTX', 'VC',
                         'VCEL', 'VCYT', 'VECO', 'VEEV', 'VEON', 'VERU', 'VET', 'VFC', 'VGR',
                         'VIAV', 'VICR', 'VIPS', 'VIV', 'VLO', 'VLRS', 'VLY', 'VMC', 'VMW',
                         'VNDA', 'VNET', 'VNO', 'VOD', 'VOYA', 'VRNS', 'VRNT', 'VRSK', 'VRSN',
                         'VRTX', 'VSAT', 'VSH', 'VTNR', 'VTR', 'VUZI', 'VXRT', 'VZ', 'W', 'WAB',
                         'WAFD', 'WAL', 'WAT', 'WB', 'WBA', 'WBS', 'WCC', 'WCN', 'WDAY', 'WDC',
                         'WEC', 'WELL', 'WEN', 'WERN', 'WES', 'WEX', 'WFC', 'WGO', 'WHR', 'WIRE',
                         'WIT', 'WIX', 'WK', 'WLK', 'WM', 'WMB', 'WMS', 'WMT', 'WNC', 'WNS',
                         'WOR', 'WPC', 'WPP', 'WPRT', 'WRB', 'WSBC', 'WSFS', 'WSM', 'WSO', 'WSR',
                         'WST', 'WTFC', 'WTI', 'WTRG', 'WU', 'WW', 'WWD', 'WWW', 'WY', 'WYNN',
                         'X', 'XEL', 'XENE', 'XNCR', 'XOM', 'XPEL', 'XPO', 'XRAY', 'XRX', 'XXII',
                         'XYL', 'YELP', 'YPF', 'YUM', 'YY', 'ZBH', 'ZBRA', 'ZG', 'ZION', 'ZTS',
                         'ZUMZ', 'ZYXI']

        else:
            companies = self.company_pool
        logger.info("Now downloading returns data.")
        df_returns = self.data_service.ticker_data_historic(
            companies, start=start_date, end=stop_date, pct_change=True)[OHLC_spec]
        self._df_returns = df_returns
        return df_returns.dropna()

    def _get_factor_data(self, start_date):
        df_factors = self.famafrench_data.famafrench_data_historic(start_date)
        self._df_factors = df_factors
        return df_factors, self.famafrench_data.latest_date

    def run_strategy(self, train_period: int = 24):
        """Run MaxDistance-Strategy."""
        start_date = (
            dt.today() - relativedelta(months=train_period)).strftime('%Y-%m-%d')
        # first download factor data and check latest available data
        factor_df, latest_avail_factor_data = self._get_factor_data(
            start_date=start_date)

        returns_df = self._get_returns_data(
            start_date=start_date, stop_date=latest_avail_factor_data)

        analysis_df = returns_df.merge(factor_df, left_index=True, right_index=True)
        betas_scal_df = self.estimate_betas(
            analysis_df, drop_outliers=True, standard_scaled_data=True)
        low_risk_betas, lowest_risk_comp_idx = self.get_low_risk_cluster(betas_scal_df)
        weights = self.calculate_farthest_distances(
            low_risk_betas, lowest_risk_comp_idx, n=20)

        print(weights)

        self.weights = weights
        return weights

    @staticmethod
    def estimate_betas(df, drop_outliers=True, standard_scaled_data=True):
        '''
        Function description:
        Fama-French Regression of daily discrete company returns on the three Fama-French Factors.

        Parameters:
            df: a pandas DataFrame containing stock returns and the Fama-French factors
            drop_outliers: a boolean parameter indicating whether to drop the top and bottom 
            1% of the distribution of each factor. Default is True.
            standard_scaled_data: a boolean parameter indicating whether to standard scale 
            the betas. Default is True.

        Returns:
            betas: a pandas DataFrame containing estimated betas for each company with respect 
            to the Fama-French factors. The betas are standard-scaled if the 
            standard_scaled_data parameter is set to True.
            residuals: a pandas DataFrame containing residuals for each company after the 
            regression with respect to the Fama-French factors.
            scaler: a StandardScaler object that was used to standard-scale the betas. If 
            standard_scaled_data parameter is set to False, it returns None.
        '''

        # Fama-French regression
        companies = list(df.iloc[:, :-4].columns)
        residuals = pd.DataFrame(columns=companies)
        betas = pd.DataFrame(columns=['Mkt-RF', 'SMB', 'HML'])
        models = dict()
        X = df[['Mkt-RF', 'SMB', 'HML']]
        X = sm.add_constant(X)

        for company in companies:
            y = df[company] - df['RF']
            model = sm.OLS(y, X).fit()
            models[company] = model
            betas.loc[company, :] = model.params[1:].values
            residuals.loc[:, company] = y - model.predict(X)

        # Dropping outliers
        if drop_outliers:
            outlier_pct = 0.01

            low_threshold_mkt, high_threshold_mkt = betas['Mkt-RF'].quantile(
                outlier_pct), betas['Mkt-RF'].quantile(1-outlier_pct)
            low_threshold_smb, high_threshold_smb = betas['SMB'].quantile(
                outlier_pct),    betas['SMB'].quantile(1-outlier_pct)
            low_threshold_hml, high_threshold_hml = betas['HML'].quantile(
                outlier_pct),    betas['HML'].quantile(1-outlier_pct)

            outlier_rows = betas[(betas['Mkt-RF'] <= low_threshold_mkt) | (betas['Mkt-RF'] >= high_threshold_mkt) |
                                 (betas['SMB'] <= low_threshold_smb) | (betas['SMB'] >= high_threshold_smb) |
                                 (betas['HML'] <= low_threshold_hml) | (betas['HML'] >= high_threshold_hml)].index

            betas.drop(outlier_rows, inplace=True)
        else:
            pass

        # Standard scaling the data (please note that the scaler was only used for
        # standard-scaling the betas. The residuals are not standard-scaled.)
        if standard_scaled_data:
            scaler = StandardScaler()
            mapper = DataFrameMapper([(betas.columns, scaler)])
            scaled_features = mapper.fit_transform(betas.copy(), 3)
            betas = pd.DataFrame(scaled_features, index=betas.index,
                                 columns=betas.columns)
        else:
            scaler = None

        return betas

    @staticmethod
    def get_low_risk_cluster(betas_scal_df):
        '''
        Function description:
        It calculates the cluster with the lowest risk, where the risk is defined as the 
        average market beta of the cluster.

        Parameters:
            betas_scal_df (pandas DataFrame): A DataFrame containing the beta coefficients 
            from the Fama-French Regression of all companies. 

        Returns:
            low_risk_betas (pandas DataFrame): A DataFrame containing the beta coefficients 
            of the companies in the lowest risk cluster.
            lowest_risk_comp_idx (int): The index of the company with the lowest risk in the 
            lowest risk cluster.
        '''
        # K-Means clustering
        kmeans = KMeans(n_clusters=3, random_state=123).fit(betas_scal_df)
        cluster_centers = kmeans.cluster_centers_

        betas_scal_df["cluster"] = [np.nan for i in range(len(betas_scal_df))]
        for comp in betas_scal_df.index:
            comp_betas = betas_scal_df.loc[comp, :][0:3].values.reshape(1, -1)
            betas_scal_df.loc[comp, "cluster"] = int(kmeans.predict(comp_betas))

        # filter for the lowest risk cluster, where the market beta is the lowest
        market_factor_centroids = cluster_centers[:, 0]
        lowest_market_factor_cluster = np.argmin(market_factor_centroids)
        low_risk_betas = betas_scal_df[betas_scal_df["cluster"]
                                       == lowest_market_factor_cluster].drop("cluster", axis=1)
        lowest_risk_comp_idx = low_risk_betas.sum(axis=1).argmin()

        return low_risk_betas, lowest_risk_comp_idx

    @staticmethod
    def calculate_farthest_distances(df_betas, lowest_risk_comp_idx, n=10):
        '''
        Function description:
        It calculates the n farthest points from each other and returns the symbols 
        (company ticker symbols) of those farthest points. 

        Parameters:
            df_betas (pandas DataFrame): A DataFrame containing the beta coefficients 
            from the Fama-French Regression of all companies. 
            n (int): The number of farthest points to be selected. Default is 10.
            show_3d_plot (bool): Whether to show a 3D scatter plot of the points and the 
            selected farthest points. Default is False.

        Returns:
            n_farthest_symbols (list): A list of symbols (company names) of the farthest
            n points from each other.

        Notes:
            The starting point is chosen randomly.
            The approach of maximizing the total distance between all points via a for 
            loop where each company is taken once as a starting point took too much runtime, so I continue with this simplified approach.
            The algorithm may not be written very efficiently.
        '''

        # The starting point is the company in the first row, as it gets selected by the algorithm in the first round. We randomly assign the first seed to a company.
        points = [(x[0], x[1], x[2]) for x in df_betas.to_numpy()]
        points[lowest_risk_comp_idx], points[0] = points[0], points[lowest_risk_comp_idx]

        # Select n points such that each point is as far away from the others as possible
        selected_points = []
        while len(selected_points) < n:
            # Find the point that is farthest from all previously selected points
            farthest_point = None
            farthest_distance = 0
            for point in points:
                # Calculate the distance from this point to the closest selected point
                tmp_distance = float("inf")
                for selected_point in selected_points:
                    # Using the Euclidean distance algorithm
                    distance = ((point[0] - selected_point[0]) ** 2 + (point[1] -
                                selected_point[1]) ** 2 + (point[2] - selected_point[2]) ** 2) ** 0.5
                    tmp_distance = min(tmp_distance, distance)
                # Update the farthest point and distance if this point is farther than the previous farthest point
                if tmp_distance > farthest_distance:
                    farthest_point = point
                    farthest_distance = tmp_distance
            # Add the farthest point to the selected points
            selected_points.append(farthest_point)

        # get n farthest symbols
        df_betas_copy = df_betas.copy()
        df_betas_copy['symbol'] = df_betas_copy.index
        df_betas_copy['n_farthest_points'] = np.isin(df_betas, selected_points)[:, 0]
        df_n_farthest_points = df_betas_copy[df_betas_copy['n_farthest_points']]
        n_farthest_symbols = dict(zip(df_n_farthest_points['symbol'], [1/n]*n))

        return n_farthest_symbols

    @property
    def company_pool(self):
        """Returns the company pool."""
        return self._company_pool

    @company_pool.setter
    def company_pool(self, value):
        if isinstance(value, list):
            if non_valid_symbols := [symbol for symbol in value if not isinstance(symbol, str)]:
                raise TypeError("Not all symbols in `ticker_symbols` are of type string. The"
                                " following non valid symbols have been provided:"
                                f" {non_valid_symbols}.")
        elif isinstance(value, str):
            if value not in self._valid_inputs["company_pool"]:
                raise ValueError(f"`company_pool` must be one of {self._valid_inputs['company_pool']}"
                                 f" or a list of ticker symbols. Received {value}")
        else:
            raise TypeError("`company_pool` must be of type str or list.")
        self._company_pool = value

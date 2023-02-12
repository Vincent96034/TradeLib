


class Hold_Strategy:
    ''' Just hold all funds and do nothing; used as a fallback '''

    def __init__(self):
        pass

    def strategy_run(self):
        ''' Generic function for every strategy class: runs strategy '''
        print("... run hold strategy")
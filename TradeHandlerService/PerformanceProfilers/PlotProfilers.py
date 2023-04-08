from TradeHandlerService.PerformanceProfilers.ParentProfilers import PlotProfiler


class PlotTimeValProfiler(PlotProfiler):
    """
    - Plot value over time of portfolio
    """
    def run_profiler(self):
        return self.format_result(self.input)


class PlotRetDistrProfiler(PlotProfiler):
    """
    - Plot return distribution of portfolio
    """
    def run_profiler(self):
        return self.format_result(self.input)


class PlotVolaDistrProfiler(PlotProfiler):
    """
    - Plot volatility distribution of portfolio
    """
    def run_profiler(self):
        return self.format_result(self.input)
    

class PlotBenchmarkProfiler(PlotProfiler):
    """
    - Plot benchmark value over time
    """
    def run_profiler(self):
        return self.format_result(self.input)



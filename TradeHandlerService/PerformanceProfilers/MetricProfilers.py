from TradeHandlerService.PerformanceProfilers.ParentProfilers import StandardProfiler


class BasicProfiler(StandardProfiler):
    """
    - Balance
    - Rel performance
    - Abs performance
    """
    def run_profiler(self):
        return self.format_result(self.input)


class RiskProfiler(StandardProfiler):
    """
    - Standard deviation
    - Value at risk
    - Conditional value at risk
    - ...
    """
    def run_profiler(self):
        return self.format_result(self.input)


class BenchmarkProfiler(StandardProfiler):
    """
    - Return vs. Benchmark
    - Correlation & R^2
    - ...
    """
    def run_profiler(self):
        return self.format_result(self.input)


class AdvancedProfiler(StandardProfiler):
    """
    - Beta
    - Sharpe Ratio
    - Sortino Ratio
    - ...
    """
    def run_profiler(self):
        return self.format_result(self.input)


class AccountProfiler(StandardProfiler):
    """
    - Balance
    - Cash to invest
    - Cash to withdraw
    """
    def run_profiler(self):
        return self.format_result(self.input)

class BaseProfiler:
    """ Base class for all Profiler-Parent Classes. Includes basic functionality
    like getting the name of the profiler, etc. """
    def __init__(self):
        self.input = None

    def get_reqired_input(self):
        """ Returns a list of the required inputs of the Profiler. 
        Defaults to the lemon class as single input.
        """
        return ["lemon"]

    def run_profiler(self):
        raise NotImplementedError("The profiler is not implemented yet.")

    def format_result(self, result, metadata):
        return {
            "result": result,
            "metadata": metadata}
    
    def get_name(self):
        return self.__class__.__name__



class StandardProfiler(BaseProfiler):
    """ Parent class for all standard Profiler classes.
    Overwrites the format_result method from BaseProfiler.
    """
    def format_result(self, result, metadata):
        return {
            "result": result,
            "metadata": metadata
        }
    

class PlotProfiler(BaseProfiler):
    """ Parent class for all Profiler classes that produce plots.
    Overwrites the format_result method from BaseProfiler.
    """
    def format_result(self, result, metadata, plot):
        return {
            "result": result,
            "metadata": metadata,
            "plot": plot
        }
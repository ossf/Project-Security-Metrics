class BaseJob(object):
    def __init__(self):
        pass

    def run(self):
        raise NotImplementedError("This method should be called against a subclass.")

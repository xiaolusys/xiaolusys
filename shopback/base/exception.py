class RuleMatchPruductException(Exception):
    def __init__(self, msg=''):
        self.msg = msg

    def __str__(self):
        return self.msg


class NotImplement(Exception):
    # for extend class override method
    def __init__(self, msg=''):
        self.msg = msg

    def __str__(self):
        return self.msg

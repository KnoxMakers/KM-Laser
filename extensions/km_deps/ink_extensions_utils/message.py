import logging

from ink_extensions import inkex

# alias that makes more semantic sense to how inkex.errormsg is used
emit = inkex.errormsg

class UserMessageHandler(logging.Handler):
    ''' To be used when a message is logged, and the user should receive the message
    (e.g. an error message)'''

    def __init__(self, formatter=None):
        super(UserMessageHandler, self).__init__()

        # if no formatter specified, set the logging formatter to one that passes the message
        # through unchanged (i.e. without adding dates, etc.)
        self.setFormatter(formatter if formatter is not None else logging.Formatter())
        
    def emit(self, record):
        emit(self.format(record))

import logging
from mock import patch
import unittest


from ink_extensions_utils import message

# python -m unittest discover in top-level package dir

@patch.object(message.inkex, "errormsg")
class UserMessageHandlerTestCase(unittest.TestCase):

    def test_init(self, m_errormsg):
        logger = logging.getLogger('test_init')
        a_message = "a message"        
        handler = message.UserMessageHandler()
        logger.addHandler(handler)

        logger.info(a_message)

        m_errormsg.error_msg.called_once_with(a_message) # message is unchanged (default formatter)

    def test_init_w_formatter(self, m_errormsg):
        logger = logging.getLogger('test_init_w_formatter')
        format_string = 'a really silly format that discards the actual message'
        handler = message.UserMessageHandler(logging.Formatter(format_string))
        logger.addHandler(handler)

        logger.info("WEEEOOOWEEEOOOWEEEOOO")

        m_errormsg.error_msg.called_once_with(format_string)

    @patch.object(message.UserMessageHandler, "format")
    @patch.object(message, "emit")
    def test_handler(self, m_emit, m_format, m_errormsg):
        handler = message.UserMessageHandler()
        a_message = "a message"
        record = logging.LogRecord("", 0, "", 0, a_message, {}, {})
        m_format.return_value = a_message
        
        handler.emit(record)

        m_format.assert_called_once_with(record)
        m_emit.assert_called_once_with(a_message)

import sys
import logging


# logging.basicConfig(level=logging.DEBUG,
#                     filename="blockchain_simulation.log",
#                     filemode='w',
#                     format='%(asctime)s - %(levelname)s - %(funcName)s - %(message)s')
# logger = logging.getLogger(__name__)


def init_logger():
    logging.basicConfig(
        # level=logging.DEBUG,
        # stream=sys.stdout,
        filename="blockchain_simulation.log",
        filemode="w",
        format="%(asctime)s - %(levelname)s - %(funcName)s - %(message)s",
        datefmt="%H:%M:%S",
    )
    logger = logging.getLogger(__name__)
    return logger

class Config:
    TEST_CASE_NAME = "z1_10_z2_0"
    NUMBER_OF_PEERS = 50  # n
    Z1 = 1.0  # zeta1
    Z2 = 0.001  # zeta2
    AVG_TXN_INTERVAL_TIME = 100  # Ttx

    ## below parameters are unchanged for all the experiments

    SAVE_RESULTS = True

    Z0 = 0.5  # network z0 is slow

    NUMBER_OF_TRANSACTIONS_PER_PEER = 200  # not used

    # mean of exponential time interval bw transactions (ms)
    INITIAL_COINS = 1000
    EVENT_QUEUE_TIMEOUT = 5
    BLOCK_TXNS_MAX_THRESHOLD = 1020  # 1020
    BLOCK_TXNS_TARGET_THRESHOLD = 5
    BLOCK_TXNS_MIN_THRESHOLD = 2
    AVG_BLOCK_MINING_TIME = 10000  # avg block interval time (ms)

    # sim stop conditions
    MAX_NUM_BLOCKS = NUMBER_OF_PEERS * 3

    NUMBER_OF_TRANSACTIONS = MAX_NUM_BLOCKS * BLOCK_TXNS_TARGET_THRESHOLD

    def __dict__(self):
        return {
            "TEST_CASE_NAME": self.TEST_CASE_NAME,
            "NUMBER_OF_PEERS": self.NUMBER_OF_PEERS,
            "Z1": self.Z1,
            "Z2": self.Z2,
            "AVG_TXN_INTERVAL_TIME": self.AVG_TXN_INTERVAL_TIME,
            "SAVE_RESULTS": self.SAVE_RESULTS,
            "Z0": self.Z0,
            "NUMBER_OF_TRANSACTIONS_PER_PEER": self.NUMBER_OF_TRANSACTIONS_PER_PEER,
            "INITIAL_COINS": self.INITIAL_COINS,
            "EVENT_QUEUE_TIMEOUT": self.EVENT_QUEUE_TIMEOUT,
            "BLOCK_TXNS_MAX_THRESHOLD": self.BLOCK_TXNS_MAX_THRESHOLD,
            "BLOCK_TXNS_TARGET_THRESHOLD": self.BLOCK_TXNS_TARGET_THRESHOLD,
            "BLOCK_TXNS_MIN_THRESHOLD": self.BLOCK_TXNS_MIN_THRESHOLD,
            "AVG_BLOCK_MINING_TIME": self.AVG_BLOCK_MINING_TIME,
            "MAX_NUM_BLOCKS": self.MAX_NUM_BLOCKS,
            "NUMBER_OF_TRANSACTIONS": self.NUMBER_OF_TRANSACTIONS,
        }


CONFIG = Config()

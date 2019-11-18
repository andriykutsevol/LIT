import testlib


def run_test(env):
    print("Sell Contract")

    bc = env.bitcoind

    lit1 = env.lits[0]
    lit2 = env.lits[1]
    lit3 = env.lits[2]

    lit1.connect_to_peer(lit2)

    lit1.rpc.SellContract()

    
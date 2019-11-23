import testlib


def run_test(env):
    print("Sell Contract")

    bc = env.bitcoind

    lit1 = env.lits[0]
    lit2 = env.lits[1]


    lit1.connect_to_peer(lit2)


    ##res = lit1.rpc.OfferContract(CIdx=contract["Contract"]["Idx"], PeerIdx=lit1.get_peer_id(lit2))
    ##assert res["Success"], "OfferContract does not works"

    # NegotiateContractResult =  lit1.rpc.NegotiateContract (CIdx, DesiredOracleValue)


    ##res = lit2.rpc.ContractRespond(AcceptOrDecline=True, CIdx=1)
    ##assert res["Success"], "ContractRespond on lit2 does not works"

    # NegotiateContractRespondResult = lit2.rpc.NegotiateContractRespond(CIdx)







    
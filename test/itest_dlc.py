import testlib

import time, datetime
import json

import pprint

import requests # pip3 install requests

import codecs

deb_mod = False

def run_t(env, params):
    global deb_mod
    try:

        lit_funding_amt = params[0]
        contract_funding_amt = params[1]
        oracle_value = params[2]
        node_to_settle = params[3]
        valueFullyOurs=params[4]
        valueFullyTheirs=params[5]

        FundingTxVsize = params[6][0]
        SettlementTxVsize = params[6][1]

        feeperbyte = params[7]

        SetTxFeeOurs = params[8]
        SetTxFeeTheirs = params[9]

        ClaimTxFeeOurs = params[10]
        ClaimTxFeeTheirs = params[11]

        bc = env.bitcoind

        #------------
        # Create oracles
        #------------

        env.new_oracle(1, oracle_value) # publishing interval is 1 second.

        #settle_lit = env.lits[node_to_settle]

        oracle1 = env.oracles[0]

        time.sleep(2)

        #------------
        # Create lits
        #------------

        lit1 = env.lits[0]
        lit2 = env.lits[1]


        pp = pprint.PrettyPrinter(indent=4)


        #------------------------------------------
        if deb_mod:
            print("ADDRESSES BEFORE SEND TO ADDRESS")
            print("LIT1 Addresses")
            print(pp.pprint(lit1.rpc.GetAddresses()))

            print("LIT2 Addresses")
            print(pp.pprint(lit2.rpc.GetAddresses()))

            print("bitcoind Addresses")
            print(pp.pprint(bc.rpc.listaddressgroupings()))
        #------------------------------------------ 


        lit1.connect_to_peer(lit2)
        print("---------------")
        print('Connecting lit1:', lit1.lnid, 'to lit2:', lit2.lnid)

        addr1 = lit1.make_new_addr()
        txid1 = bc.rpc.sendtoaddress(addr1, lit_funding_amt)

        if deb_mod:
            print("Funding TxId lit1: " + str(txid1))

        time.sleep(5)

        addr2 = lit2.make_new_addr()
        txid2 = bc.rpc.sendtoaddress(addr2, lit_funding_amt)

        if deb_mod:
            print("Funding TxId lit2: " + str(txid2))

        time.sleep(5)

        env.generate_block()
        time.sleep(5)

        print("Funding")
        bals1 = lit1.get_balance_info()  
        print('new lit1 balance:', bals1['TxoTotal'], 'in txos,', bals1['ChanTotal'], 'in chans')
        bal1sum = bals1['TxoTotal'] + bals1['ChanTotal']
        print('  = sum ', bal1sum)

        print(lit_funding_amt)

        lit_funding_amt *= 100000000        # to satoshi

        


        bals2 = lit2.get_balance_info()
        print('new lit2 balance:', bals2['TxoTotal'], 'in txos,', bals2['ChanTotal'], 'in chans')
        bal2sum = bals2['TxoTotal'] + bals2['ChanTotal']
        print('  = sum ', bal2sum) 


        assert bal1sum == lit_funding_amt, "Funding lit1 does not works"
        assert bal2sum == lit_funding_amt, "Funding lit2 does not works"
        

        #------------------------------------------
        if deb_mod:
            print("ADDRESSES AFTER SEND TO ADDRESS")
            print("LIT1 Addresses")
            print(pp.pprint(lit1.rpc.GetAddresses()))

            print("LIT2 Addresses")
            print(pp.pprint(lit2.rpc.GetAddresses()))

            print("bitcoind Addresses")
            print(pp.pprint(bc.rpc.listaddressgroupings()))
        #------------------------------------------          


        # #------------
        # # Add oracles
        # #------------

        res = lit1.rpc.ListOracles()
        assert len(res) != 0, "Initial lis of oracles must be empty"
        
        oracle1_pubkey = json.loads(oracle1.get_pubkey())
        assert len(oracle1_pubkey["A"]) == 66, "Wrong oracle1 pub key"
        
        # oracle2_pubkey = json.loads(oracle2.get_pubkey())
        # assert len(oracle2_pubkey["A"]) == 66, "Wrong oracle2 pub key"

        oracle_res1 = lit1.rpc.AddOracle(Key=oracle1_pubkey["A"], Name="oracle1")
        assert oracle_res1["Oracle"]["Idx"] == 1, "AddOracle does not works"

        res = lit1.rpc.ListOracles(ListOraclesArgs={})
        assert len(res["Oracles"]) == 1, "ListOracles 1 does not works"


        lit2.rpc.AddOracle(Key=oracle1_pubkey["A"], Name="oracle1")


        # #------------
        # # Now we have to create a contract in the lit1 node.
        # #------------

        contract = lit1.rpc.NewContract()

        res = lit1.rpc.ListContracts()
        assert len(res["Contracts"]) == 1, "ListContracts does not works"


        res = lit1.rpc.GetContract(Idx=1)
        assert res["Contract"]["Idx"] == 1, "GetContract does not works"
                

        res = lit1.rpc.SetContractOracle(CIdx=contract["Contract"]["Idx"], OIdx=oracle_res1["Oracle"]["Idx"])
        assert res["Success"], "SetContractOracle does not works"

        datasources = json.loads(oracle1.get_datasources())

        # Since the oracle publishes data every 1 second (we set this time above), 
        # we increase the time for a point by 3 seconds.

        settlement_time = int(time.time()) + 3

        # dlc contract settime 1 1552080600
        lit1.rpc.SetContractSettlementTime(CIdx=contract["Contract"]["Idx"], Time=settlement_time)

        res = lit1.rpc.ListContracts()
        assert res["Contracts"][contract["Contract"]["Idx"] - 1]["OracleTimestamp"] == settlement_time, "SetContractSettlementTime does not match settlement_time"

        rpoint1 = oracle1.get_rpoint(datasources[0]["id"], settlement_time)

        decode_hex = codecs.getdecoder("hex_codec")
        b_RPoint = decode_hex(json.loads(rpoint1)['R'])[0]
        RPoint = [elem for elem in b_RPoint]

        res = lit1.rpc.SetContractRPoint(CIdx=contract["Contract"]["Idx"], RPoint=RPoint)
        assert res["Success"], "SetContractRpoint does not works"

        lit1.rpc.SetContractCoinType(CIdx=contract["Contract"]["Idx"], CoinType = 257)
        res = lit1.rpc.GetContract(Idx=contract["Contract"]["Idx"])
        assert res["Contract"]["CoinType"] == 257, "SetContractCoinType does not works"


        lit1.rpc.SetContractFeePerByte(CIdx=contract["Contract"]["Idx"], FeePerByte = feeperbyte)
        res = lit1.rpc.GetContract(Idx=contract["Contract"]["Idx"])
        assert res["Contract"]["FeePerByte"] == feeperbyte, "SetContractFeePerByte does not works"        

        ourFundingAmount = contract_funding_amt
        theirFundingAmount = contract_funding_amt

        lit1.rpc.SetContractFunding(CIdx=contract["Contract"]["Idx"], OurAmount=ourFundingAmount, TheirAmount=theirFundingAmount)
        res = lit1.rpc.GetContract(Idx=contract["Contract"]["Idx"])
        assert res["Contract"]["OurFundingAmount"] == ourFundingAmount, "SetContractFunding does not works"
        assert res["Contract"]["TheirFundingAmount"] == theirFundingAmount, "SetContractFunding does not works"

        print("Before SetContractDivision")
        
        res = lit1.rpc.SetContractDivision(CIdx=contract["Contract"]["Idx"], ValueFullyOurs=valueFullyOurs, ValueFullyTheirs=valueFullyTheirs)
        assert res["Success"], "SetContractDivision does not works"
        
        print("After SetContractDivision")

        time.sleep(8)
  

        res = lit1.rpc.ListConnections()
        print(res)

        print("Before OfferContract")

        res = lit1.rpc.OfferContract(CIdx=contract["Contract"]["Idx"], PeerIdx=lit1.get_peer_id(lit2))
        assert res["Success"], "OfferContract does not works"

        print("After OfferContract")

        time.sleep(8)
       

        print("Before ContractRespond")

        res = lit2.rpc.ContractRespond(AcceptOrDecline=True, CIdx=1)
        assert res["Success"], "ContractRespond on lit2 does not works"

        print("After ContractRespond")

        time.sleep(8)

        #------------------------------------------
        
        if deb_mod:
            print("ADDRESSES AFTER CONTRACT RESPOND")
            print("LIT1 Addresses")
            print(lit1.rpc.GetAddresses())

            print("LIT2 Addresses")
            print(lit2.rpc.GetAddresses())

            print("bitcoind Addresses")
            print(bc.rpc.listaddressgroupings())


        # #------------------------------------------  


        print("Before Generate Block")

        env.generate_block()
        time.sleep(5)

        print("After Generate Block")

        print("Accept")
        bals1 = lit1.get_balance_info()  
        print('new lit1 balance:', bals1['TxoTotal'], 'in txos,', bals1['ChanTotal'], 'in chans')
        bal1sum = bals1['TxoTotal'] + bals1['ChanTotal']
        print('  = sum ', bal1sum)

        lit1_bal_after_accept = (lit_funding_amt - ourFundingAmount) - (126*feeperbyte)
        

        bals2 = lit2.get_balance_info()
        print('new lit2 balance:', bals2['TxoTotal'], 'in txos,', bals2['ChanTotal'], 'in chans')
        bal2sum = bals2['TxoTotal'] + bals2['ChanTotal']
        print('  = sum ', bal2sum)   

        lit2_bal_after_accept = (lit_funding_amt - theirFundingAmount) - (126*feeperbyte)


        assert bal1sum == lit1_bal_after_accept, "lit1 Balance after contract accept does not match"
        assert bal2sum == lit2_bal_after_accept, "lit2 Balance after contract accept does not match"        

        oracle1_val = ""
        oracle1_sig = ""

        i = 0
        while True:
            res = oracle1.get_publication(json.loads(rpoint1)['R'])
            time.sleep(5)
            i += 1
            if i>4:
                assert False, "Error: Oracle does not publish data"
            
            try:
                oracle1_val = json.loads(res)["value"]
                oracle1_sig = json.loads(res)["signature"]
                break
            except BaseException as e:
                print(e)
                next


        b_OracleSig = decode_hex(oracle1_sig)[0]
        OracleSig = [elem for elem in b_OracleSig]


        print("Before SettleContract")
        time.sleep(8)


        res = env.lits[node_to_settle].rpc.SettleContract(CIdx=contract["Contract"]["Idx"], OracleValue=oracle1_val, OracleSig=OracleSig)
        assert res["Success"], "SettleContract does not works."

        time.sleep(8)

        print('After SettleContract:')
        print(res)


        try:
            env.generate_block(1)
            time.sleep(2)
            env.generate_block(10)
            time.sleep(2)
            env.generate_block(1)
        except BaseException as be:
            print("Exception After SettleContract: ")
            print(be)    

        time.sleep(10)
        #------------------------------------------

        if deb_mod:

            best_block_hash = bc.rpc.getbestblockhash()
            bb = bc.rpc.getblock(best_block_hash)
            print(bb)
            print("bb['height']: " + str(bb['height']))

            print("Balance from RPC: " + str(bc.rpc.getbalance()))

            # batch support : print timestamps of blocks 0 to 99 in 2 RPC round-trips:
            commands = [ [ "getblockhash", height] for height in range(bb['height'] + 1) ]
            block_hashes = bc.rpc.batch_(commands)
            blocks = bc.rpc.batch_([ [ "getblock", h ] for h in block_hashes ])
            block_times = [ block["time"] for block in blocks ]
            print(block_times)

            print('--------------------')

            for b in blocks:
                print("--------BLOCK--------")
                print(b)
                tx = b["tx"]
                #print(tx)
                try:

                    for i in range(len(tx)):
                        print("--------TRANSACTION--------")
                        rtx = bc.rpc.getrawtransaction(tx[i])
                        print(rtx)
                        decoded = bc.rpc.decoderawtransaction(rtx)
                        pp.pprint(decoded)
                except BaseException as be:
                    print(be)
                # print(type(rtx))
                print('--------')


        #------------------------------------------
        #------------------------------------------
        print("AFter Settle")

        print("ORACLE VALUE:", oracle1_val, "; oracle signature:", oracle1_sig)

        valueOurs = 0 
  

        valueOurs = env.lits[node_to_settle].rpc.GetContractDivision(CIdx=contract["Contract"]["Idx"],OracleValue=oracle1_val)['ValueOurs']
        valueTheirs = contract_funding_amt * 2 - valueOurs

        print("valueOurs:", valueOurs, "; valueTheirs:", valueTheirs)


        lit1_bal_after_settle = valueOurs - SetTxFeeOurs
        lit2_bal_after_settle = valueTheirs - SetTxFeeTheirs
        

        lit1_bal_after_claim = lit1_bal_after_settle - ClaimTxFeeOurs
        lit2_bal_after_claim = lit2_bal_after_settle - ClaimTxFeeTheirs

        lit1_bal_result = lit1_bal_after_claim  + lit1_bal_after_accept
        lit2_bal_result = lit2_bal_after_claim  + lit2_bal_after_accept

        print("============== Fees Calc ===========================")
        print("lit1_bal_after_settle", lit1_bal_after_settle)
        print("lit2_bal_after_settle", lit2_bal_after_settle)

        print("lit1_bal_after_claim",lit1_bal_after_claim)
        print("lit2_bal_after_claim",lit2_bal_after_claim)

        print("lit1_bal_result: ", lit1_bal_result)
        print("lit2_bal_result: ", lit2_bal_result)
        print("====================================================")



        bals1 = lit1.get_balance_info()  
        print('new lit1 balance:', bals1['TxoTotal'], 'in txos,', bals1['ChanTotal'], 'in chans')
        bal1sum = bals1['TxoTotal'] + bals1['ChanTotal']
        print(bals1)
        print('  = sum ', bal1sum)
        

        bals2 = lit2.get_balance_info()
        print('new lit2 balance:', bals2['TxoTotal'], 'in txos,', bals2['ChanTotal'], 'in chans')
        bal2sum = bals2['TxoTotal'] + bals2['ChanTotal']
        print(bals2)
        print('  = sum ', bal2sum)
        
        if node_to_settle == 0:
            assert bal1sum == lit1_bal_result, "The resulting lit1 node balance does not match." 
            assert bal2sum == lit2_bal_result, "The resulting lit2 node balance does not match." 
        elif node_to_settle == 1:
            assert bal1sum == lit2_bal_result, "The resulting lit1 node balance does not match." 
            assert bal2sum == lit1_bal_result, "The resulting lit2 node balance does not match." 




        #------------------------------------------
        if deb_mod:
            print("ADDRESSES AFTER SETTLE")
            print("LIT1 Addresses")
            print(pp.pprint(lit1.rpc.GetAddresses()))

            print("LIT2 Addresses")
            print(pp.pprint(lit2.rpc.GetAddresses()))

            print("bitcoind Addresses")
            print(pp.pprint(bc.rpc.listaddressgroupings()))
            #------------------------------------------   

    
    
            print("=====START CONTRACT N1=====")
            res = lit1.rpc.ListContracts()
            #print(pp.pprint(res))
            print(res)
            print("=====END CONTRACT N1=====")

            print("=====START CONTRACT N2=====")
            res = lit2.rpc.ListContracts()
            #print(pp.pprint(res))
            print(res)
            print("=====END CONTRACT N2=====")
        
        

    except BaseException as be:
        raise be  



def t_11_0(env):

    #-----------------------------
    # 1)Funding transaction.
    # Here can be a situation when peers have different number of inputs.

    # ::lit1:: BuildDlcFundingTransaction: qln/dlc.go: our_tx_vsize: 126
    # ::lit1:: BuildDlcFundingTransaction: qln/dlc.go: their_tx_vsize: 126
    # ::lit1:: BuildDlcFundingTransaction: qln/dlc.go: our_fee: 10080
    # ::lit1:: BuildDlcFundingTransaction: qln/dlc.go: their_fee: 10080

    # Vsize from Blockchain: 252

    # So we expect lit1, and lit2 balances equal to 89989920 !!!
    # 90000000 - 89989920 = 10080
    # But this is only when peers have one input each. What we expect.

    #-----------------------------
    # 2) SettlementTx vsize will be printed

    # ::lit0:: SettlementTx()1: qln/dlclib.go: --------------------: 
    # ::lit0:: SettlementTx()1: qln/dlclib.go: valueOurs: 18000000
    # ::lit0:: SettlementTx()1: qln/dlclib.go: valueTheirs: 2000000
    # ::lit0:: SettlementTx()1: qln/dlclib.go: --------------------: 
    # ::lit0:: SettlementTx()2: qln/dlclib.go: --------------------: 
    # ::lit0:: SettlementTx()2: qln/dlclib.go: valueOurs: 18000000
    # ::lit0:: SettlementTx()2: qln/dlclib.go: valueTheirs: 2000000
    # ::lit0:: SettlementTx()2: qln/dlclib.go: --------------------: 
    # ::lit0:: SettlementTx()3: qln/dlclib.go: --------------------: 
    # ::lit0:: SettlementTx()3: qln/dlclib.go: totalFee: 14400 
    # ::lit0:: SettlementTx()3: qln/dlclib.go: feeEach: 7200
    # ::lit0:: SettlementTx()3: qln/dlclib.go: feeOurs: 7200
    # ::lit0:: SettlementTx()3: qln/dlclib.go: feeTheirs: 7200
    # ::lit0:: SettlementTx()3: qln/dlclib.go: valueOurs: 17992800
    # ::lit0:: SettlementTx()3: qln/dlclib.go: valueTheirs: 1992800
    # ::lit0:: SettlementTx()3: qln/dlclib.go: vsize: 0   # Actually we have 14400/80 = 180
    # ::lit0:: SettlementTx()3: qln/dlclib.go: --------------------:     


    # Vsize from Blockchain: 181

    # There fore we expect here
    # valueOurs: 17992800 = 18000000 - 7200     !!!
    # valueTheirs: 1992800 = 2000000 - 7200     !!!


    #-----------------------------

    # 3) Claim TX in SettleContract 
    # Here the transaction vsize is always the same: 121


    # Vsize from Blockchain: 121

    #-----------------------------

    # 4) Claim TX from another peer
    # Here the transaction vsize is always the same: 110

    # Vsize from Blockchain: 110

    #-----------------------------

    # 17992800 - (121 * 80) = 17983120
    # 89989920 + 17983120 = 107973040

    # 1992800 - (110*80) = 1984000
    # 89989920 + 1984000 = 91973920

    #-----------------------------

    # AFter Settle
    # new lit1 balance: 107973040 in txos, 0 in chans
    #   = sum  107973040
    # {'CoinType': 257, 'SyncHeight': 514, 'ChanTotal': 0, 'TxoTotal': 107973040, 'MatureWitty': 107973040, 'FeeRate': 80}
    # new lit2 balance: 91973920 in txos, 0 in chans
    #   = sum  91973920

    #-----------------------------

    oracle_value = 11
    node_to_settle = 0

    valueFullyOurs=10
    valueFullyTheirs=20

    lit_funding_amt =      1     # 1 BTC
    contract_funding_amt = 10000000     # satoshi

    FundingTxVsize = 252
    SettlementTxVsize = 180

    SetTxFeeOurs = 7200
    SetTxFeeTheirs = 7200

    ClaimTxFeeOurs = 121 * 80
    ClaimTxFeeTheirs = 110 * 80


    feeperbyte = 80


    vsizes = [FundingTxVsize, SettlementTxVsize]

    params = [lit_funding_amt, contract_funding_amt, oracle_value, node_to_settle, valueFullyOurs, valueFullyTheirs, vsizes, feeperbyte, SetTxFeeOurs, SetTxFeeTheirs, ClaimTxFeeOurs, ClaimTxFeeTheirs]

    run_t(env, params)



# ====================================================================================
# ====================================================================================  


def t_1300_1(env):
    
    #-----------------------------
    # 1)Funding transaction.
    # Here can be a situation when peers have different number of inputs.

    # ::lit1:: BuildDlcFundingTransaction: qln/dlc.go: our_tx_vsize: 126
    # ::lit1:: BuildDlcFundingTransaction: qln/dlc.go: their_tx_vsize: 126
    # ::lit1:: BuildDlcFundingTransaction: qln/dlc.go: our_fee: 10080
    # ::lit1:: BuildDlcFundingTransaction: qln/dlc.go: their_fee: 10080

    # Vsize from Blockchain: 252

    # So we expect lit1, and lit2 balances equal to 89989920 !!!
    # 90000000 - 89989920 = 10080
    # But this is only when peers have one input each. What we expect.

    #-----------------------------
    # 2) SettlementTx vsize will be printed

    # ::lit1:: SettlementTx()1: qln/dlclib.go: --------------------:
    # ::lit1:: SettlementTx()1: qln/dlclib.go: valueOurs: 6000000 
    # ::lit1:: SettlementTx()1: qln/dlclib.go: valueTheirs: 14000000 
    # ::lit1:: SettlementTx()1: qln/dlclib.go: --------------------:
    # ::lit1:: SettlementTx()2: qln/dlclib.go: --------------------:
    # ::lit1:: SettlementTx()2: qln/dlclib.go: valueOurs: 5992800 
    # ::lit1:: SettlementTx()2: qln/dlclib.go: valueTheirs: 13992800 
    # ::lit1:: SettlementTx()2: qln/dlclib.go: --------------------:
    # ::lit1:: SettlementTx()2: qln/dlclib.go: --------------------:
    # ::lit1:: SettlementTx()2: qln/dlclib.go: totalFee: 14400 
    # ::lit1:: SettlementTx()2: qln/dlclib.go: feeEach: 7200 
    # ::lit1:: SettlementTx()2: qln/dlclib.go: feeOurs: 7200 
    # ::lit1:: SettlementTx()2: qln/dlclib.go: feeTheirs: 7200 
    # ::lit1:: SettlementTx()2: qln/dlclib.go: valueOurs: 5992800 
    # ::lit1:: SettlementTx()2: qln/dlclib.go: valueTheirs: 13992800 
    # ::lit1:: SettlementTx()2: qln/dlclib.go: vsize: 180 
    # ::lit1:: SettlementTx()2: qln/dlclib.go: --------------------:  


    # Vsize from Blockchain: 181

    # There fore we expect here
    # valueOurs: 5992800 = 6000000 - 7200     !!!
    # valueTheirs: 13992800 = 14000000 - 7200     !!!


    #-----------------------------

    # 3) Claim TX in SettleContract lit1
    # Here the transaction vsize is always the same: 121


    # Vsize from Blockchain: 121

    #-----------------------------

    # 4) Claim TX from another peer lit0
    # Here the transaction vsize is always the same: 110

    # Vsize from Blockchain: 110

    #-----------------------------

    # 5992800 - (121 * 80) = 5983120
    # 89989920 + 5983120 = 95973040

    # 13992800 - (110*80) = 13984000
    # 89989920 + 13984000 = 103973920

    #-----------------------------

    # AFter Settle
    # new lit1 balance: 103973920 in txos, 0 in chans
    #   = sum  103973920


    # new lit2 balance: 95973040 in txos, 0 in chans
    #   = sum  95973040

    #-----------------------------

    oracle_value = 1300
    node_to_settle = 1

    valueFullyOurs=1000
    valueFullyTheirs=2000

    lit_funding_amt =      1     # 1 BTC
    contract_funding_amt = 10000000     # satoshi

    FundingTxVsize = 252
    SettlementTxVsize = 180


    SetTxFeeOurs = 7200
    SetTxFeeTheirs = 7200

    ClaimTxFeeOurs = 121 * 80
    ClaimTxFeeTheirs = 110 * 80


    feeperbyte = 80


    vsizes = [FundingTxVsize, SettlementTxVsize]

    params = [lit_funding_amt, contract_funding_amt, oracle_value, node_to_settle, valueFullyOurs, valueFullyTheirs, vsizes, feeperbyte, SetTxFeeOurs, SetTxFeeTheirs, ClaimTxFeeOurs, ClaimTxFeeTheirs]

    run_t(env, params)



# ====================================================================================
# ====================================================================================  



def t_10_0(env):
    

    oracle_value = 10
    node_to_settle = 0

    valueFullyOurs=10
    valueFullyTheirs=20

    lit_funding_amt =      1     # 1 BTC
    contract_funding_amt = 10000000     # satoshi

    FundingTxVsize = 252
    SettlementTxVsize = 150

    SetTxFeeOurs = 150 * 80
    SetTxFeeTheirs = 0

    ClaimTxFeeOurs = 121 * 80
    ClaimTxFeeTheirs = 0


    feeperbyte = 80


    vsizes = [FundingTxVsize, SettlementTxVsize]

    params = [lit_funding_amt, contract_funding_amt, oracle_value, node_to_settle, valueFullyOurs, valueFullyTheirs, vsizes, feeperbyte, SetTxFeeOurs, SetTxFeeTheirs, ClaimTxFeeOurs, ClaimTxFeeTheirs]

    run_t(env, params)



# ====================================================================================
# ====================================================================================  



def t_10_1(env):
    

    oracle_value = 10
    node_to_settle = 1

    valueFullyOurs=10
    valueFullyTheirs=20

    lit_funding_amt =      1     # 1 BTC
    contract_funding_amt = 10000000     # satoshi

    FundingTxVsize = 252
    SettlementTxVsize = 137



    SetTxFeeOurs = 0
    SetTxFeeTheirs = 137 * 80

    ClaimTxFeeOurs = 0
    ClaimTxFeeTheirs = 110 * 80


    feeperbyte = 80


    vsizes = [FundingTxVsize, SettlementTxVsize]

    params = [lit_funding_amt, contract_funding_amt, oracle_value, node_to_settle, valueFullyOurs, valueFullyTheirs, vsizes, feeperbyte, SetTxFeeOurs, SetTxFeeTheirs, ClaimTxFeeOurs, ClaimTxFeeTheirs]

    run_t(env, params)



# ====================================================================================
# ====================================================================================  



def t_20_0(env):
    

    oracle_value = 20
    node_to_settle = 0

    valueFullyOurs=10
    valueFullyTheirs=20

    lit_funding_amt =      1     # 1 BTC
    contract_funding_amt = 10000000     # satoshi

    FundingTxVsize = 252
    SettlementTxVsize = 137

    SetTxFeeOurs = 0
    SetTxFeeTheirs = 137 * 80

    ClaimTxFeeOurs = 0
    ClaimTxFeeTheirs = 110 * 80


    feeperbyte = 80


    vsizes = [FundingTxVsize, SettlementTxVsize]

    params = [lit_funding_amt, contract_funding_amt, oracle_value, node_to_settle, valueFullyOurs, valueFullyTheirs, vsizes, feeperbyte, SetTxFeeOurs, SetTxFeeTheirs, ClaimTxFeeOurs, ClaimTxFeeTheirs]

    run_t(env, params)




# ====================================================================================
# ====================================================================================  



def t_20_1(env):
    

    oracle_value = 20
    node_to_settle = 1

    valueFullyOurs=10
    valueFullyTheirs=20

    lit_funding_amt =      1     # 1 BTC
    contract_funding_amt = 10000000     # satoshi

    FundingTxVsize = 252
    SettlementTxVsize = 150



    SetTxFeeOurs = 150 * 80
    SetTxFeeTheirs = 0

    ClaimTxFeeOurs = 121 * 80
    ClaimTxFeeTheirs = 0


    feeperbyte = 80


    vsizes = [FundingTxVsize, SettlementTxVsize]

    params = [lit_funding_amt, contract_funding_amt, oracle_value, node_to_settle, valueFullyOurs, valueFullyTheirs, vsizes, feeperbyte, SetTxFeeOurs, SetTxFeeTheirs, ClaimTxFeeOurs, ClaimTxFeeTheirs]

    run_t(env, params)
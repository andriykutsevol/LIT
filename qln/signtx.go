package qln

import (
	"bytes"
	"fmt"

	"os"

	"github.com/mit-dci/lit/btcutil/txscript"
	"github.com/mit-dci/lit/crypto/koblitz"
	"github.com/mit-dci/lit/lnutil"
	"github.com/mit-dci/lit/logging"
	"github.com/mit-dci/lit/sig64"
	"github.com/mit-dci/lit/wire"
)

// SignBreak signs YOUR tx, which you already have a sig for
func (nd *LitNode) SignBreakTx(q *Qchan) (*wire.MsgTx, error) {
	// TODO: we probably have to do something with the HTLCs here

	tx, _, _, err := q.BuildStateTxs(true)
	if err != nil {
		return nil, err
	}

	// make hash cache for this tx
	hCache := txscript.NewTxSigHashes(tx)


	fmt.Printf("::%s:: FundTxScript(): SignBreakTx(): qln/signtx.go: q.MyPub %x, q.TheirPub %x \n",os.Args[6][len(os.Args[6])-4:], q.MyPub, q.TheirPub)	

	// generate script preimage (keep track of key order)
	pre, swap, err := lnutil.FundTxScript(q.MyPub, q.TheirPub)
	if err != nil {
		return nil, err
	}		

	// get private signing key
	priv, err := nd.SubWallet[q.Coin()].GetPriv(q.KeyGen)
	if err != nil {
		return nil, err
	}
	// generate sig.
	mySig, err := txscript.RawTxInWitnessSignature(
		tx, hCache, 0, q.Value, pre, txscript.SigHashAll, priv)
	if err != nil {
		return nil, err
	}

	fmt.Printf("::%s:: SignBreakTx(): qln/signtx.go: txscript.RawTxInWitnessSignature sig %x \n",os.Args[6][len(os.Args[6])-4:], mySig)

	theirSig := sig64.SigDecompress(q.State.Sig)
	// put the sighash all byte on the end of their signature
	theirSig = append(theirSig, byte(txscript.SigHashAll))

	logging.Infof("made mysig: %x theirsig: %x\n", mySig, theirSig)
	// add sigs to the witness stack
	if swap {
		tx.TxIn[0].Witness = SpendMultiSigWitStack(pre, theirSig, mySig)
	} else {
		tx.TxIn[0].Witness = SpendMultiSigWitStack(pre, mySig, theirSig)
	}

	// save channel state as closed
	// Removed - this is already done in the calling function - and is killing
	// the ability to just print the TX.
	// q.CloseData.Closed = true
	// q.CloseData.CloseTxid = tx.TxHash()
	// err = nd.SaveQchanUtxoData(q)
	// if err != nil {
	//	return nil, err
	// }

	return tx, nil
}

// SignSimpleClose signs the given simpleClose tx, given the other signature
// Tx is modified in place.
func (nd *LitNode) SignSimpleClose(q *Qchan, tx *wire.MsgTx) ([64]byte, error) {

	fmt.Printf("::%s:: SignSimpleClose() lnutil.TxToString(tx) %x \n",os.Args[6][len(os.Args[6])-4:], lnutil.TxToString(tx))

	var sig [64]byte
	// make hash cache
	hCache := txscript.NewTxSigHashes(tx)

	fmt.Printf("::%s:: FundTxScript(): SignSimpleClose() qln/signtx.go q.MyPub %x, q.TheirPub %x \n",os.Args[6][len(os.Args[6])-4:], q.MyPub, q.TheirPub)

	// generate script preimage for signing (ignore key order)
	pre, _, err := lnutil.FundTxScript(q.MyPub, q.TheirPub)
	if err != nil {
		return sig, err
	}


	fmt.Printf("::%s:: SignSimpleClose() lnutil.TxToString(tx): GetPriv(q.KeyGen) Step[2] %d \n",os.Args[6][len(os.Args[6])-4:], q.KeyGen.Step[2])

	// get private signing key
	priv, err := nd.SubWallet[q.Coin()].GetPriv(q.KeyGen)
	if err != nil {
		return sig, err
	}
	// generate sig
	mySig, err := txscript.RawTxInWitnessSignature(
		tx, hCache, 0, q.Value, pre, txscript.SigHashAll, priv)
	if err != nil {
		return sig, err
	}

	fmt.Printf("::%s:: SignSimpleClose(): qln/signtx.go: txscript.RawTxInWitnessSignature sig %x \n",os.Args[6][len(os.Args[6])-4:], mySig)
	
	// truncate sig (last byte is sighash type, always sighashAll)
	mySig = mySig[:len(mySig)-1]
	return sig64.SigCompress(mySig)
}

// SignSettlementTx signs the given settlement tx based on the passed contract
// using the passed private key. Tx is modified in place.
func (nd *LitNode) SignSettlementTx(c *lnutil.DlcContract, tx *wire.MsgTx,
	priv *koblitz.PrivateKey) ([64]byte, error) {

	var sig [64]byte
	// make hash cache
	hCache := txscript.NewTxSigHashes(tx)

	fmt.Printf("::%s:: FundTxScript(): SignSettlementTx: qln/signtx.go c.OurFundMultisigPub %x, c.TheirFundMultisigPub %x \n",os.Args[6][len(os.Args[6])-4:], c.OurFundMultisigPub, c.TheirFundMultisigPub)	

	// generate script preimage for signing (ignore key order)
	pre, _, err := lnutil.FundTxScript(c.OurFundMultisigPub, c.TheirFundMultisigPub)
	

		
	if err != nil {
		return sig, err
	}
	// generate sig
	mySig, err := txscript.RawTxInWitnessSignature(
		tx, hCache, 0, c.TheirFundingAmount+c.OurFundingAmount,
		pre, txscript.SigHashAll, priv)

	if err != nil {
		return sig, err
	}

	fmt.Printf("::%s:: SignSettlementTx(): qln/signtx.go: txscript.RawTxInWitnessSignature sig %x \n",os.Args[6][len(os.Args[6])-4:], mySig)

	// truncate sig (last byte is sighash type, always sighashAll)
	mySig = mySig[:len(mySig)-1]
	return sig64.SigCompress(mySig)
}

// SignClaimTx signs the given claim tx based on the passed preimage and value
// using the passed private key. Tx is modified in place. timeout=false means
// it's a regular claim, timeout=true means we're claiming an output that has
// expired (for instance if someone) published the wrong settlement TX, we can
// claim this output back to our wallet after the timelock expired.
func (nd *LitNode) SignClaimTx(claimTx *wire.MsgTx, value int64, pre []byte,
	priv *koblitz.PrivateKey, timeout bool) error {

	// make hash cache
	hCache := txscript.NewTxSigHashes(claimTx)

	// generate sig
	mySig, err := txscript.RawTxInWitnessSignature(
		claimTx, hCache, 0, value, pre, txscript.SigHashAll, priv)
	if err != nil {
		return err
	}

	fmt.Printf("::%s:: SignState(): qln/signtx.go: txscript.RawTxInWitnessSignature sig %x \n",os.Args[6][len(os.Args[6])-4:], mySig)

	witStash := make([][]byte, 3)
	witStash[0] = mySig
	if timeout {
		witStash[1] = nil
	} else {
		witStash[1] = []byte{0x01}
	}
	witStash[2] = pre
	claimTx.TxIn[0].Witness = witStash
	return nil
}

// SignNextState generates your signature for their state.
func (nd *LitNode) SignState(q *Qchan) ([64]byte, [][64]byte, error) {
	var sig [64]byte

	fmt.Printf("::%s:: SignState(): qln/signtx.go \n",os.Args[6][len(os.Args[6])-4:])

	// make sure channel exists, and wallet is present on node
	if q == nil {
		return sig, nil, fmt.Errorf("SignState nil channel")
	}
	_, ok := nd.SubWallet[q.Coin()]
	if !ok {
		return sig, nil, fmt.Errorf("SignState no wallet for cointype %d", q.Coin())
	}
	// build transaction for next state
	commitmentTx, spendHTLCTxs, HTLCTxOuts, err := q.BuildStateTxs(false) // their tx, as I'm signing
	if err != nil {
		return sig, nil, err
	}

	logging.Infof("Signing state with Elk [%x] NextElk [%x] N2Elk [%x]\n", q.State.ElkPoint, q.State.NextElkPoint, q.State.N2ElkPoint)

	// make hash cache for this tx
	hCache := txscript.NewTxSigHashes(commitmentTx)


	fmt.Printf("::%s:: SignState()2: qln/signtx.go: hCache %+v \n",os.Args[6][len(os.Args[6])-4:], hCache)

	fmt.Printf("::%s:: FundTxScript(): SignState: qln/signtx.go q.MyPub %x, q.TheirPub %x \n",os.Args[6][len(os.Args[6])-4:], q.MyPub, q.TheirPub)

	// generate script preimage (ignore key order)
	pre, _, err := lnutil.FundTxScript(q.MyPub, q.TheirPub)
	if err != nil {
		return sig, nil, err
	}
		

	// get private signing key
	priv, err := nd.SubWallet[q.Coin()].GetPriv(q.KeyGen)
	if err != nil {
		return sig, nil, err
	}

	fmt.Printf("::%s:: FundTxScript(): SignState: qln/signtx.go GetPriv(q.KeyGen) Step[2] %d \n",os.Args[6][len(os.Args[6])-4:], q.KeyGen.Step[2])

	// generate sig.
	bigSig, err := txscript.RawTxInWitnessSignature(
		commitmentTx, hCache, 0, q.Value, pre, txscript.SigHashAll, priv)
	if err != nil {
		return sig, nil, err
	}

	fmt.Printf("::%s:: SignState(): qln/signtx.go: txscript.RawTxInWitnessSignature sig %x \n",os.Args[6][len(os.Args[6])-4:], bigSig)

	// truncate sig (last byte is sighash type, always sighashAll)
	bigSig = bigSig[:len(bigSig)-1]

	sig, err = sig64.SigCompress(bigSig)
	if err != nil {
		return sig, nil, err
	}

	fmt.Printf("::%s:: SignState(): qln/signtx.go: sig %x \n",os.Args[6][len(os.Args[6])-4:], sig)

	logging.Infof("____ sig creation for channel (%d,%d):\n", q.Peer(), q.Idx())
	logging.Infof("\tinput %s\n", commitmentTx.TxIn[0].PreviousOutPoint.String())
	for i, txout := range commitmentTx.TxOut {
		logging.Infof("\toutput %d: %x %d\n", i, txout.PkScript, txout.Value)
	}

	logging.Infof("\tstate %d myamt: %d theiramt: %d\n", q.State.StateIdx, q.State.MyAmt, q.Value-q.State.MyAmt)

	// Generate signatures for HTLC-success/failure transactions
	spendHTLCSigs := map[int][64]byte{}

	curElk, err := q.ElkSnd.AtIndex(q.State.StateIdx)
	if err != nil {
		return sig, nil, err
	}
	elkScalar := lnutil.ElkScalar(curElk)

	ep := lnutil.ElkPointFromHash(curElk)

	logging.Infof("Using elkpoint %x to sign HTLC txs", ep)

	for idx, h := range HTLCTxOuts {
		// Find out which vout this HTLC is in the commitment tx since BIP69
		// potentially reordered them
		var where uint32
		for i, o := range commitmentTx.TxOut {
			if bytes.Compare(o.PkScript, h.PkScript) == 0 {
				where = uint32(i)
				break
			}
		}

		var HTLCPrivBase *koblitz.PrivateKey
		if idx == len(q.State.HTLCs) {
			HTLCPrivBase, err = nd.SubWallet[q.Coin()].GetPriv(q.State.InProgHTLC.KeyGen)
		} else if idx == len(q.State.HTLCs)+1 {
			HTLCPrivBase, err = nd.SubWallet[q.Coin()].GetPriv(q.State.CollidingHTLC.KeyGen)
		} else {
			HTLCPrivBase, err = nd.SubWallet[q.Coin()].GetPriv(q.State.HTLCs[idx].KeyGen)
		}

		if err != nil {
			return sig, nil, err
		}

		HTLCPriv := lnutil.CombinePrivKeyWithBytes(HTLCPrivBase, elkScalar[:])

		// Find the tx we need to sign. (this would all be much easier if we
		// didn't use BIP69)
		var spendTx *wire.MsgTx
		var which int
		for i, t := range spendHTLCTxs {
			if t.TxIn[0].PreviousOutPoint.Index == where {
				spendTx = t
				which = i
				break
			}
		}

		hc := txscript.NewTxSigHashes(spendTx)
		var HTLCScript []byte

		if idx == len(q.State.HTLCs) {
			fmt.Printf("::%s:: SignState(): qln/signtx.go: idx == len(q.State.HTLCs) \n",os.Args[6][len(os.Args[6])-4:])
			HTLCScript, err = q.GenHTLCScript(*q.State.InProgHTLC, false)
		} else if idx == len(q.State.HTLCs)+1 {
			fmt.Printf("::%s:: SignState(): qln/signtx.go: idx == len(q.State.HTLCs)+1 \n",os.Args[6][len(os.Args[6])-4:])
			HTLCScript, err = q.GenHTLCScript(*q.State.CollidingHTLC, false)
		} else {
			fmt.Printf("::%s:: SignState(): qln/signtx.go: else \n",os.Args[6][len(os.Args[6])-4:])
			HTLCScript, err = q.GenHTLCScript(q.State.HTLCs[idx], false)
		}
		if err != nil {
			return sig, nil, err
		}

		HTLCparsed, err := txscript.ParseScript(HTLCScript)
		if err != nil {
			return sig, nil, err
		}

		fmt.Printf("::%s:: !Script SignState(): qln/signtx.go: HTLCparsed\n",os.Args[6][len(os.Args[6])-4:])

		for _, p := range HTLCparsed {
			fmt.Printf("::%s:: SignState(): qln/signtx.go: OpCode: %s \n",os.Args[6][len(os.Args[6])-4:], p.Print(false))
		}		

		spendHTLCHash := txscript.CalcWitnessSignatureHash(
			HTLCparsed, hc, txscript.SigHashAll, spendTx, 0, h.Value)

		logging.Infof("Signing HTLC hash: %x, with pubkey: %x", spendHTLCHash, HTLCPriv.PubKey().SerializeCompressed())

		fmt.Printf("::%s:: SignState(): qln/signtx.go: spendHTLCHashe %x, pubkey %x \n",os.Args[6][len(os.Args[6])-4:], spendHTLCHash, HTLCPriv.PubKey().SerializeCompressed())

		mySig, err := HTLCPriv.Sign(spendHTLCHash)
		if err != nil {
			return sig, nil, err
		}

		HTLCSig := mySig.Serialize()
		s, err := sig64.SigCompress(HTLCSig)
		if err != nil {
			return sig, nil, err
		}

		spendHTLCSigs[which] = s
	}

	// Get the sigs in the same order as the HTLCs in the tx
	var spendHTLCSigsArr [][64]byte
	for i := 0; i < len(spendHTLCSigs)+2; i++ {
		if s, ok := spendHTLCSigs[i]; ok {
			spendHTLCSigsArr = append(spendHTLCSigsArr, s)
		}
	}

	fmt.Printf("::%s:: SignState(): qln/signtx.go: RETURN: sig %x (from txscript.RawTxInWitnessSignature), spendHTLCSigsArr %x \n",os.Args[6][len(os.Args[6])-4:], sig, spendHTLCSigsArr)

	return sig, spendHTLCSigsArr, err
}

// VerifySig verifies their signature for your next state.
// it also saves the sig if it's good.
// do bool, error or just error?  Bad sig is an error I guess.
// for verifying signature, always use theirHAKDpub, so generate & populate within
// this function.
func (q *Qchan) VerifySigs(sig [64]byte, HTLCSigs [][64]byte) error {

	fmt.Printf("::%s:: VerifySigs(): qln/signtx.go \n",os.Args[6][len(os.Args[6])-4:])

	bigSig := sig64.SigDecompress(sig)
	// my tx when I'm verifying.
	commitmentTx, spendHTLCTxs, HTLCTxOuts, err := q.BuildStateTxs(true)
	if err != nil {
		return err
	}

	logging.Infof("Verifying signatures with Elk [%x] NextElk [%x] N2Elk [%x]\n", q.State.ElkPoint, q.State.NextElkPoint, q.State.N2ElkPoint)

	fmt.Printf("::%s:: FundTxScript(): VerifySigs: qln/signtx.go q.MyPub %x, q.TheirPub %x \n",os.Args[6][len(os.Args[6])-4:], q.MyPub, q.TheirPub)

	// generate fund output script preimage (ignore key order)
	pre, _, err := lnutil.FundTxScript(q.MyPub, q.TheirPub)
	if err != nil {
		return err
	}

	hCache := txscript.NewTxSigHashes(commitmentTx)

	parsed, err := txscript.ParseScript(pre)



	if err != nil {
		return err
	}
	// always sighash all
	hash := txscript.CalcWitnessSignatureHash(
		parsed, hCache, txscript.SigHashAll, commitmentTx, 0, q.Value)

	// sig is pre-truncated; last byte for sighashtype is always sighashAll
	pSig, err := koblitz.ParseDERSignature(bigSig, koblitz.S256())
	if err != nil {
		return err
	}
	theirPubKey, err := koblitz.ParsePubKey(q.TheirPub[:], koblitz.S256())
	if err != nil {
		return err
	}
	logging.Infof("____ sig verification for channel (%d,%d):\n", q.Peer(), q.Idx())
	logging.Infof("\tinput %s\n", commitmentTx.TxIn[0].PreviousOutPoint.String())
	for i, txout := range commitmentTx.TxOut {
		logging.Infof("\toutput %d: %x %d\n", i, txout.PkScript, txout.Value)
	}
	logging.Infof("\tstate %d myamt: %d theiramt: %d\n", q.State.StateIdx, q.State.MyAmt, q.Value-q.State.MyAmt)
	logging.Infof("\tsig: %x\n", sig)

	worked := pSig.Verify(hash, theirPubKey)
	if !worked {
		return fmt.Errorf("Invalid signature on chan %d state %d",
			q.Idx(), q.State.StateIdx)
	}

	// Verify HTLC-success/failure signatures

	if len(HTLCSigs) != len(spendHTLCTxs) {
		return fmt.Errorf("Wrong number of signatures provided for HTLCs in channel. Got %d expected %d.",
			len(HTLCSigs), len(spendHTLCTxs))
	}

	// Map HTLC index to signature index
	sigIndex := map[uint32]uint32{}

	logging.Infof("Using elkpoint %x to verify HTLC txs", q.State.NextElkPoint)

	for idx, h := range HTLCTxOuts {
		// Find out which vout this HTLC is in the commitment tx since BIP69
		// potentially reordered them
		var where uint32
		for i, o := range commitmentTx.TxOut {
			if bytes.Compare(o.PkScript, h.PkScript) == 0 {
				where = uint32(i)
				break
			}
		}

		// Find the tx we need to verify. (this would all be much easier if we
		// didn't use BIP69)
		var spendTx *wire.MsgTx
		var which int
		for i, t := range spendHTLCTxs {
			if t.TxIn[0].PreviousOutPoint.Index == where {
				spendTx = t
				which = i
				sigIndex[uint32(idx)] = uint32(which)
				break
			}
		}

		hc := txscript.NewTxSigHashes(spendTx)
		var HTLCScript []byte
		if idx == len(q.State.HTLCs) {
			HTLCScript, err = q.GenHTLCScript(*q.State.InProgHTLC, true)
		} else if idx == len(q.State.HTLCs)+1 {
			HTLCScript, err = q.GenHTLCScript(*q.State.CollidingHTLC, true)
		} else {
			HTLCScript, err = q.GenHTLCScript(q.State.HTLCs[idx], true)
		}
		if err != nil {
			return err
		}

		HTLCparsed, err := txscript.ParseScript(HTLCScript)
		if err != nil {
			return err
		}
		// always sighash all
		spendHTLCHash := txscript.CalcWitnessSignatureHash(
			HTLCparsed, hc, txscript.SigHashAll, spendTx, 0, h.Value)

		// sig is pre-truncated; last byte for sighashtype is always sighashAll
		HTLCSig, err := koblitz.ParseDERSignature(sig64.SigDecompress(HTLCSigs[which]), koblitz.S256())
		if err != nil {
			return err
		}

		var theirHTLCPub [33]byte
		if idx == len(q.State.HTLCs) {
			theirHTLCPub = lnutil.CombinePubs(q.State.InProgHTLC.TheirHTLCBase, q.State.NextElkPoint)
		} else if idx == len(q.State.HTLCs)+1 {
			theirHTLCPub = lnutil.CombinePubs(q.State.CollidingHTLC.TheirHTLCBase, q.State.NextElkPoint)
		} else {
			theirHTLCPub = lnutil.CombinePubs(q.State.HTLCs[idx].TheirHTLCBase, q.State.NextElkPoint)
		}

		theirHTLCPubKey, err := koblitz.ParsePubKey(theirHTLCPub[:], koblitz.S256())
		if err != nil {
			return err
		}

		logging.Infof("Verifying HTLC hash: %x, with pubkey: %x", spendHTLCHash, theirHTLCPub)

		sigValid := HTLCSig.Verify(spendHTLCHash, theirHTLCPubKey)
		if !sigValid {
			return fmt.Errorf("Invalid signature HTLC on chan %d state %d HTLC %d",
				q.Idx(), q.State.StateIdx, idx)
		}
	}

	// copy signature, overwriting old signature.
	q.State.Sig = sig

	// copy HTLC-success/failure signatures
	for i, s := range sigIndex {
		if int(i) == len(q.State.HTLCs) {
			q.State.InProgHTLC.Sig = HTLCSigs[s]
		} else if int(i) == len(q.State.HTLCs)+1 {
			q.State.CollidingHTLC.Sig = HTLCSigs[s]
		} else {
			q.State.HTLCs[i].Sig = HTLCSigs[s]
		}
	}

	return nil
}

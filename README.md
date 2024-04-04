## It is hardened version of https://github.com/mit-dci/lit repository.


**DLC negotiate contract. #471**
From the DLC whitepaper:
If both parties are online and agree, they may be able to negotiate 
an end to the contract based on the current price, rather than the future price.


**Dlc oracle fraud detection #468**

From the DLC whitepaper.

If Olivia attempts to publicly report two different prices (in order to assume the role of a counterparty 
in a contract and “win” the bet regardless of the true outcome), she will reveal her permanent private key, 
as well as the k value for the particular contract she attempted to double-report:
"checkoraclefraud 1"

Check for possible ofracle fraud. If Olivia herself is a counterparty to a contract (e.g. Alice is Olivia), 
she can cause it to execute in an arbitrary fashion withouth revealing her private key.
This is detectable, and the defrauded party Bob can provide a compact proof of the fraud so that all other 
users can stop using Olivia’s commitments and signatures:

```
publishedTX = lit2.rpc.GetLatestTx(CIdx=1)
msg = lit2.rpc.GetMessageFromTx(CIdx=1, Tx=str(publishedTX["Tx"]))

proofOfMsg = lit2.rpc.CompactProofOfMsg(
OracleValue=msg["OracleValue"],
ValueOurs=msg["ValueOurs"],
ValueTheirs=msg["ValueTheirs"],
OracleA=msg["OracleA"],
OracleR=msg["OracleR"],
TheirPayoutBase=msg["TheirPayoutBase"],
OurPayoutBase=msg["OurPayoutBase"], Tx=publishedTX["Tx"])
```


**DLC multiple oracles support added. #466**

DLC multiple oracles support added.


**DLC Refund Transaction Created. #465**

DLC Refund Transaction Created. #465

**DLC Subsystem. All the stuff below + Test + Add FeePerByte to the lit-af utility. #463**

Added tests for:

Writing tests for the subsystem.
Creating arbitrarily large contracts.
Bug fixing at the ends of the interval.
Calculate the transactions vsizes.
Bug fixing when the counterparty runs the contract.


**DLC Subsystem. Calculate Transactions virtual sizes. #462**

Calculate Transactions virtual sizes.

**DLC Subsystem. Contract settlement from counterparty works. #459**

This allows you to run a contract from another node. Not from that which offers the contract.

**DLC Subsystem. Fix bug at the edges of interval. #458**

his PR eliminates the bug when one of the participants wins nothing and the other gets everything. Or vice versa.

**https://github.com/mit-dci/lit/pull/457**

This PR is to avoid Noise Protocol message size limitation (64kb).
https://noiseprotocol.org/noise.html
(All Noise messages are less than or equal to 65535 bytes in length.)

I think that even with the optimization by 'Base and Exponent R values'
a contract can be larger than 64kb.


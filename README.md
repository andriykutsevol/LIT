# It is hardened version of https://github.com/mit-dci/lit repository.


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

"publishedTX = lit2.rpc.GetLatestTx(CIdx=1)"
"msg = lit2.rpc.GetMessageFromTx(CIdx=1, Tx=str(publishedTX["Tx"]))"

"proofOfMsg = lit2.rpc.CompactProofOfMsg(
OracleValue=msg["OracleValue"],
ValueOurs=msg["ValueOurs"],
ValueTheirs=msg["ValueTheirs"],
OracleA=msg["OracleA"],
OracleR=msg["OracleR"],
TheirPayoutBase=msg["TheirPayoutBase"],
OurPayoutBase=msg["OurPayoutBase"], Tx=publishedTX["Tx"])
"


**https://github.com/mit-dci/lit/pull/466**

DLC multiple oracles support added.

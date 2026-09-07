import sys
sys.path.append('.')
from transport.fec.fec_engine import BlockFEC

def test_fec():
    fec = BlockFEC(k=8, m=4)
    data = [bytes([i]*10) for i in range(1, 9)]
    parity = fec.encode(data)
    
    print("Python parity block 0:", parity[0].hex())

test_fec()

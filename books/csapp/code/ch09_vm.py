"""Read the fixed Figure 9.20 snapshot; unknown PTEs raise ValueError."""
import sys
PTE = [0x28, None, 0x33, 2, None, 0x16, None, None, 0x13, 0x17, 9, None, None, 0x2d, 0x11, 0xd]
TLB = [{9:13, 7:2}, {3:45}, {}, {3:13, 10:52}]
CACHE = {0:(0x19,[0x99,0x11,0x23,0x11]),2:(0x1b,[0,2,4,8]),4:(0x32,[0x43,0x6d,0x8f,9]),5:(13,[0x36,0x72,0xf0,0x1d]),7:(0x16,[0x11,0xc2,0xdf,3]),8:(0x24,[0x3a,0,0x51,0x89]),10:(0x2d,[0x93,0x15,0xda,0x3b]),13:(0x16,[4,0x96,0x34,0x15]),14:(0x13,[0x83,0x77,0x1b,0xd3])}
def translate(va):
    if not 0 <= va < 0x4000:
        raise ValueError('14-bit address required')
    vpn, vpo = divmod(va,64)
    tt, ti = divmod(vpn,4)
    hit = tt in TLB[ti]
    if not hit and vpn >= len(PTE):
        raise ValueError('PTE absent from snapshot')
    ppn = TLB[ti][tt] if hit else PTE[vpn]
    out = f'va={va:04x} vpn={vpn:02x} vpo={vpo:02x} tlbi={ti:x} tlbt={tt:02x} tlb={"Y" if hit else "N"}'
    if ppn is None:
        return out + ' fault=Y'
    pa = ppn*64+vpo
    ct, rest = divmod(pa,64)
    ci, co = divmod(rest,4)
    row = CACHE.get(ci)
    ch = row is not None and row[0] == ct
    out += f' fault=N pa={pa:03x} co={co:x} ci={ci:x} ct={ct:02x} cache={"Y" if ch else "N"}'
    if ch:
        out += f' byte={row[1][co]:02x}'
    return out
if __name__ == '__main__':
    try:
        if len(sys.argv) == 1:
            addresses = [0x3d7,0x27c,0x3a9,0x40]
        elif len(sys.argv) == 2 and sys.argv[1] and sys.argv[1][0] not in '+-' and all(c in '0123456789abcdefABCDEFxX' for c in sys.argv[1]):
            addresses = [int(sys.argv[1],16)]
        else:
            raise ValueError('one hexadecimal address expected')
        for address in addresses:
            print(translate(address))
    except ValueError:
        sys.exit(2)

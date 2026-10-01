"""Reproduce the two offline images; this script never accesses a device."""
import argparse
import hashlib
import struct
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('kind', choices=['aboot', 'recovery'])
parser.add_argument('source', type=Path)
parser.add_argument('output', type=Path)
args = parser.parse_args()
if args.source.resolve() == args.output.resolve():
    parser.error('Source and output must be different files.')
if args.output.exists():
    parser.error('Output already exists; choose a new path.')
data = args.source.read_bytes()
if args.kind == 'aboot':
    expected = '28a2f559b7c56c9565da334e21b78d5a94bf0179417d895faf0a2688a5ecbeb3'
    if hashlib.sha256(data).hexdigest() != expected:
        parser.error('Source is not the verified MIUI 11 santoni MBN.')
    result = data + bytes(1048576 - len(data))
else:
    expected = '50be6e05c0881fb65feca5fed614b3986c0057960f44df1117b05cd012f2a0be'
    if hashlib.sha256(data).hexdigest() != expected:
        parser.error('Source is not the verified original TWRP 3.6.2 image.')
    kernel, ramdisk, second, page, dt = [struct.unpack_from('<I', data, n)[0] for n in (8,16,24,36,40)]
    align = lambda n: (n + page - 1) // page * page
    end = page + sum(align(n) for n in (kernel,ramdisk,second,dt))
    if data[:8] != b'ANDROID!' or end != len(data):
        parser.error('Unexpected Android boot image layout.')
    result = data + bytes.fromhex('3083198964') + bytes(4091)
args.output.write_bytes(result)
print(f'{hashlib.sha256(result).hexdigest().upper()} *{args.output} ({len(result)} bytes)')

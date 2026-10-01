"""Append the tested santoni footer to a legacy v0 Android boot image, offline."""
import argparse
import hashlib
import struct
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('source', type=Path)
parser.add_argument('output', type=Path)
args = parser.parse_args()
if args.source.resolve() == args.output.resolve() or args.output.exists():
    parser.error('Choose a new output path; existing files are never overwritten.')
data = args.source.read_bytes()
if len(data) < 1632 or data[:8] != b'ANDROID!':
    parser.error('Not a complete Android boot header.')
page = struct.unpack_from('<I', data, 36)[0]
version = struct.unpack_from('<I', data, 40)[0]
if version != 0 or page not in (2048, 4096, 8192, 16384):
    parser.error('Only the tested v0 format without a legacy DT section is supported.')
sizes = [struct.unpack_from('<I', data, offset)[0] for offset in (8, 16, 24)]
end = page + sum((size + page - 1) // page * page for size in sizes)
if end > len(data):
    parser.error('Truncated image payload.')
footer = bytes.fromhex('3083198964') + bytes(4091)
tail = data[end:]
if tail != footer and any(tail):
    parser.error('Unknown nonzero trailing data; inspect it before changing the image.')
result = data[:end] + footer
args.output.write_bytes(result)
print(f'{hashlib.sha256(result).hexdigest()} *{args.output} ({len(result)} bytes)')

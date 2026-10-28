"""Remove superseded trailing literal blocks from the verified v31/256-byte layout.

Never relocates other metadata sections or edits a literal. Fails closed for any
other header layout, overlapping active sections, or non-trailing literal data.
"""
import struct

def compact_metadata_tail(data: bytes) -> bytes:
    if len(data)<256 or struct.unpack_from('<II',data)!=(0xFAB11BAF,31):
        raise ValueError('Expected IL2CPP metadata v31')
    sections={i:struct.unpack_from('<II',data,i) for i in range(8,256,8)}
    if sections[8][0]!=256:raise ValueError('Unexpected metadata header length')
    for off,size in sections.values():
        if off+size>len(data) or (size and off<256):raise ValueError('Invalid active section')
    offset,size=sections[16]
    end=max(off+length for key,(off,length) in sections.items() if key!=16)
    if offset<end or offset+size!=len(data):raise ValueError('Literal data is not a separate trailing section')
    end=(end+3)&~3
    if end>offset:raise ValueError('Insufficient alignment space')
    result=bytearray(data[:end]);result.extend(data[offset:offset+size])
    struct.pack_into('<I',result,16,end)
    # Every other active section, including name strings and literal lookup
    # indices, stays at its original offset with exactly its original bytes.
    for key,(off,length) in sections.items():
        if key!=16 and result[off:off+length]!=data[off:off+length]:
            raise AssertionError('Compaction changed an active section')
    return bytes(result)

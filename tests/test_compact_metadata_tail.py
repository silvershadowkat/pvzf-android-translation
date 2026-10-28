import struct,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from compact_metadata_tail import compact_metadata_tail

class CompactMetadataTests(unittest.TestCase):
    def fixture(self):
        b=bytearray(1024);struct.pack_into('<II',b,0,0xFAB11BAF,31)
        for i in range(8,256,8):struct.pack_into('<II',b,i,400,0)
        struct.pack_into('<II',b,8,256,8);struct.pack_into('<II',b,16,1000,24)
        struct.pack_into('<II',b,24,300,100);struct.pack_into('<II',b,256,24,0)
        b[300:400]=b'N'*100;b[400:1000]=b'X'*600;b[1000:]=b'English translation text'
        return bytes(b)
    def test_preserves_all_referenced_bytes(self):
        b=self.fixture();r=compact_metadata_tail(b)
        self.assertEqual(len(r),424);self.assertEqual(r[256:400],b[256:400]);self.assertEqual(r[400:],b[1000:])
        self.assertEqual(struct.unpack_from('<II',r,16),(400,24))
        self.assertEqual(compact_metadata_tail(r),r)
    def test_unknown_layout_rejected(self):
        b=bytearray(self.fixture());struct.pack_into('<I',b,4,29)
        with self.assertRaises(ValueError):compact_metadata_tail(b)
    def test_overlapping_or_nontrailing_rejected(self):
        b=bytearray(self.fixture());struct.pack_into('<II',b,24,990,20)
        with self.assertRaises(ValueError):compact_metadata_tail(b)
        with self.assertRaises(ValueError):compact_metadata_tail(self.fixture()+b'unknown')

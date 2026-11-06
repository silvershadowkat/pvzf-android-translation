import struct,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from runtime_apk import Pool,chunks,U32,application_bootstrap,APPLICATION

class ApplicationBootstrapTests(unittest.TestCase):
    def fixture(self,custom=None,settings=False):
        pool=Pool(struct.pack('<HHIIIIII',1,28,28,0,0,256,28,0))
        for s in ('manifest','application','activity','name','http://schemas.android.com/apk/res/android','com.unity3d.player.UnityPlayerActivity'):pool.add(s)
        if settings:pool.add('label');pool.add('debuggable')
        def attr(value,key=3):
            i=pool.add(value)
            return struct.pack('<IIIHBBI',4,key,i,8,0,3,i)
        def node(tag,attrs=b''):
            return struct.pack('<HHIIIIIHHHHHH',0x102,16,36+len(attrs),1,0xffffffff,0xffffffff,pool.add(tag),20,20,len(attrs)//20,0,0,0)+attrs
        attributes=(attr('Label',6)+attr('false',7)) if settings else b''
        app=node('application',attributes+(attr(custom) if custom else b''))
        activity=node('activity',attr('com.unity3d.player.UnityPlayerActivity'))
        ids=[0,0,0,0x01010003,0,0]+([0x01010001,0x0101000f] if settings else [])
        resource_map=struct.pack('<HHI',0x180,8,8+4*len(ids))+struct.pack('<'+'I'*len(ids),*ids)
        body=pool.encode()+resource_map+app+activity
        return struct.pack('<HHI',3,8,len(body)+8)+body
    def test_registers_application_without_renaming_unity_or_changing_indices(self):
        original=self.fixture();changed=application_bootstrap(original)
        before=list(chunks(original));after=list(chunks(changed))
        old_pool=Pool(before[0][3]);new_pool=Pool(after[0][3])
        self.assertEqual(new_pool.strings[:len(old_pool.strings)],old_pool.strings)
        self.assertEqual(before[3][3],after[3][3])
        app=after[2][3]
        self.assertEqual(struct.unpack_from('<H',app,28)[0],1)
        self.assertEqual(new_pool.strings[U32(app,52)],APPLICATION)
    def test_reapplying_does_not_duplicate_attributes(self):
        once=application_bootstrap(self.fixture())
        self.assertEqual(application_bootstrap(once),once)
    def test_unreviewed_existing_application_is_rejected(self):
        with self.assertRaisesRegex(AssertionError,'custom Application'):
            application_bootstrap(self.fixture('third.party.Application'))
    def test_android_typed_array_resource_id_order_is_preserved(self):
        changed=list(chunks(application_bootstrap(self.fixture(settings=True))))
        pool=Pool(changed[0][3]);resource_map=changed[1][3]
        ids=struct.unpack('<'+'I'*((len(resource_map)-8)//4),resource_map[8:])
        app=changed[2][3]
        self.assertEqual([ids[U32(app,36+20*i+4)] for i in range(3)],[0x01010001,0x01010003,0x0101000f])
        self.assertEqual(pool.strings[U32(app,36+20+16)],APPLICATION)

if __name__=='__main__':unittest.main()

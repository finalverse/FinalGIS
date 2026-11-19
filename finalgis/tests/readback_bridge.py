"""Check presentation admission without a model, public server or world writer."""
import importlib.util,json,pathlib,struct,sys,tempfile,unittest

spec=importlib.util.spec_from_file_location('bridge',pathlib.Path(__file__).parents[1]/'scripts/readback_scene.py')
bridge=importlib.util.module_from_spec(spec);spec.loader.exec_module(bridge)

def mesh():
    binary=struct.pack('<9f3I',0,0,0,1,0,0,0,0,1,0,1,2)
    doc={'asset':{'version':'2.0'},'meshes':[{'primitives':[{'attributes':{'POSITION':0},'indices':1,'material':0}]}],'materials':[{}]}
    raw=json.dumps(doc).encode();raw+=b' '*((-len(raw))%4)
    return struct.pack('<III',0x46546c67,2,28+len(raw)+len(binary))+struct.pack('<II',len(raw),0x4e4f534a)+raw+struct.pack('<II',len(binary),0x004e4942)+binary,binary

class Bridge(unittest.TestCase):
    def material(self):return {'base_color_factor':[0.2,0.3,0.4,1],'metallic_factor':0,'roughness_factor':0.8,'double_sided':True,'emissive_factor':[0,0,0]}
    def test_material_binding_preserves_every_binary_byte(self):
        raw,binary=mesh();derived,sha=bridge.bind_material(raw,self.material())
        self.assertNotEqual(raw,derived);self.assertTrue(derived.endswith(binary));self.assertEqual(sha,bridge.digest(binary))
        n=struct.unpack_from('<I',derived,12)[0];doc=json.loads(derived[20:20+n])
        self.assertEqual(doc['materials'][0]['pbrMetallicRoughness']['baseColorFactor'],[0.2,0.3,0.4,1])
    def test_profile_refuses_unimplemented_texture_binding(self):
        raw,_=mesh();m=self.material();m['base_color_texture']={'texture_id':'unknown'}
        with self.assertRaises(ValueError):bridge.bind_material(raw,m)
    def test_truncated_chunks_refused(self):
        raw,_=mesh()
        for broken in [raw[:12],raw[:-1],b'not GLB']:
            with self.assertRaises(ValueError):bridge.bind_material(broken,self.material())
    def test_remote_credentials_and_output_remain_untouched(self):
        with tempfile.TemporaryDirectory() as d:
            root=pathlib.Path(d);token=root/'token';token.write_text('private');out=root/'output'
            with self.assertRaises(ValueError):bridge.readback('https://example.com',token,'bad','bad','bad',root/'none','none',out)
            self.assertEqual(token.read_text(),'private');self.assertFalse(out.exists())

if __name__=='__main__':unittest.main()

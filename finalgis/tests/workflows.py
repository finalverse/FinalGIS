"""Execute the native binary; check real geometry, authority and replay boundaries."""
import json, os, pathlib, shutil, struct, subprocess, sys, tempfile, unittest

WORKER, SOURCE = sys.argv[1:3]
sys.argv = [sys.argv[0]]

class Workflows(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="finalgis-test-")
        self.root = pathlib.Path(self.tmp.name)
    def tearDown(self): self.tmp.cleanup()
    def call(self, *args, ok=True):
        p = subprocess.run([WORKER, *map(str, args)], capture_output=True, text=True, timeout=40)
        self.assertEqual(p.returncode == 0, ok, p.stderr)
        return json.loads(p.stdout) if p.returncode == 0 else p.stderr
    def recipe(self):
        p = self.call("plan", "--request", "Analyze public Montréal roads and buildings")
        path = self.root / "plan.json"; path.write_text(json.dumps(p)); return path
    def test_crs_axis_order_and_roundtrip(self):
        origin = [-73.55350350168884, 45.507201203216475, 0]
        xyz = self.call("transform", "--from", "EPSG:4326", "--to", "EPSG:2950", "--xyz", ",".join(map(str, origin)))["xyz"]
        self.assertAlmostEqual(xyz[0], 300619.334946641, places=5)
        self.assertAlmostEqual(xyz[1], 5040809.30754108, places=5)
        actual = self.call("transform", "--from", "EPSG:2950", "--to", "EPSG:4326", "--xyz", ",".join(map(str, xyz)))["xyz"]
        for a,b in zip(actual,origin): self.assertAlmostEqual(a,b,places=7)
        self.call("transform", "--from", "EPSG:4326", "--to", "EPSG:2950", "--xyz", "nan,45,0", ok=False)
        self.call("transform", "--from", "garbage", "--to", "EPSG:2950", "--xyz", "0,0,0", ok=False)
        self.call("transform", "--from", "https://127.0.0.1:9/crs", "--to", "EPSG:2950", "--xyz", "0,0,0", ok=False)
        self.call("transform", "--from", "/etc/passwd", "--to", "EPSG:2950", "--xyz", "0,0,0", ok=False)
    def test_native_replay_and_real_source(self):
        outputs=[]
        for i in range(2):
            out=self.root/str(i)
            r=self.call("run","--source",SOURCE,"--output",out,"--plan",self.recipe(),"--approve")
            self.assertEqual(r["dataset"]["buildings"],45)
            self.assertEqual(r["included_building_proxies"],17)
            self.assertEqual(r["buffered_road_segments"],41)
            self.assertGreater(r["asset"]["triangles"],4000)
            outputs.append((out/"scene.glb").read_bytes())
        self.assertEqual(*outputs)
        self.call("run","--source",SOURCE,"--output",self.root/"0","--plan",self.recipe(),"--approve",ok=False)
    def test_source_integrity_and_symlinks(self):
        copy=self.root/"source";shutil.copytree(SOURCE,copy)
        (copy/"roads.geojson").write_bytes(b'{}')
        self.call("inspect","--source",copy,ok=False)
        (copy/"roads.geojson").unlink();(copy/"roads.geojson").symlink_to(pathlib.Path(SOURCE)/"roads.geojson")
        self.call("inspect","--source",copy,ok=False)
    def test_plan_review_and_tool_permissions(self):
        path=self.recipe();out=self.root/"output"
        self.call("run","--source",SOURCE,"--output",out,"--plan",path,ok=False)
        for mutation in ["shell", "publish_world", "clip_project"]:
            data=json.loads(path.read_text());data["operations"][0]["tool"]=mutation;path.write_text(json.dumps(data))
            self.call("run","--source",SOURCE,"--output",out,"--plan",path,"--approve",ok=False)
            path=self.recipe()
        self.assertFalse(out.exists())
    def test_model_failure_fallback_and_network_denial(self):
        r=self.call("plan","--request","Montréal streets","--provider","ollama","--endpoint","http://127.0.0.1:9")
        self.assertEqual(r["planning"]["outcome"],"deterministic_fallback")
        self.call("plan","--request","Montréal","--provider","openai","--endpoint","https://example.com/v1",ok=False)
        self.call("plan","--request","Montréal","--provider","ollama","--endpoint","http://127.0.0.1@evil.example",ok=False)
    def test_fictional_seed_replay_and_binary_validation(self):
        a=self.call("fiction","--output",self.root/"a","--seed","42","--approve")
        b=self.call("fiction","--output",self.root/"b","--seed","42","--approve")
        c=self.call("fiction","--output",self.root/"c","--seed","43","--approve")
        self.assertEqual(a["asset"]["sha256"],b["asset"]["sha256"])
        self.assertNotEqual(a["asset"]["sha256"],c["asset"]["sha256"])
        data=bytearray((self.root/"a/scene.glb").read_bytes());struct.pack_into('<I',data,8,1)
        broken=self.root/"broken.glb";broken.write_bytes(data)
        self.call("validate","--asset",broken,ok=False)
        self.call("fiction","--output",self.root/"d","--seed","-1","--approve",ok=False)

if __name__ == '__main__': unittest.main()

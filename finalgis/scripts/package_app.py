#!/usr/bin/env python3
"""Package an isolated FinalGIS product launcher and QGIS profile, never patch QGIS."""
import argparse,json,pathlib,plistlib,shutil,stat
def main():
 p=argparse.ArgumentParser();p.add_argument('--qgis',required=True);p.add_argument('--worker',required=True);p.add_argument('--source',required=True);p.add_argument('--output',required=True);p.add_argument('--profile',required=True);a=p.parse_args()
 product=pathlib.Path(__file__).resolve().parents[1];app=pathlib.Path(a.output).resolve();profile=pathlib.Path(a.profile).resolve()
 if app.exists():raise ValueError('New app destination required')
 qgis=pathlib.Path(a.qgis).resolve();info=plistlib.loads((qgis/'Contents/Info.plist').read_bytes());exe=qgis/'Contents/MacOS'/info['CFBundleExecutable']
 if not exe.is_file() or not pathlib.Path(a.worker).is_file():raise ValueError('QGIS app and built native worker required')
 plugins=profile/'profiles/FinalGIS/python/plugins/finalgis';plugins.parent.mkdir(parents=True,exist_ok=True);shutil.copytree(product/'plugin',plugins)
 settings=profile/'profiles/FinalGIS/qgis.org';settings.mkdir(parents=True,exist_ok=True)
 (settings/'QGIS3.ini').write_text('[PythonPlugins]\nfinalgis=true\nprocessing=true\n')
 config=profile/'finalgis-config.json';config.write_text(json.dumps({'worker':str(pathlib.Path(a.worker).resolve()),'source':str(pathlib.Path(a.source).resolve()),'outputs':str(profile/'exports')}))
 resources=app/'Contents/Resources';resources.mkdir(parents=True);mac=app/'Contents/MacOS';mac.mkdir()
 plist={'CFBundleName':'FinalGIS','CFBundleDisplayName':'FinalGIS','CFBundleIdentifier':'org.finalverse.finalgis','CFBundleShortVersionString':'0.1.0','CFBundleVersion':'1','CFBundleExecutable':'FinalGIS','CFBundlePackageType':'APPL','CFBundleIconFile':'FinalGIS.icns','NSHighResolutionCapable':True,'NSHumanReadableCopyright':'FinalGIS © Finalverse. QGIS © QGIS contributors, GPL-2.0-or-later.'}
 (app/'Contents/Info.plist').write_bytes(plistlib.dumps(plist));shutil.copy2(product/'plugin/logo.svg',resources/'FinalGIS.svg')
 icon=product/'branding/FinalGIS.icns'
 if icon.exists():shutil.copy2(icon,resources/'FinalGIS.icns')
 import shlex
 script='#!/bin/sh\nexport FINALGIS_CONFIG='+shlex.quote(str(config))+'\nexport PROJ_NETWORK=OFF\nexec '+shlex.quote(str(exe))+' --profiles-path '+shlex.quote(str(profile))+' --profile FinalGIS --nologo "$@"\n'
 launcher=mac/'FinalGIS';launcher.write_text(script);launcher.chmod(0o755)
 print(json.dumps({'application':str(app),'qgis':str(qgis),'profile':str(profile),'foundation_patched':False}))
if __name__=='__main__':main()

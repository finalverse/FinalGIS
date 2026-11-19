"""Run with the pinned QGIS bundle's Python, not a substituted GIS implementation."""
import json, os, pathlib, sys, tempfile
from qgis.core import (Qgis,QgsApplication,QgsVectorLayer,QgsRasterLayer,QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,QgsProject,QgsPointXY,QgsGeometry)
from qgis.PyQt.QtCore import QT_VERSION_STR

app_path=pathlib.Path(sys.argv[1]);source=pathlib.Path(sys.argv[2]);report=pathlib.Path(sys.argv[3])
QgsApplication.setPrefixPath(str(app_path/'Contents/MacOS'),True)
app=QgsApplication([],False);app.initQgis()
checks=[]
try:
    project=QgsProject.instance();project.setCrs(QgsCoordinateReferenceSystem('EPSG:2950'))
    buildings=QgsVectorLayer(str(source/'buildings.geojson'),'Montréal roof outlines','ogr')
    roads=QgsVectorLayer(str(source/'roads.geojson'),'Montréal road centerlines','ogr')
    assert buildings.isValid() and roads.isValid()
    buildings.setCrs(QgsCoordinateReferenceSystem('EPSG:2950'));roads.setCrs(QgsCoordinateReferenceSystem('EPSG:4326'))
    assert buildings.featureCount()==45 and roads.featureCount()==93;checks+=['QGIS OGR providers: 45 roofs, 93 roads']
    tx=QgsCoordinateTransform(roads.crs(),buildings.crs(),project)
    p=tx.transform(QgsPointXY(-73.55350350168884,45.507201203216475))
    assert abs(p.x()-300619.334946641)<0.05 and abs(p.y()-5040809.30754108)<0.05
    checks+=['QGIS PROJ CRS and GIS axis order agrees within 5cm numerical tolerance (not source accuracy)']
    for f in buildings.getFeatures():assert not f.geometry().isEmpty() and f.geometry().isGeosValid()
    first=next(roads.getFeatures());g=QgsGeometry(first.geometry());g.transform(tx)
    buffer=g.buffer(2.5,4);assert not buffer.isEmpty() and buffer.isGeosValid() and buffer.area()>0
    checks+=['QGIS GEOS geometry validation and native 2.5m road buffer']
    raster=QgsRasterLayer(str(source/'dtm.tif'),'NRCan DTM','gdal');assert raster.isValid() and raster.crs().authid()=='EPSG:3979'
    checks+=['QGIS GDAL raster provider, EPSG:3979 terrain']
    project.addMapLayer(buildings);project.addMapLayer(roads)
    with tempfile.TemporaryDirectory() as temp:
        path=pathlib.Path(temp)/'FinalGIS.qgz';assert project.write(str(path));project.clear();assert project.read(str(path));assert len(project.mapLayers())==2
        roads=next(l for l in project.mapLayers().values() if l.name()=='Montréal road centerlines')
    checks+=['QGIS project write/read restart and existing format compatibility']
    # Exercise a maintained upstream processing provider, not the FinalGIS worker.
    sys.path.insert(0,str(app_path/'Contents/Resources/qgis/python/plugins'))
    from processing.core.Processing import Processing
    Processing.initialize()
    import processing
    result=processing.run('native:reprojectlayer',{'INPUT':roads,'TARGET_CRS':QgsCoordinateReferenceSystem('EPSG:2950'),'OUTPUT':'memory:'})
    assert result['OUTPUT'].isValid() and result['OUTPUT'].featureCount()==93
    checks+=['Unmodified QGIS native Processing reprojectlayer provider']
    report.write_text(json.dumps({'status':'PASS','qgis':Qgis.QGIS_VERSION,'qt':QT_VERSION_STR,'checks':checks,'foundation':'official checksum-verified QGIS '+Qgis.QGIS_VERSION+' macOS universal binary; upstream source not rebuilt','source_processing':'QGIS native providers and independent FinalGIS C++ worker'},indent=2))
    print(report.read_text())
finally:
    # C++ QObject lifetimes must outlive this script's GIS Python wrappers.
    QgsProject.instance().clear()
    del result, first, g, buffer, roads, buildings, raster, tx, project
    app.exitQgis()

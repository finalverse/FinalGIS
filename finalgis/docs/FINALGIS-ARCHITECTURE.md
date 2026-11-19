# FinalGIS architecture

FinalGIS0.1 is a separately maintained product layer over QGIS. The inherited QGIS tree remains untouched. Its supported PyQGIS extension owns the workflow workspace; its separate C++20 worker owns deterministic GDAL/PROJ/GEOS execution and exports a C17 transform ABI. QGIS retains professional providers, Processing, raster/vector, project formats and plugin interfaces. No QGIS implementation code enters Core/Storm/SpatialDB. No upstream submissions are made.

Flow: intent → optional model recipe selection → strict reviewed plan → native source-integrity/CRS/geometry operations → static GLB → canonical Core FWD → reviewed Cloud Forge validation → existing SpatialDB authored compiler/seal/import → Storm native Metal presentation. MutSea state and WorldLine commits remain separate authority gates. A receipt is not permission to mutate a world.

The application modes are Professional GIS and World Engineering, with buttons and Command-Option1/2 shortcuts on macOS. Worker execution uses QProcess outside the GUI thread. Cancel kills that owned child; a60s frontend deadline bounds stalled work. Output is a new directory; partial directories are never published or overwritten. Model code, shell and filesystem paths never become agent tools. Workflow receipts are artifacts, not another SpatialDB or resident memory store.

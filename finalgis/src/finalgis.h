// SPDX-License-Identifier: GPL-2.0-or-later
// Copyright (c) 2026 Finalverse contributors.
#ifndef FINALGIS_H
#define FINALGIS_H
#include <stddef.h>
#ifdef __cplusplus
extern "C" {
#endif
/* Native GDAL/PROJ execution. Traditional GIS x,y order, finite doubles only.
 * Errors return 0 and write a terminated message into the caller's buffer. */
int fgis_transform(const char *source_crs, const char *target_crs,
                   double xyz[3], char *error, size_t error_capacity);
const char *fgis_version(void);
#ifdef __cplusplus
}
#endif
#endif

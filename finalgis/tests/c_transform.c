/* SPDX-License-Identifier: GPL-2.0-or-later */
#include "finalgis.h"
#include <math.h>
#include <string.h>
int main(void) {
 double p[3]={-73.55350350168884,45.507201203216475,0};char error[32]={0};
 if(strcmp(fgis_version(),"0.1.0"))return 1;
 if(!fgis_transform("EPSG:4326","EPSG:2950",p,error,sizeof(error)))return 2;
 if(fabs(p[0]-300619.334946641)>0.001||fabs(p[1]-5040809.30754108)>0.001)return 3;
 p[0]=NAN;
 if(fgis_transform("EPSG:4326","EPSG:2950",p,error,sizeof(error)))return 4;
 if(error[31]!=0||error[0]==0)return 5;
 if(fgis_transform(NULL,"EPSG:2950",p,NULL,0))return 6;
 return 0;
}

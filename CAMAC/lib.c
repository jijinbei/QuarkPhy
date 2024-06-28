#include <stdio.h>
#include <stdlib.h>
#include "camdrv.h"
#include "toyocamac.h"
#include <time.h>

void clear_camac_data(int stationNo, int address, int data)
{
    int function = 9;
    result = camac_24(stationNo, address, function, &data);
}
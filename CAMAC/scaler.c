#include <stdio.h>
#include <stdlib.h>
#include "camdrv.h"
#include "toyocamac.h"
#include <time.h>

void handleError(const char *errorMessage)
{
    fprintf(stderr, "%s\n", errorMessage);
    exit(EXIT_FAILURE);
}

void clear_camac_data(int stationNo, int address)
{
    int function = 9;
    int data = 0;
    int result = camac_24(stationNo, address, function, &data);
    if (result != 0)
    {
        printf("station: No%d\n", stationNo);
        printf("address: %d\n", address);
        handleError("Failed to clear CAMAC data.");
    }
}

void read_camac_data(int stationNo, int address, int *data)
{
    int function = 0;
    int result = camac_24(stationNo, address, function, data); // 24bit転送
    if (result != 0)
    {
        printf("station: No%d\n", stationNo);
        printf("address: %d\n", address);
        handleError("Failed to read CAMAC data.");
    }
}

int main(int argc, char *argv[])
{
    int n = 2; // Station number
    int reset_channel = 0;
    int count_address = 1;
    int lam;   // Look at Me
    FILE *fp;
    
    if (argc < 2)
    {
        handleError("Usage: ./scaler <number_of_events>");
    }

    const int nevent = atoi(argv[1]);
    if (nevent <= 0)
    {
        handleError("The number of events must be a positive integer.");
    }

    if (!(fp = fopen("CAMAC.dat", "w")))
    {
        handleError("File Open error!");
    }

    execz();
    setei();

    for (int i = 1; i <= nevent; i++)
    {
        lam = 0;
        int data = 0;

        clear_camac_data(n, reset_channel);
        clear_camac_data(n, count_address);

        while (lam == 0)
        {
            // 割り込み処理が発生するとlamの値が0以外になる
            read_camac_data(n, reset_channel, &lam);
        }

        read_camac_data(n, count_address, &data);
        printf("i = %d: data = %d\n", i, data);
        fprintf(fp, "%d\n", data);

        printf("\n");
    }

    fclose(fp);
    execc();
    return 0;
}

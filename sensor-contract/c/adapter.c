#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main(void) {
    char line[4096];
    if (!fgets(line, sizeof line, stdin)) return 2;
    line[strcspn(line, "\r\n")] = 0;
    char *fields[6] = {0};
    int count = 0;
    char *save = NULL;
    for (char *part = strtok_r(line, "\t", &save); part && count < 7;
         part = strtok_r(NULL, "\t", &save)) {
        if (count < 6) fields[count] = part;
        count++;
    }
    int ok = count == 6 && fields[0] && strcmp(fields[0], "APOLO1") == 0 &&
        fields[1] && *fields[1] && fields[2] && *fields[2] &&
        fields[3] && (strcmp(fields[3], "HOST_OS") == 0 || strcmp(fields[3], "PHYSICAL_INTERFACE") == 0) &&
        fields[4] && *fields[4] && fields[5] && *fields[5];
    if (ok) {
        char *end = NULL;
        unsigned long long timestamp = strtoull(fields[5], &end, 10);
        ok = end && *end == '\0' && timestamp > 0;
    }
    puts(ok ? "ACCEPTED" : "REJECTED");
    return ok ? 0 : 2;
}

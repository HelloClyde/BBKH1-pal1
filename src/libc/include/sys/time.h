#ifndef H1PAL_SYS_TIME_H
#define H1PAL_SYS_TIME_H

struct timeval {
    long tv_sec;
    long tv_usec;
};

struct timezone {
    int tz_minuteswest;
    int tz_dsttime;
};

#ifdef __cplusplus
extern "C" {
#endif
int gettimeofday(struct timeval *time_value, struct timezone *zone);

#ifdef __cplusplus
}
#endif

#endif

#ifndef RADAR_H
#define RADAR_H 

#include <bool.h>

/**
* Initialises the radar
* @returns false if setup fails, true if succeeds
*/
bool radar_setup();

/**
* Checks radar for any errors and prints an error message if so
* Must checked called before every call to get_distances and get_strengths
* @returns Error status, or 0 if no error
*/
int  radar_check_errors();

/**
* @param distances buffer in which distances will be stored
* @param nd        number of distances
*/
void get_distances(uint32_t *distances, int nd);

/**
* @param strengths buffer in which distances will be stored
* @param ns        number of strengths
*/
void get_strengths(int32_t *strengths, int ns);


#endif
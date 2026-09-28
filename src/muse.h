#pragma once

#include <NimBLEAdvertisedDevice.h>
#include <NimBLEDevice.h>


void muse_start();
void muse_stop();
void muse_init();

void muse_set_intensity(float intensity_percent);

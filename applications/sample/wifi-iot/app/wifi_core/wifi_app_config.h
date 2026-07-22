/*
 * Classroom Wi-Fi credentials — edit ONLY this file for SSID/password.
 * Do not put secrets in business .c files. Use a classroom AP, not home Wi-Fi.
 */
#ifndef WIFI_APP_CONFIG_H
#define WIFI_APP_CONFIG_H

#include "hi_wifi_api.h"

/* Lecturer-issued classroom hotspot (change per lab session) */
#ifndef WIFI_APP_SSID
#define WIFI_APP_SSID     "00"
#endif

#ifndef WIFI_APP_PASSWORD
#define WIFI_APP_PASSWORD "040906161231"
#endif

/* Must match the AP: open / WPA / WPA2-PSK */
#ifndef WIFI_APP_AUTH
#define WIFI_APP_AUTH     HI_WIFI_SECURITY_WPA2PSK
#endif

/* Optional scan before connect (1 = scan+print SSIDs, 0 = connect directly) */
#ifndef WIFI_APP_DO_SCAN
#define WIFI_APP_DO_SCAN  1
#endif

#endif /* WIFI_APP_CONFIG_H */

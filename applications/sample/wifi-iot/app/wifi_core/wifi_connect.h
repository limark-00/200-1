/*
 * wifi_core — reusable STA connect module for wifi-iot samples.
 * Business apps should only include this header; do not call hi_wifi_* directly.
 */
#ifndef WIFI_CONNECT_H
#define WIFI_CONNECT_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/**
 * Start STA, register events, optional scan, then connect using wifi_app_config.h.
 * Returns 0 on success (connect request issued), -1 on failure.
 * IP readiness is asynchronous — use WifiApp_WaitReady / WifiApp_IsReady.
 */
int WifiApp_StartSta(void);

/** Non-zero when associated and DHCP has yielded a non-zero IPv4 address. */
int WifiApp_IsReady(void);

/**
 * Block until WifiApp_IsReady() or timeout_ms elapses.
 * timeout_ms == 0 means wait forever.
 * Returns 0 if ready, -1 on timeout.
 */
int WifiApp_WaitReady(uint32_t timeout_ms);

/** Copy STA IPv4 string into buf; returns 0 on success, -1 if not ready. */
int WifiApp_GetIpString(char *buf, size_t len);

#ifdef __cplusplus
}
#endif

#endif /* WIFI_CONNECT_H */

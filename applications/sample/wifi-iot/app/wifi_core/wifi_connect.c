#include "wifi_connect.h"
#include "wifi_app_config.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#include "cmsis_os2.h"
#include "hi_wifi_api.h"
#include "securec.h"
#include "lwip/ip_addr.h"
#include "lwip/netifapi.h"

#define APP_INIT_VAP_NUM 2
#define APP_INIT_USR_NUM 2

/* Poll interval while waiting for IP (usleep unit: us) */
#define WIFI_APP_WAIT_SLICE_US 30000U

static struct netif *g_lwip_netif = NULL;
static volatile int g_wifi_ready = 0;
static int g_ip_printed = 0;

static void WifiApp_ResetAddr(struct netif *netif)
{
    ip4_addr_t gw;
    ip4_addr_t ipaddr;
    ip4_addr_t netmask;

    if (netif == NULL) {
        return;
    }

    IP4_ADDR(&gw, 0, 0, 0, 0);
    IP4_ADDR(&ipaddr, 0, 0, 0, 0);
    IP4_ADDR(&netmask, 0, 0, 0, 0);
    netifapi_netif_set_addr(netif, &ipaddr, &netmask, &gw);
}

/**
 * Read IPv4 via netifapi (same as wifi_lite HAL GetLocalWifiIp).
 * Do NOT pass &netif->ip_addr into ip4addr_ntoa — on this lwIP dual-stack
 * layout that can print garbage (e.g. 255.255.255.0 as "IP").
 */
static int WifiApp_FetchIpv4(ip4_addr_t *ip, ip4_addr_t *mask, ip4_addr_t *gw)
{
    if (g_lwip_netif == NULL || ip == NULL || mask == NULL || gw == NULL) {
        return -1;
    }
    if (netifapi_netif_get_addr(g_lwip_netif, ip, mask, gw) != 0) {
        return -1;
    }
    return 0;
}

static int WifiApp_Ipv4IsUsable(const ip4_addr_t *ip)
{
    u32_t addr;

    if (ip == NULL) {
        return 0;
    }
    addr = ip4_addr_get_u32(ip);
    /* 0.0.0.0 or 255.255.255.255 — not a usable STA address */
    if (addr == 0 || addr == 0xFFFFFFFFu) {
        return 0;
    }
    return 1;
}

static void WifiApp_PrintIpv4(const ip4_addr_t *ip, const ip4_addr_t *mask, const ip4_addr_t *gw)
{
    char ip_s[16];
    char gw_s[16];
    char mask_s[16];

    /* ip4addr_ntoa uses one static buffer — copy before next call */
    strncpy(ip_s, ip4addr_ntoa(ip), sizeof(ip_s) - 1);
    ip_s[sizeof(ip_s) - 1] = '\0';
    strncpy(gw_s, ip4addr_ntoa(gw), sizeof(gw_s) - 1);
    gw_s[sizeof(gw_s) - 1] = '\0';
    strncpy(mask_s, ip4addr_ntoa(mask), sizeof(mask_s) - 1);
    mask_s[sizeof(mask_s) - 1] = '\0';

    printf("STA IP: %s\n", ip_s);
    printf("STA Gateway: %s\n", gw_s);
    printf("STA Netmask: %s\n", mask_s);
}

static void WifiApp_EventCb(const hi_wifi_event *event)
{
    if (event == NULL) {
        return;
    }

    switch (event->event) {
        case HI_WIFI_EVT_SCAN_DONE:
            printf("WiFi: Scan results available\n");
            break;
        case HI_WIFI_EVT_CONNECTED:
            printf("WiFi: Connected, starting DHCP\n");
            g_wifi_ready = 0;
            g_ip_printed = 0;
            /* Do not block/osDelay here — WaitReady polls until DHCP finishes */
            netifapi_dhcp_start(g_lwip_netif);
            break;
        case HI_WIFI_EVT_DISCONNECTED:
            printf("WiFi: Disconnected\n");
            g_wifi_ready = 0;
            g_ip_printed = 0;
            netifapi_dhcp_stop(g_lwip_netif);
            WifiApp_ResetAddr(g_lwip_netif);
            break;
        case HI_WIFI_EVT_WPS_TIMEOUT:
            printf("WiFi: WPS timeout\n");
            break;
        default:
            break;
    }
}

static int WifiApp_DoConnect(void)
{
    hi_wifi_assoc_request assoc_req = {0};
    size_t ssid_len;
    size_t key_len;
    errno_t rc;
    int ret;

    ssid_len = strlen(WIFI_APP_SSID);
    if (ssid_len == 0 || ssid_len > HI_WIFI_MAX_SSID_LEN) {
        printf("WiFi: invalid SSID length\n");
        return -1;
    }
    rc = memcpy_s(assoc_req.ssid, HI_WIFI_MAX_SSID_LEN + 1, WIFI_APP_SSID, ssid_len);
    if (rc != EOK) {
        return -1;
    }

    assoc_req.auth = WIFI_APP_AUTH;

    key_len = strlen(WIFI_APP_PASSWORD);
    if (key_len > HI_WIFI_MAX_KEY_LEN) {
        printf("WiFi: invalid password length\n");
        return -1;
    }
    if (key_len > 0) {
        rc = memcpy_s(assoc_req.key, HI_WIFI_MAX_KEY_LEN + 1, WIFI_APP_PASSWORD, key_len);
        if (rc != EOK) {
            return -1;
        }
    }

    printf("WiFi: connecting SSID=\"%s\"\n", WIFI_APP_SSID);
    ret = hi_wifi_sta_connect(&assoc_req);
    if (ret != HISI_OK) {
        printf("WiFi: hi_wifi_sta_connect failed (%d)\n", ret);
        return -1;
    }
    return 0;
}

#if WIFI_APP_DO_SCAN
static int WifiApp_DoScan(void)
{
    unsigned int num = WIFI_SCAN_AP_LIMIT;
    hi_wifi_ap_info *results;
    int ret;
    unsigned int i;

    ret = hi_wifi_sta_scan();
    if (ret != HISI_OK) {
        printf("WiFi: scan start failed\n");
        return -1;
    }

    sleep(5);

    results = (hi_wifi_ap_info *)malloc(sizeof(hi_wifi_ap_info) * WIFI_SCAN_AP_LIMIT);
    if (results == NULL) {
        return -1;
    }

    ret = hi_wifi_sta_scan_results(results, &num);
    if (ret != HISI_OK) {
        free(results);
        return -1;
    }

    for (i = 0; (i < num) && (i < WIFI_SCAN_AP_LIMIT); i++) {
        printf("SSID: %s\n", results[i].ssid);
    }
    free(results);
    return 0;
}
#endif

int WifiApp_StartSta(void)
{
    char ifname[WIFI_IFNAME_MAX_SIZE + 1] = {0};
    int len = sizeof(ifname);
    int ret;

    g_wifi_ready = 0;

    (void)APP_INIT_VAP_NUM;
    (void)APP_INIT_USR_NUM;

    ret = hi_wifi_sta_start(ifname, &len);
    if (ret != HISI_OK) {
        printf("WiFi: hi_wifi_sta_start failed (%d)\n", ret);
        return -1;
    }

    ret = hi_wifi_register_event_callback(WifiApp_EventCb);
    if (ret != HISI_OK) {
        printf("WiFi: register event callback failed\n");
    }

    g_lwip_netif = netifapi_netif_find(ifname);
    if (g_lwip_netif == NULL) {
        printf("WiFi: get netif failed\n");
        return -1;
    }

#if WIFI_APP_DO_SCAN
    if (WifiApp_DoScan() != 0) {
        printf("WiFi: scan failed, still trying connect\n");
    }
#endif

    return WifiApp_DoConnect();
}

int WifiApp_IsReady(void)
{
    ip4_addr_t ip;
    ip4_addr_t mask;
    ip4_addr_t gw;

    if (WifiApp_FetchIpv4(&ip, &mask, &gw) != 0) {
        g_wifi_ready = 0;
        return 0;
    }
    if (!WifiApp_Ipv4IsUsable(&ip)) {
        g_wifi_ready = 0;
        return 0;
    }

    if (!g_ip_printed) {
        WifiApp_PrintIpv4(&ip, &mask, &gw);
        g_ip_printed = 1;
    }
    g_wifi_ready = 1;
    return 1;
}

int WifiApp_WaitReady(uint32_t timeout_ms)
{
    uint32_t elapsed = 0;

    while (!WifiApp_IsReady()) {
        if (timeout_ms != 0 && elapsed >= timeout_ms) {
            return -1;
        }
        usleep(WIFI_APP_WAIT_SLICE_US);
        elapsed += WIFI_APP_WAIT_SLICE_US / 1000U;
    }
    return 0;
}

int WifiApp_GetIpString(char *buf, size_t len)
{
    ip4_addr_t ip;
    ip4_addr_t mask;
    ip4_addr_t gw;
    const char *ip_str;

    if (buf == NULL || len == 0) {
        return -1;
    }
    if (WifiApp_FetchIpv4(&ip, &mask, &gw) != 0 || !WifiApp_Ipv4IsUsable(&ip)) {
        return -1;
    }

    ip_str = ip4addr_ntoa(&ip);
    if (ip_str == NULL) {
        return -1;
    }
    if (strlen(ip_str) + 1 > len) {
        return -1;
    }
    strncpy(buf, ip_str, len - 1);
    buf[len - 1] = '\0';
    return 0;
}

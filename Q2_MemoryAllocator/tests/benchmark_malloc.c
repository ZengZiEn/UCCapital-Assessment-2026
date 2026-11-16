/**
 * @file benchmark_malloc.c
 * @brief UC Capital 面試考題 — 題目二：標準 malloc/free vs. myMalloc/myFree 效能基準測試
 *        實際驗證效能提升幅度（爭取額外 +10% 加分）。
 *
 * 包含三大實測場景：
 * - 場景 1 (題目核心情境)：反覆配置與釋放 10,000 * sizeof(int) 共 1,000,000 次
 * - 場景 2 (批次高峰併發緩衝區)：每輪同時配置 64 個 10,000 * sizeof(int)，執行 10,000 輪 (共 640,000 次)
 * - 場景 3 (混合大小動態配置)：於 128B ~ 4096B 間變動大小交錯配置與釋放，共 500,000 次
 */

#include "my_malloc.h"
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>

#ifdef _WIN32
#include <windows.h>
static double get_time_ms(void) {
    LARGE_INTEGER freq, counter;
    QueryPerformanceFrequency(&freq);
    QueryPerformanceCounter(&counter);
    return (double)counter.QuadPart * 1000.0 / (double)freq.QuadPart;
}
#else
#include <time.h>
static double get_time_ms(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (double)ts.tv_sec * 1000.0 + (double)ts.tv_nsec / 1e6;
}
#endif

/* 全域 volatile 校驗和，防止編譯器開啟 /O2 最佳化時將記憶體分配與讀寫視為 Dead Code 消除 */
static volatile long long g_sink_checksum = 0;

/**
 * 場景 1：單一 10,000 * sizeof(int) 反覆配置、讀寫與釋放 (1,000,000 次)
 */
static void run_benchmark_scenario_1(void) {
    const int iterations = 1000000;
    const size_t target_bytes = 10000U * sizeof(int);

    printf("\n【場景 1：題目核心情境 — 單一 10,000 * sizeof(int) (40 KB) 反覆配置與釋放 %d 次】\n",
           iterations);

    /* A. 測試標準 C 庫 malloc / free */
    long long std_sum = 0;
    double t0 = get_time_ms();
    for (int i = 0; i < iterations; ++i) {
        int *ptr = (int *)malloc(target_bytes);
        if (ptr != NULL) {
            ptr[0] = i;
            ptr[5000] = i + 1;
            ptr[9999] = i + 2;
            std_sum += ptr[0] + ptr[5000] + ptr[9999];
            free(ptr);
        }
    }
    double std_ms = get_time_ms() - t0;

    /* B. 測試自訂 myMalloc / myFree */
    long long my_sum = 0;
    double t1 = get_time_ms();
    for (int i = 0; i < iterations; ++i) {
        int *ptr = (int *)myMalloc(target_bytes);
        if (ptr != NULL) {
            ptr[0] = i;
            ptr[5000] = i + 1;
            ptr[9999] = i + 2;
            my_sum += ptr[0] + ptr[5000] + ptr[9999];
            myFree(ptr);
        }
    }
    double my_ms = get_time_ms() - t1;

    g_sink_checksum += (std_sum ^ my_sum);
    double speedup = (my_ms > 0.0) ? (std_ms / my_ms) : 0.0;

    printf("  - 標準 C malloc/free 耗時 : %8.2f ms (吞吐量: %8.2f 萬次/秒)\n",
           std_ms, (iterations / 10000.0) / (std_ms / 1000.0));
    printf("  - 自訂 myMalloc/myFree 耗時: %8.2f ms (吞吐量: %8.2f 萬次/秒)\n",
           my_ms, (iterations / 10000.0) / (my_ms / 1000.0));
    printf("  => 效能加速倍率 (Speedup)  : %.2f 倍 (節省 %.1f%% 執行時間)\n",
           speedup, (1.0 - my_ms / std_ms) * 100.0);
}

/**
 * 場景 2：批次高峰配置 (每輪同時持有 64 個 10,000 * sizeof(int) 陣列，共 10,000 輪 = 640,000 次)
 */
static void run_benchmark_scenario_2(void) {
    const int rounds = 10000;
    const int batch_size = 64;
    const size_t target_bytes = 10000U * sizeof(int);
    int *ptrs[64];

    printf("\n【場景 2：批次高峰負載 — 同時配置 %d 個 10,000 * sizeof(int) 陣列 × %d 輪 (共 %d 次)】\n",
           batch_size, rounds, rounds * batch_size);

    /* A. 標準 C malloc / free */
    long long std_sum = 0;
    double t0 = get_time_ms();
    for (int r = 0; r < rounds; ++r) {
        for (int b = 0; b < batch_size; ++b) {
            ptrs[b] = (int *)malloc(target_bytes);
            ptrs[b][0] = r + b;
            ptrs[b][9999] = r ^ b;
            std_sum += ptrs[b][0] + ptrs[b][9999];
        }
        for (int b = 0; b < batch_size; ++b) {
            free(ptrs[b]);
        }
    }
    double std_ms = get_time_ms() - t0;

    /* B. 自訂 myMalloc / myFree */
    long long my_sum = 0;
    double t1 = get_time_ms();
    for (int r = 0; r < rounds; ++r) {
        for (int b = 0; b < batch_size; ++b) {
            ptrs[b] = (int *)myMalloc(target_bytes);
            ptrs[b][0] = r + b;
            ptrs[b][9999] = r ^ b;
            my_sum += ptrs[b][0] + ptrs[b][9999];
        }
        for (int b = 0; b < batch_size; ++b) {
            myFree(ptrs[b]);
        }
    }
    double my_ms = get_time_ms() - t1;

    g_sink_checksum += (std_sum ^ my_sum);
    double total_ops = (double)(rounds * batch_size);
    double speedup = (my_ms > 0.0) ? (std_ms / my_ms) : 0.0;

    printf("  - 標準 C malloc/free 耗時 : %8.2f ms (吞吐量: %8.2f 萬次/秒)\n",
           std_ms, (total_ops / 10000.0) / (std_ms / 1000.0));
    printf("  - 自訂 myMalloc/myFree 耗時: %8.2f ms (吞吐量: %8.2f 萬次/秒)\n",
           my_ms, (total_ops / 10000.0) / (my_ms / 1000.0));
    printf("  => 效能加速倍率 (Speedup)  : %.2f 倍 (節省 %.1f%% 執行時間)\n",
           speedup, (1.0 - my_ms / std_ms) * 100.0);
}

/**
 * 場景 3：通用 Arena 混合尺寸動態配置與雙向合併測試 (128B ~ 4096B，共 500,000 次)
 */
static void run_benchmark_scenario_3(void) {
    const int iterations = 500000;
    static const size_t sizes[8] = {128, 256, 512, 1024, 1536, 2048, 3072, 4096};

    printf("\n【場景 3：混合大小動態配置 — 128B ~ 4096B 不規則區塊配置與合併 %d 次】\n",
           iterations);

    long long std_sum = 0;
    double t0 = get_time_ms();
    for (int i = 0; i < iterations; ++i) {
        size_t sz = sizes[i & 7];
        int *p = (int *)malloc(sz);
        p[0] = i;
        p[(sz / sizeof(int)) - 1] = i;
        std_sum += p[0];
        free(p);
    }
    double std_ms = get_time_ms() - t0;

    long long my_sum = 0;
    double t1 = get_time_ms();
    for (int i = 0; i < iterations; ++i) {
        size_t sz = sizes[i & 7];
        int *p = (int *)myMalloc(sz);
        p[0] = i;
        p[(sz / sizeof(int)) - 1] = i;
        my_sum += p[0];
        myFree(p);
    }
    double my_ms = get_time_ms() - t1;

    g_sink_checksum += (std_sum ^ my_sum);
    double speedup = (my_ms > 0.0) ? (std_ms / my_ms) : 0.0;

    printf("  - 標準 C malloc/free 耗時 : %8.2f ms (吞吐量: %8.2f 萬次/秒)\n",
           std_ms, (iterations / 10000.0) / (std_ms / 1000.0));
    printf("  - 自訂 myMalloc/myFree 耗時: %8.2f ms (吞吐量: %8.2f 萬次/秒)\n",
           my_ms, (iterations / 10000.0) / (my_ms / 1000.0));
    printf("  => 效能加速倍率 (Speedup)  : %.2f 倍 (節省 %.1f%% 執行時間)\n",
           speedup, (1.0 - my_ms / std_ms) * 100.0);
}

int main(void) {
#ifdef _WIN32
    SetConsoleOutputCP(65001);
#endif
    printf("========================================================================\n");
    printf("   UC Capital 題目二：標準 malloc vs. myMalloc 實測效能基準測試套件\n");
    printf("========================================================================\n");

    myMallocInit(128, 8 * 1024 * 1024);

    run_benchmark_scenario_1();
    run_benchmark_scenario_2();
    run_benchmark_scenario_3();

    printf("\n");
    myMallocPrintStats();
    printf("  (防編譯器消除校驗碼 Checksum = %lld)\n", g_sink_checksum);
    printf("========================================================================\n");

    myMallocDestroy();
    return 0;
}


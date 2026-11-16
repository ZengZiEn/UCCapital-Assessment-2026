/**
 * @file test_my_malloc.c
 * @brief UC Capital 面試考題 — 題目二：myMalloc 完整單元測試套件
 *
 * 測試項目：
 * 1. 16-Byte 記憶體對齊與 10,000 * sizeof(int) 完整讀寫驗證
 * 2. Tier-1 Slab Pool LIFO 熱快取位址重用與溢位轉移至 Arena 測試
 * 3. Tier-2 通用 Arena 區塊分割 (Splitting) 與雙向合併 (Bi-directional Coalescing) 零碎片驗證
 * 4. myCalloc 自動清零與 myRealloc 原位擴展/跨區搬移驗證
 * 5. Tier-3 OS Fallback 超大區塊配置與回收驗證
 * 6. Double-Free (重複釋放) 與 NULL 指標安全防護驗證
 */

#include "my_malloc.h"
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

#ifdef _WIN32
#include <windows.h>
#endif

static void test_01_alignment_and_10000_ints(void) {
    printf("  [Test 01] 測試 10,000 * sizeof(int) 配置、16-Byte 對齊與資料完整性... ");
    myMallocInit(64, 4 * 1024 * 1024);

    int *arr = (int *)myMalloc(10000 * sizeof(int));
    assert(arr != NULL);
    assert(((uintptr_t)arr % MY_ALIGNMENT) == 0);

    for (int i = 0; i < 10000; ++i) {
        arr[i] = i ^ 0x5A5A5A5A;
    }
    for (int i = 0; i < 10000; ++i) {
        assert(arr[i] == (i ^ 0x5A5A5A5A));
    }

    myFree(arr);
    myMallocDestroy();
    printf("通過 (PASS)\n");
}

static void test_02_slab_lifo_cache_reuse_and_exhaustion(void) {
    printf("  [Test 02] 測試 Slab LIFO 熱快取位址重用與池滿自動轉移至 Arena... ");
    /* 刻意只配置 4 個 Slab Slots */
    myMallocInit(4, 2 * 1024 * 1024);

    void *p1 = myMalloc(10000 * sizeof(int));
    assert(p1 != NULL);
    myFree(p1);

    /* LIFO 特性：剛釋放的 p1 應立即在下一次配置時被重用 */
    void *p2 = myMalloc(10000 * sizeof(int));
    assert(p2 == p1);
    myFree(p2);

    /* 連續配置 6 個 40,000 Bytes：前 4 個命中 Slab，後 2 個應無縫轉由 Arena 配置 */
    void *blocks[6];
    for (int i = 0; i < 6; ++i) {
        blocks[i] = myMalloc(10000 * sizeof(int));
        assert(blocks[i] != NULL);
    }

    MyAllocatorStats st;
    myMallocGetStats(&st);
    assert(st.slab_free_slots == 0);
    assert(st.arena_hit_count == 2);

    for (int i = 0; i < 6; ++i) {
        myFree(blocks[i]);
    }
    myMallocGetStats(&st);
    assert(st.slab_free_slots == 4);
    assert(st.arena_used_bytes == 0);

    myMallocDestroy();
    printf("通過 (PASS)\n");
}

static void test_03_arena_splitting_and_bidirectional_coalescing(void) {
    printf("  [Test 03] 測試通用 Arena 區塊分割與釋放後雙向相鄰合併 (防碎裂化)... ");
    myMallocInit(8, 1024 * 1024);

    /* 配置 3 個小型相鄰區塊 (各 1024 Bytes，走 Tier-2 Arena) */
    void *a = myMalloc(1024);
    void *b = myMalloc(1024);
    void *c = myMalloc(1024);
    assert(a != NULL && b != NULL && c != NULL);

    /* 先釋放兩側 a 與 c，最後釋放中間的 b，觸發向左與向右雙向合併！ */
    myFree(a);
    myFree(c);
    myFree(b);

    MyAllocatorStats st;
    myMallocGetStats(&st);
    assert(st.arena_used_bytes == 0);
    assert(st.coalesce_merges >= 3); /* a+b, (a+b)+c, 以及與後方剩餘大區塊合併 */

    myMallocDestroy();
    printf("通過 (PASS)\n");
}

static void test_04_calloc_and_realloc(void) {
    printf("  [Test 04] 測試 myCalloc 自動清零與 myRealloc 擴展資料保留... ");
    myMallocInit(16, 2 * 1024 * 1024);

    int *zeros = (int *)myCalloc(500, sizeof(int));
    assert(zeros != NULL);
    for (int i = 0; i < 500; ++i) {
        assert(zeros[i] == 0);
        zeros[i] = i + 10;
    }

    /* 將 500 個 int 擴展為 10,000 個 int */
    int *expanded = (int *)myRealloc(zeros, 10000 * sizeof(int));
    assert(expanded != NULL);
    for (int i = 0; i < 500; ++i) {
        assert(expanded[i] == i + 10);
    }

    myFree(expanded);
    myMallocDestroy();
    printf("通過 (PASS)\n");
}

static void test_05_os_fallback_and_double_free_guard(void) {
    printf("  [Test 05] 測試超大區塊 OS Fallback 與 Double-Free 重複釋放攔截... ");
    myMallocInit(8, 1024 * 1024);

    /* 申請 4 MB 超大區塊，超過 1 MB Arena 上限，自動走 Tier-3 OS Fallback */
    void *huge = myMalloc(4 * 1024 * 1024);
    assert(huge != NULL);

    MyAllocatorStats st;
    myMallocGetStats(&st);
    assert(st.fallback_hit_count == 1);
    myFree(huge);

    /* 測試池內區塊之 Double-Free (重複釋放) 防護：應被安全攔截而不崩潰 */
    void *slab_blk = myMalloc(10000 * sizeof(int));
    assert(slab_blk != NULL);
    myFree(slab_blk);
    myFree(slab_blk); /* 故意重複釋放第二次 */
    myFree(NULL);

    myMallocGetStats(&st);
    assert(st.double_free_detections == 1);

    myMallocDestroy();
    printf("通過 (PASS)\n");
}

int main(void) {
#ifdef _WIN32
    SetConsoleOutputCP(65001);
#endif
    printf("========================================================================\n");
    printf("       UC Capital 題目二：myMalloc 單元測試套件 (Unit Test Suite)       \n");
    printf("========================================================================\n");

    test_01_alignment_and_10000_ints();
    test_02_slab_lifo_cache_reuse_and_exhaustion();
    test_03_arena_splitting_and_bidirectional_coalescing();
    test_04_calloc_and_realloc();
    test_05_os_fallback_and_double_free_guard();

    printf("------------------------------------------------------------------------\n");
    printf("  結果：全部 5 大項單元測試 100%% 通過！\n");
    printf("========================================================================\n");
    return 0;
}

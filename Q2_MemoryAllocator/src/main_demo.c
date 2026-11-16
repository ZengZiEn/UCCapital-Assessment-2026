/**
 * @file main_demo.c
 * @brief UC Capital 面試考題 — 題目二：主程式示範
 *        展示如何以 myMalloc() 與 myFree() 直接替換題目中的 malloc(10000 * sizeof(int)) 與 free()。
 */

#include "my_malloc.h"
#include <stdio.h>
#include <assert.h>

#ifdef _WIN32
#include <windows.h>
#endif

int main(void) {
#ifdef _WIN32
    SetConsoleOutputCP(65001);
#endif

    printf("========================================================================\n");
    printf("   UC Capital 面試考題 — 題目二：myMalloc() 動態記憶體管理示範主程式\n");
    printf("========================================================================\n\n");

    /* 1. 顯式初始化記憶體池（若省略此步，第一次呼叫 myMalloc 亦會自動初始化） */
    if (myMallocInit(128, 8 * 1024 * 1024) != 0) {
        fprintf(stderr, "記憶體池初始化失敗！\n");
        return 1;
    }

    /* 2. 完全對應考題投影片第 3 頁之使用方式：申請 10,000 個 int 的空間 */
    int *ptr = NULL;
    ptr = (int *)myMalloc(10000 * sizeof(int));
    assert(ptr != NULL);

    printf("[步驟 1] 成功透過 myMalloc(10000 * sizeof(int)) 取得記憶體位址: %p\n", (void *)ptr);
    printf("         位址 16-Byte 對齊檢查: ((uintptr_t)ptr %% 16) == %zu (0 代表完美對齊)\n",
           (size_t)((uintptr_t)ptr % 16U));

    /* 3. 對 10,000 個整數進行讀寫驗證 */
    long long sum = 0;
    for (int i = 0; i < 10000; ++i) {
        ptr[i] = i + 1;
        sum += ptr[i];
    }
    printf("[步驟 2] 寫入 1..10000 並驗證總和: %lld (預期值: 50005000)\n", sum);
    assert(sum == 50005000LL);

    /* 4. 當記憶體使用完畢，不再需要時，以 myFree() 將記憶體空間回收至熱快取池 */
    if (NULL != ptr) {
        myFree(ptr);
        ptr = NULL;
    }
    printf("[步驟 3] 已呼叫 myFree(ptr) 並將 ptr 設為 NULL，區塊已 O(1) 回收至 Slab 熱快取頂端。\n");

    /* 5. 再次申請 10,000 個 int，驗證 LIFO 熱快取重用 (Cache-Hot Reuse) */
    int *ptr2 = (int *)myMalloc(10000 * sizeof(int));
    printf("[步驟 4] 再次呼叫 myMalloc(10000 * sizeof(int)) 取得位址: %p (直接命中剛釋放的 L1/L2 熱快取區塊！)\n\n",
           (void *)ptr2);
    myFree(ptr2);

    /* 6. 印出記憶體池統計報表 */
    myMallocPrintStats();

    /* 7. 程式結束前釋放記憶體池 */
    myMallocDestroy();
    return 0;
}


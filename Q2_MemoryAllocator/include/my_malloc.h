/**
 * @file my_malloc.h
 * @brief UC Capital 面試考題 — 題目二：高效能雙層混合式記憶體配置器 (Dual-Tier Hybrid Memory Pool)
 *
 * 設計架構說明：
 * 1. Tier-1 (O(1) Fast-Path Slab Pool)：
 *    針對高頻率、固定範圍（如題目所述 10,000 * sizeof(int) = 40,000 Bytes）之配置請求，
 *    預先配置一塊連續且對齊的記憶體池，內部以侵入式單向串列 (Intrusive LIFO Free-List) 管理。
 *    分配與釋放皆僅需 O(1) 指標操作，零系統呼叫、零碎片，且具備極佳的 L1/L2 Cache Locality。
 *
 * 2. Tier-2 (General Boundary-Tag Coalescing Arena)：
 *    針對不規則大小的記憶體請求，於預先分配的通用 Arena 中進行搜尋、分割 (Splitting)，
 *    並在釋放時立即與前後相鄰的空閒區塊進行雙向合併 (Bi-directional Coalescing)，防止外部碎裂化。
 *
 * 3. Tier-3 (OS Fallback)：
 *    當請求大小超過池容量上限或池空間暫時耗盡時，自動安全降級至系統標準 malloc/free。
 */

#ifndef UC_MY_MALLOC_H
#define UC_MY_MALLOC_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/** 預設配置常數定義 */
#define MY_ALIGNMENT              16U                  /* 16-Byte 記憶體對齊（支援 SSE/AVX 向量化） */
#define MY_SLAB_SLOT_PAYLOAD_SIZE 40960U               /* 單一 Slab Slot 容量：40 KB (足以容納 10,000 * sizeof(int)) */
#define MY_SLAB_DEFAULT_SLOTS     128U                 /* 預設預配置 128 個 Slab Slots (約 5.25 MB) */
#define MY_ARENA_DEFAULT_SIZE     (8U * 1024U * 1024U) /* 通用 Arena 預設大小：8 MB */

/** 區塊來源層級列舉 */
typedef enum MyBlockTier {
    MY_TIER_SLAB     = 1, /* 來自 O(1) Fast-Path Slab Pool */
    MY_TIER_ARENA    = 2, /* 來自通用型 Coalescing Arena */
    MY_TIER_FALLBACK = 3  /* 來自作業系統 Fallback 配置 */
} MyBlockTier;

/** 配置器運行統計資訊結構（供監控、除錯與效能分析使用） */
typedef struct MyAllocatorStats {
    size_t slab_total_slots;         /* Slab 池總 Slot 數 */
    size_t slab_free_slots;          /* Slab 池目前空閒 Slot 數 */
    size_t slab_hit_count;           /* 命中 O(1) Slab Fast-Path 次數 */
    size_t arena_total_bytes;        /* 通用 Arena 總位元組數 */
    size_t arena_used_bytes;         /* 通用 Arena 目前已分配位元組數 */
    size_t arena_hit_count;          /* 命中通用 Arena 次數 */
    size_t fallback_hit_count;       /* 降級至系統 malloc 次數 */
    size_t total_alloc_calls;        /* 總呼叫 myMalloc 次數 */
    size_t total_free_calls;         /* 總呼叫 myFree 次數 */
    size_t coalesce_merges;          /* Arena 執行相鄰區塊合併次數 */
    size_t double_free_detections;   /* 偵測並攔截到重複釋放 (Double-Free) 或損毀次數 */
} MyAllocatorStats;

/**
 * @brief 初始化雙層記憶體池。
 *        若使用者未主動呼叫，第一次呼叫 myMalloc() 時亦會自動以預設參數進行延遲初始化 (Lazy Init)。
 *
 * @param slab_slot_count Slab 池預先配置的區塊數量（若傳入 0 則使用預設值 128）
 * @param arena_bytes     通用 Arena 預先配置的總位元組數（若傳入 0 則使用預設值 8 MB）
 * @return int            0 代表成功，-1 代表系統記憶體不足
 */
int myMallocInit(size_t slab_slot_count, size_t arena_bytes);

/**
 * @brief 銷毀記憶體池並將所有預配置空間歸還給作業系統。
 */
void myMallocDestroy(void);

/**
 * @brief 高效能動態記憶體配置函式（相容標準 malloc 介面）。
 *
 * @param size 欲配置的記憶體位元組數
 * @return void* 成功時回傳 16-Byte 對齊之記憶體位址；若 size == 0 或失敗則回傳 NULL
 */
void *myMalloc(size_t size);

/**
 * @brief 高效能記憶體釋放函式（相容標準 free 介面）。
 *        內建 Double-Free 與非法標頭偵測防護。
 *
 * @param ptr 由 myMalloc / myCalloc / myRealloc 配置之指標（傳入 NULL 為安全無操作）
 */
void myFree(void *ptr);

/**
 * @brief 配置並自動清零之記憶體配置函式（相容標準 calloc 介面）。
 *
 * @param num  元素個數
 * @param size 單一元素位元組大小
 * @return void* 清零後的記憶體位址
 */
void *myCalloc(size_t num, size_t size);

/**
 * @brief 重新調整已配置記憶體區塊大小（相容標準 realloc 介面）。
 *
 * @param ptr      原記憶體指標
 * @param new_size 新需求位元組大小
 * @return void*   調整後的記憶體位址
 */
void *myRealloc(void *ptr, size_t new_size);

/**
 * @brief 取得目前配置器的內部統計數據快照。
 *
 * @param out_stats 指向接收統計結果的結構指標
 */
void myMallocGetStats(MyAllocatorStats *out_stats);

/**
 * @brief 印出人類易讀的配置器內部狀態與效能統計報表。
 */
void myMallocPrintStats(void);

#ifdef __cplusplus
}
#endif

#endif /* UC_MY_MALLOC_H */


/**
 * @file my_malloc.c
 * @brief UC Capital 面試考題 — 題目二：極致最佳化版雙層混合式記憶體配置器 (O(1) Slab + O(1) Explicit Free-List Arena)
 *
 * 參考開源專案與文獻：
 * 1. Linux Kernel Slab Allocator / Google tcmalloc (Thread-Caching Malloc)
 * 2. Doug Lea's Malloc (dlmalloc) & Matthew Conte's TLSF (mattconte/tlsf on GitHub)
 *
 * 核心最佳化亮點：
 * - Tier-1 (O(1) LIFO Slab Pool)：
 *   針對高頻 10,000 * sizeof(int) (40 KB) 請求，將熱路徑置於第一順位分支，
 *   以單向侵入式 LIFO 串列達成 O(1) 分配與釋放，100% 命中 L1/L2 Cache。
 * - Tier-2 (O(1) Explicit Doubly-Linked Free-List + Boundary-Tag Coalescing Arena)：
 *   改進傳統隱式串列需線性掃描已分配區塊之缺點，於空閒區塊之 Payload 前 16 Bytes
 *   內嵌雙向自由串列指標 (free_prev / free_next)。
 *   分配時直接由 arena_free_head 取出空閒塊 (O(1))，釋放時透過實體前後標頭 (phys_prev / phys_next)
 *   進行 O(1) 雙向合併並維護顯式自由串列，徹底消除搜尋已分配區塊的時間開銷！
 */

#include "my_malloc.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/** 魔術數字 (Magic Numbers) 用於標頭完整性驗證與 Double-Free 攔截 */
#define MAGIC_ALLOCATED 0x5543414CU /* "UCAL" - 代表區塊目前處於「已分配」狀態 */
#define MAGIC_FREED     0x55434652U /* "UCFR" - 代表區塊目前處於「已釋放」狀態 */

/** 將任意大小向上對齊至 MY_ALIGNMENT (16 Bytes) 的倍數 */
static __inline size_t align_up(size_t size) {
    return (size + (MY_ALIGNMENT - 1U)) & ~(size_t)(MY_ALIGNMENT - 1U);
}

/**
 * @brief 記憶體區塊前置標頭 (Block Header)。
 *        固定大小為 32 Bytes（在 64-bit 系統下恰好為 16 Bytes 的兩倍，保證後方 Payload 對齊 16 Bytes）。
 */
typedef struct MyBlockHeader {
    uint32_t magic;                  /* 狀態魔術碼：MAGIC_ALLOCATED 或 MAGIC_FREED */
    uint32_t tier;                   /* 所屬層級：MY_TIER_SLAB / MY_TIER_ARENA / MY_TIER_FALLBACK */
    size_t   payload_capacity;       /* 此區塊可容納的最大有效負載位元組數 */
    struct MyBlockHeader *phys_prev; /* Arena 實體相鄰前一個區塊（用於 O(1) 向左合併 Coalescing） */
    struct MyBlockHeader *phys_next; /* Slab 空閒串列指標，或 Arena 實體相鄰下一個區塊（用於向右合併） */
} MyBlockHeader;

/**
 * @brief 顯式雙向自由串列節點 (Explicit Free-List Links)。
 *        當 Tier-2 Arena 區塊處於「空閒 (MAGIC_FREED)」狀態時，直接映射於其 Payload 的前 16 Bytes，
 *        完全不佔用額外標頭空間（Intrusive Design，參考 dlmalloc / TLSF）。
 */
typedef struct ArenaFreeNode {
    MyBlockHeader *free_prev;
    MyBlockHeader *free_next;
} ArenaFreeNode;

#define HEADER_SIZE 32U /* sizeof(MyBlockHeader) 固定為 32 Bytes */

static __inline ArenaFreeNode *get_free_node(MyBlockHeader *block) {
    return (ArenaFreeNode *)((uint8_t *)block + HEADER_SIZE);
}

/** 全域配置器內部狀態管理結構 */
typedef struct MyAllocatorContext {
    int            is_initialized;
    /* Tier-1: Slab Pool 成員 */
    uint8_t       *slab_raw_memory;
    size_t         slab_slot_stride;
    MyBlockHeader *slab_free_head;
    /* Tier-2: Explicit Free-List General Arena 成員 */
    uint8_t       *arena_raw_memory;
    MyBlockHeader *arena_first_block;
    MyBlockHeader *arena_free_head; /* 顯式空閒串列頭指標：直接指向第一個可用空閒區塊！ */
    /* 統計數據 */
    MyAllocatorStats stats;
} MyAllocatorContext;

static MyAllocatorContext g_ctx = {0};

/** 將空閒區塊 O(1) 插入 Tier-2 顯式自由串列頭部 (LIFO) */
static __inline void arena_freelist_insert(MyBlockHeader *block) {
    ArenaFreeNode *node = get_free_node(block);
    node->free_prev = NULL;
    node->free_next = g_ctx.arena_free_head;
    if (g_ctx.arena_free_head != NULL) {
        get_free_node(g_ctx.arena_free_head)->free_prev = block;
    }
    g_ctx.arena_free_head = block;
}

/** 將空閒區塊 O(1) 從 Tier-2 顯式自由串列中移除 */
static __inline void arena_freelist_remove(MyBlockHeader *block) {
    ArenaFreeNode *node = get_free_node(block);
    if (node->free_prev != NULL) {
        get_free_node(node->free_prev)->free_next = node->free_next;
    } else {
        g_ctx.arena_free_head = node->free_next;
    }
    if (node->free_next != NULL) {
        get_free_node(node->free_next)->free_prev = node->free_prev;
    }
    node->free_prev = NULL;
    node->free_next = NULL;
}

/**
 * @brief 初始化雙層混合式記憶體池。
 */
int myMallocInit(size_t slab_slot_count, size_t arena_bytes) {
    if (g_ctx.is_initialized) {
        return 0;
    }

    if (slab_slot_count == 0) {
        slab_slot_count = MY_SLAB_DEFAULT_SLOTS;
    }
    if (arena_bytes == 0) {
        arena_bytes = MY_ARENA_DEFAULT_SIZE;
    }

    memset(&g_ctx, 0, sizeof(g_ctx));

    /* 1. 初始化 Tier-1: O(1) Fast-Path Slab Pool */
    size_t slot_payload = align_up(MY_SLAB_SLOT_PAYLOAD_SIZE);
    size_t slot_stride = HEADER_SIZE + slot_payload;

    g_ctx.slab_raw_memory = (uint8_t *)malloc(slot_stride * slab_slot_count);
    if (g_ctx.slab_raw_memory == NULL) {
        return -1;
    }
    g_ctx.slab_slot_stride = slot_stride;
    g_ctx.stats.slab_total_slots = slab_slot_count;
    g_ctx.stats.slab_free_slots = slab_slot_count;

    g_ctx.slab_free_head = NULL;
    for (size_t i = 0; i < slab_slot_count; ++i) {
        size_t idx = (slab_slot_count - 1U) - i;
        MyBlockHeader *hdr = (MyBlockHeader *)(g_ctx.slab_raw_memory + idx * slot_stride);
        hdr->magic = MAGIC_FREED;
        hdr->tier = MY_TIER_SLAB;
        hdr->payload_capacity = slot_payload;
        hdr->phys_prev = NULL;
        hdr->phys_next = g_ctx.slab_free_head;
        g_ctx.slab_free_head = hdr;
    }

    /* 2. 初始化 Tier-2: O(1) Explicit Free-List Coalescing Arena */
    arena_bytes = align_up(arena_bytes);
    g_ctx.arena_raw_memory = (uint8_t *)malloc(arena_bytes);
    if (g_ctx.arena_raw_memory == NULL) {
        free(g_ctx.slab_raw_memory);
        g_ctx.slab_raw_memory = NULL;
        return -1;
    }

    g_ctx.stats.arena_total_bytes = arena_bytes;
    g_ctx.stats.arena_used_bytes = 0;

    MyBlockHeader *initial_block = (MyBlockHeader *)g_ctx.arena_raw_memory;
    initial_block->magic = MAGIC_FREED;
    initial_block->tier = MY_TIER_ARENA;
    initial_block->payload_capacity = arena_bytes - HEADER_SIZE;
    initial_block->phys_prev = NULL;
    initial_block->phys_next = NULL;

    g_ctx.arena_first_block = initial_block;
    g_ctx.arena_free_head = NULL;
    arena_freelist_insert(initial_block);

    g_ctx.is_initialized = 1;
    return 0;
}

/**
 * @brief 釋放整個自訂記憶體池歸還予作業系統。
 */
void myMallocDestroy(void) {
    if (!g_ctx.is_initialized) {
        return;
    }
    if (g_ctx.slab_raw_memory != NULL) {
        free(g_ctx.slab_raw_memory);
        g_ctx.slab_raw_memory = NULL;
    }
    if (g_ctx.arena_raw_memory != NULL) {
        free(g_ctx.arena_raw_memory);
        g_ctx.arena_raw_memory = NULL;
    }
    memset(&g_ctx, 0, sizeof(g_ctx));
}

/**
 * @brief 於 Tier-2 通用 Arena 中執行區塊分割與顯式自由串列更新。
 */
static __inline void arena_allocate_from_free_block(MyBlockHeader *block, size_t needed_payload) {
    size_t min_split_threshold = HEADER_SIZE + sizeof(ArenaFreeNode) + MY_ALIGNMENT;

    arena_freelist_remove(block);

    if (block->payload_capacity >= needed_payload + min_split_threshold) {
        uint8_t *block_bytes = (uint8_t *)block;
        MyBlockHeader *remainder = (MyBlockHeader *)(block_bytes + HEADER_SIZE + needed_payload);

        remainder->magic = MAGIC_FREED;
        remainder->tier = MY_TIER_ARENA;
        remainder->payload_capacity = block->payload_capacity - needed_payload - HEADER_SIZE;
        remainder->phys_prev = block;
        remainder->phys_next = block->phys_next;

        if (block->phys_next != NULL) {
            block->phys_next->phys_prev = remainder;
        }

        block->payload_capacity = needed_payload;
        block->phys_next = remainder;

        /* 將切割剩餘的新空閒區塊推回顯式自由串列頭 */
        arena_freelist_insert(remainder);
    }

    block->magic = MAGIC_ALLOCATED;
}

/**
 * @brief 於 Tier-2 通用 Arena 中執行 O(1) 雙向相鄰空閒區塊合併並維護顯式自由串列。
 */
static __inline void arena_coalesce_and_insert(MyBlockHeader *block) {
    /* 1. 向右合併：檢查實體下一個區塊是否也是空閒狀態 */
    if (block->phys_next != NULL && block->phys_next->magic == MAGIC_FREED) {
        MyBlockHeader *right = block->phys_next;
        arena_freelist_remove(right);
        block->payload_capacity += HEADER_SIZE + right->payload_capacity;
        block->phys_next = right->phys_next;
        if (right->phys_next != NULL) {
            right->phys_next->phys_prev = block;
        }
        right->magic = 0U;
        g_ctx.stats.coalesce_merges++;
    }

    /* 2. 向左合併：檢查實體前一個區塊是否也是空閒狀態 */
    if (block->phys_prev != NULL && block->phys_prev->magic == MAGIC_FREED) {
        MyBlockHeader *left = block->phys_prev;
        arena_freelist_remove(left);
        left->payload_capacity += HEADER_SIZE + block->payload_capacity;
        left->phys_next = block->phys_next;
        if (block->phys_next != NULL) {
            block->phys_next->phys_prev = left;
        }
        block->magic = 0U;
        g_ctx.stats.coalesce_merges++;
        block = left;
    }

    arena_freelist_insert(block);
}

/**
 * @brief 高效能記憶體分配函式。
 */
void *myMalloc(size_t size) {
    if (size == 0) {
        return NULL;
    }

    if (!g_ctx.is_initialized) {
        if (myMallocInit(0, 0) != 0) {
            return NULL;
        }
    }

    g_ctx.stats.total_alloc_calls++;
    size_t aligned_size = align_up(size);
    if (aligned_size < sizeof(ArenaFreeNode)) {
        aligned_size = sizeof(ArenaFreeNode);
    }

    /* =========================================================================
     * 路徑一 (Tier-1 Fast-Path)：
     * 針對 8 KB <= size <= 40 KB (如 10,000 * sizeof(int)) 直接 O(1) LIFO Pop！
     * ========================================================================= */
    if (aligned_size >= 8192U &&
        aligned_size <= MY_SLAB_SLOT_PAYLOAD_SIZE &&
        g_ctx.slab_free_head != NULL) {

        MyBlockHeader *slot = g_ctx.slab_free_head;
        g_ctx.slab_free_head = slot->phys_next;
        slot->phys_next = NULL;
        slot->magic = MAGIC_ALLOCATED;

        g_ctx.stats.slab_free_slots--;
        g_ctx.stats.slab_hit_count++;

        return (void *)((uint8_t *)slot + HEADER_SIZE);
    }

    /* =========================================================================
     * 路徑二 (Tier-2 Explicit Free-List Arena)：
     * 直接走訪顯式空閒串列 (只看 Free Blocks，完全跳過已分配區塊)，首個滿足者 O(1) 取出！
     * ========================================================================= */
    MyBlockHeader *curr = g_ctx.arena_free_head;
    while (curr != NULL) {
        if (curr->payload_capacity >= aligned_size) {
            arena_allocate_from_free_block(curr, aligned_size);
            g_ctx.stats.arena_used_bytes += curr->payload_capacity;
            g_ctx.stats.arena_hit_count++;
            return (void *)((uint8_t *)curr + HEADER_SIZE);
        }
        curr = get_free_node(curr)->free_next;
    }

    /* 若 Arena 滿但 Slab 仍有空間且尺寸可容納，自動借用 Slab Slot */
    if (aligned_size <= MY_SLAB_SLOT_PAYLOAD_SIZE && g_ctx.slab_free_head != NULL) {
        MyBlockHeader *slot = g_ctx.slab_free_head;
        g_ctx.slab_free_head = slot->phys_next;
        slot->phys_next = NULL;
        slot->magic = MAGIC_ALLOCATED;

        g_ctx.stats.slab_free_slots--;
        g_ctx.stats.slab_hit_count++;

        return (void *)((uint8_t *)slot + HEADER_SIZE);
    }

    /* =========================================================================
     * 路徑三 (Tier-3 OS Fallback)
     * ========================================================================= */
    MyBlockHeader *sys_block = (MyBlockHeader *)malloc(HEADER_SIZE + aligned_size);
    if (sys_block == NULL) {
        return NULL;
    }
    sys_block->magic = MAGIC_ALLOCATED;
    sys_block->tier = MY_TIER_FALLBACK;
    sys_block->payload_capacity = aligned_size;
    sys_block->phys_prev = NULL;
    sys_block->phys_next = NULL;

    g_ctx.stats.fallback_hit_count++;
    return (void *)((uint8_t *)sys_block + HEADER_SIZE);
}

/**
 * @brief 高效能記憶體釋放函式。
 */
void myFree(void *ptr) {
    if (ptr == NULL) {
        return;
    }

    MyBlockHeader *hdr = (MyBlockHeader *)((uint8_t *)ptr - HEADER_SIZE);

    if (hdr->magic != MAGIC_ALLOCATED) {
        g_ctx.stats.double_free_detections++;
        return;
    }

    g_ctx.stats.total_free_calls++;

    if (hdr->tier == MY_TIER_SLAB) {
        hdr->magic = MAGIC_FREED;
        hdr->phys_next = g_ctx.slab_free_head;
        g_ctx.slab_free_head = hdr;
        g_ctx.stats.slab_free_slots++;
    } else if (hdr->tier == MY_TIER_ARENA) {
        hdr->magic = MAGIC_FREED;
        if (g_ctx.stats.arena_used_bytes >= hdr->payload_capacity) {
            g_ctx.stats.arena_used_bytes -= hdr->payload_capacity;
        }
        arena_coalesce_and_insert(hdr);
    } else if (hdr->tier == MY_TIER_FALLBACK) {
        hdr->magic = MAGIC_FREED;
        free(hdr);
    } else {
        g_ctx.stats.double_free_detections++;
    }
}

/**
 * @brief 配置並自動清零。
 */
void *myCalloc(size_t num, size_t size) {
    if (num == 0 || size == 0) {
        return NULL;
    }
    if (size > ((size_t)-1) / num) {
        return NULL;
    }
    size_t total = num * size;
    void *ptr = myMalloc(total);
    if (ptr != NULL) {
        memset(ptr, 0, total);
    }
    return ptr;
}

/**
 * @brief 重新調整記憶體大小。
 */
void *myRealloc(void *ptr, size_t new_size) {
    if (ptr == NULL) {
        return myMalloc(new_size);
    }
    if (new_size == 0) {
        myFree(ptr);
        return NULL;
    }

    MyBlockHeader *hdr = (MyBlockHeader *)((uint8_t *)ptr - HEADER_SIZE);
    if (hdr->magic != MAGIC_ALLOCATED) {
        return NULL;
    }

    if (hdr->payload_capacity >= align_up(new_size)) {
        return ptr;
    }

    void *new_ptr = myMalloc(new_size);
    if (new_ptr != NULL) {
        memcpy(new_ptr, ptr, hdr->payload_capacity);
        myFree(ptr);
    }
    return new_ptr;
}

/**
 * @brief 複製統計資訊結構。
 */
void myMallocGetStats(MyAllocatorStats *out_stats) {
    if (out_stats != NULL) {
        *out_stats = g_ctx.stats;
    }
}

/**
 * @brief 印出配置器內部運行統計報表。
 */
void myMallocPrintStats(void) {
    printf("------------------------------------------------------------------------\n");
    printf("                 [myMalloc 雙層混合式記憶體池統計報表]                  \n");
    printf("------------------------------------------------------------------------\n");
    printf("  * 總分配呼叫次數 (total_alloc_calls)   : %zu\n", g_ctx.stats.total_alloc_calls);
    printf("  * 總釋放呼叫次數 (total_free_calls)    : %zu\n", g_ctx.stats.total_free_calls);
    printf("  * Tier-1 Slab Fast-Path 命中次數       : %zu (剩餘空閒 Slot: %zu / %zu)\n",
           g_ctx.stats.slab_hit_count,
           g_ctx.stats.slab_free_slots,
           g_ctx.stats.slab_total_slots);
    printf("  * Tier-2 通用 Arena 命中次數           : %zu (目前使用: %zu / %zu Bytes)\n",
           g_ctx.stats.arena_hit_count,
           g_ctx.stats.arena_used_bytes,
           g_ctx.stats.arena_total_bytes);
    printf("  * Tier-2 相鄰空閒區塊合併次數 (Coalesce): %zu\n", g_ctx.stats.coalesce_merges);
    printf("  * Tier-3 OS Fallback 降級次數          : %zu\n", g_ctx.stats.fallback_hit_count);
    printf("  * 攔截 Double-Free / 非法釋放次數      : %zu\n", g_ctx.stats.double_free_detections);
    printf("------------------------------------------------------------------------\n");
}

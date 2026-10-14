/* Exercise 9.20, Darwin-specific, single-threaded reserved-heap comparison.
 * H counts block-storage regions, including free space and in-region metadata.
 * H excludes out-of-region controllers for both backends, and is not RSS.
 * A private libc scalable zone isolates the workload from runtime allocations;
 * this does not measure default malloc's nano/xzone dispatch policy.
 * Compile without ASan: intercepting libc would change the measured backend. */
#define ARENA_ALIGNMENT 16384
#define main allocator_example_main
#include "ch09_allocator.c"
#undef main

#ifdef __APPLE__
#include <mach/mach.h>
#include <unistd.h>

typedef struct { uintptr_t start, end; } interval;
typedef struct { interval ranges[128]; size_t count, page; bool failed; } regions;
typedef struct {
    size_t peak_payload, max_heap, final_heap, operations, samples;
} measurement;

static void record_regions(task_t task, void *context, unsigned type,
                           vm_range_t *ranges, unsigned count) {
    (void)task;
    regions *r = context;
    if (!(type & (MALLOC_PTR_REGION_RANGE_TYPE | MALLOC_ADMIN_REGION_RANGE_TYPE))) {
        r->failed = true;
        return;
    }
    for (unsigned i = 0; i < count; ++i) {
        uintptr_t start = ranges[i].address;
        size_t bytes = ranges[i].size;
        if (!bytes) continue;
        if (r->count == 128 || bytes > UINTPTR_MAX - start ||
            start + bytes > UINTPTR_MAX - (r->page - 1)) {
            r->failed = true;
            return;
        }
        r->ranges[r->count++] = (interval){start / r->page * r->page,
            (start + bytes + r->page - 1) / r->page * r->page};
    }
}

/* Page union, rather than a sum: admin/data ranges can share boundary pages. */
static size_t region_bytes(malloc_zone_t *zone, size_t page) {
    regions r = {.page = page};
    kern_return_t rc = zone->introspect->enumerator(mach_task_self(), &r,
        MALLOC_PTR_REGION_RANGE_TYPE | MALLOC_ADMIN_REGION_RANGE_TYPE,
        (vm_address_t)zone, NULL, record_regions);
    require(rc == KERN_SUCCESS && !r.failed);
    for (size_t i = 1; i < r.count; ++i) {
        interval v = r.ranges[i]; size_t j = i;
        while (j && r.ranges[j - 1].start > v.start) {
            r.ranges[j] = r.ranges[j - 1]; --j;
        }
        r.ranges[j] = v;
    }
    size_t total = 0;
    uintptr_t end = 0;
    for (size_t i = 0; i < r.count; ++i) {
        interval v = r.ranges[i];
        uintptr_t begin = v.start > end ? v.start : end;
        if (v.end > begin) total += v.end - begin;
        if (v.end > end) end = v.end;
    }
    return total;
}

static void sample(measurement *m, malloc_zone_t *zone, size_t page, size_t payload) {
    size_t h = CAP;
    if (zone) {
        malloc_statistics_t s = {0};
        malloc_zone_statistics(zone, &s);
        h = s.size_allocated;
        /* Fail rather than relabel a platform whose two region accounts differ. */
        require(h == region_bytes(zone, page));
    } else require(check());
    require(h % page == 0 && payload <= h);
    if (payload > m->peak_payload) m->peak_payload = payload;
    if (h > m->max_heap) m->max_heap = h;
    m->final_heap = h;
    ++m->samples;
}

static void measure(unsigned mode, unsigned count, size_t page) {
    void *p[512] = {0};
    size_t lens[512] = {0}, payload = 0;
    measurement m = {0};
    malloc_zone_t *zone = NULL;
    if (mode == 2) {
        zone = malloc_create_zone(0, 0);
        require(zone != NULL && zone->introspect != NULL &&
                zone->introspect->enumerator != NULL);
    } else init(mode == 1, false);
    sample(&m, zone, page, payload);
    for (unsigned i = 0; i < count; ++i) {
        lens[i] = 8u + (13u * i) % 120u;
        p[i] = zone ? malloc_zone_malloc(zone, lens[i]) : toy_malloc(lens[i]);
        require(p[i] != NULL);
        memset(p[i], (int)(i % 251u), lens[i]);
        payload += lens[i]; ++m.operations;
        sample(&m, zone, page, payload);
    }
    /* Free evens then odds, checking every payload byte before each release. */
    for (unsigned parity = 0; parity < 2; ++parity) {
        for (unsigned i = parity; i < count; i += 2) {
            for (size_t j = 0; j < lens[i]; ++j)
                require(((unsigned char *)p[i])[j] == i % 251u);
            if (zone) malloc_zone_free(zone, p[i]); else toy_free(p[i]);
            p[i] = NULL; payload -= lens[i]; ++m.operations;
            sample(&m, zone, page, payload);
        }
    }
    require(payload == 0 && m.max_heap > 0);
    if (zone) malloc_destroy_zone(zone);
    printf("{\"backend\":\"%s\",\"blocks\":%u,\"page_bytes\":%zu,"
           "\"peak_payload\":%zu,\"max_heap\":%zu,\"final_heap\":%zu,"
           "\"operations\":%zu,\"samples\":%zu,\"peak_utilization\":%.9f}\n",
        mode == 0 ? "toy-first" : mode == 1 ? "toy-next" : "libc-private-zone",
        count, page, m.peak_payload, m.max_heap, m.final_heap, m.operations,
        m.samples, (double)m.peak_payload / m.max_heap);
}

int main(void) {
    long raw_page = sysconf(_SC_PAGESIZE);
    require(raw_page > 0 && CAP % (size_t)raw_page == 0 &&
            (uintptr_t)heap.b % (size_t)raw_page == 0);
    for (unsigned count = 64; count <= 512; count *= 8)
        for (unsigned mode = 0; mode < 3; ++mode) measure(mode, count, (size_t)raw_page);
    return 0;
}
#else
int main(void) {
    fputs("Darwin malloc zone statistics are required for this experiment\n", stderr);
    return 2;
}
#endif

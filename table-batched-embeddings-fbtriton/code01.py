is_long        = (run_len >= threshold) & mask
num_long_block = tl.sum(is_long.to(tl.int32))
long_base      = tl.atomic_add(num_long_ptr, num_long_block)
long_local     = tl.cumsum(is_long.to(tl.int32), axis=0) - 1
tl.store(long_run_ids_ptr + (long_base + long_local).to(tl.int64),
         offsets.to(tl.int32), mask=is_long)
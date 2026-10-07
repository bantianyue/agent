tl.atomic_add(temp_grad_buffer_ptr + temp_grad_offset + col_offsets, grad, mask=mask)
tlx.fence("gpu")
remaining = tl.atomic_add(grad_accum_counter_ptr + grad_buffer_id, -1)
if remaining == 1:
    ...  # last sub-program applies the optimizer and stores
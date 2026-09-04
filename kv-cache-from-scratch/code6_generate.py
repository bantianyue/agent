def generate_text_simple_cached(
        model, idx, max_new_tokens, use_cache=True
    ):
    model.eval()
​
    ctx_len = model.pos_emb.num_embeddings  # max sup. len., e.g. 1024
    if use_cache:
        # Init cache with full prompt
        model.reset_kv_cache()
        with torch.no_grad():
            logits = model(idx[:, -ctx_len:], use_cache=True)
​
        for _ in range(max_new_tokens):
            # a) pick the token with the highest log-probability 
            next_idx = logits[:, -1].argmax(dim=-1, keepdim=True)
            # b) append it to the running sequence
            idx = torch.cat([idx, next_idx], dim=1)
            # c) feed model only the new token
            with torch.no_grad():
                logits = model(next_idx, use_cache=True)
    else:
        for _ in range(max_new_tokens):
            with torch.no_grad():
                logits = model(idx[:, -ctx_len:], use_cache=False)
            next_idx = logits[:, -1].argmax(dim=-1, keepdim=True)
            idx = torch.cat([idx, next_idx], dim=1)
​
    return idx

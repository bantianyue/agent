session_affinity_config = LLMConfig(
    model_loading_config=...,
    deployment_config=(
        "request_router_config": RequestRouterConfig(
            request_router_class=(
                "ray.serve.experimental.",
                "consistent_hash_router.ConsistentHashRouter"
            )
        ),
        engine_kwargs={...},
)
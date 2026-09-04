prefix_affinity_config = LLMConfig(
    model_loading_config=...,
    deployment_config=(
        "request_router_config": RequestRouterConfig(
            request_router_class=(
                "ray.serve.llm.",
                "request_router.PrefixCacheAffinityRouter",
            ),
            engine_kwargs={...},
)
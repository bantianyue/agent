```bash
# 1. Configure deployment environment variables
export NAMESPACE=qwen32-bench
export EXP_DIR=/ephemeral/shared/qwen3.6-35b-a3b/sglang/disagg/tp1-4p4d
export DEPLOYMENT=q36-sgl-pd-tp1-4p4d
export GRAPH_LABEL="nvidia.com/dynamo-graph-deployment-name=${DEPLOYMENT}"

# 2. Deploy TP1-4P4D serving graph (4 Prefill + 4 Decode across 8 GPUs)
kubectl apply -n "$NAMESPACE" -f "$EXP_DIR/deploy.yaml"

# 3. Monitor rollout & readiness across all 8 worker pods
kubectl get pods -n "$NAMESPACE" -l "$GRAPH_LABEL" -o wide -w

# 4. Teardown & release cluster resources when switching topologies
kubectl delete dynamographdeployment.nvidia.com "$DEPLOYMENT" \
  -n "$NAMESPACE" --wait=true --ignore-not-found
```
# ☸️ Kubernetes Playbook

[← Practicals](../README.md) · [Exam →](exam.md) · [Guide](../../kubernetes-foundations-to-advanced/README.md)

Hands-on labs (Part 1) and incident runbooks (Part 2). Every lab follows **Goal → Steps → ✅ Verify → 🧹 Cleanup**.

## 🧰 Prerequisites

- Docker, [`kind`](https://kind.sigs.k8s.io/) **v0.24+** (its kindnet CNI enforces NetworkPolicy), `kubectl`
- Optional: `helm`

---

# Part 1 · 🧪 Labs

## Lab 1 · A Multi-Node Cluster & the Control Plane 🟢

**Goal:** create a cluster and identify every component from [ch. 01](../../kubernetes-foundations-to-advanced/01-foundations.md).

```bash
mkdir -p ~/k8s-labs && cd ~/k8s-labs
cat > kind.yaml <<'EOF'
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
nodes:
  - role: control-plane
  - role: worker
    labels: { zone: a }
  - role: worker
    labels: { zone: b }
EOF
kind create cluster --name lab --config kind.yaml
kubectl get nodes -o wide
kubectl get pods -n kube-system -o wide
kubectl api-resources | head -20
kubectl explain deployment.spec.strategy
```

✅ **Verify:** in `kube-system` you can point to `etcd`, `kube-apiserver`, `kube-scheduler`, `kube-controller-manager` (control-plane node), `kube-proxy` + the CNI (every node) and `coredns`.

🧠 **Explain:** why does the kubelet not show up as a Pod? (It's a host process that *runs* Pods.)

---

## Lab 2 · Pods, Labels & Self-Healing 🟢

**Goal:** see the reconciliation loop at work. → [ch. 01](../../kubernetes-foundations-to-advanced/01-foundations.md), [ch. 02](../../kubernetes-foundations-to-advanced/02-core-workloads.md)

```bash
kubectl create namespace shop
kubectl config set-context --current --namespace shop

kubectl create deployment web --image=nginx:1.27-alpine --replicas=3
kubectl get deploy,rs,pods --show-labels
kubectl delete pod -l app=web --wait=false
kubectl get pods -w          # watch new Pods replace them (Ctrl-C)

kubectl label pod "$(kubectl get pod -l app=web -o name | head -1 | cut -d/ -f2)" app=quarantine --overwrite
kubectl get pods --show-labels   # 4 Pods: the relabelled one is orphaned, the RS made a replacement
```

✅ **Verify:** deleted Pods come back; relabelling one "detaches" it from the ReplicaSet (a classic debugging trick).

🧹 `kubectl delete pod -l app=quarantine`

---

## Lab 3 · Rolling Updates & Rollbacks 🟢

**Goal:** perform a zero-downtime rollout, break it, and undo it. → [ch. 02](../../kubernetes-foundations-to-advanced/02-core-workloads.md)

```bash
cat > web.yaml <<'EOF'
apiVersion: apps/v1
kind: Deployment
metadata: { name: web }
spec:
  replicas: 4
  selector: { matchLabels: { app: web } }
  strategy:
    type: RollingUpdate
    rollingUpdate: { maxSurge: 1, maxUnavailable: 0 }
  template:
    metadata: { labels: { app: web } }
    spec:
      containers:
        - name: web
          image: nginx:1.27-alpine
          ports: [{ containerPort: 80 }]
          readinessProbe:
            httpGet: { path: /, port: 80 }
            periodSeconds: 3
          resources:
            requests: { cpu: 50m, memory: 32Mi }
            limits:   { memory: 64Mi }
EOF
kubectl apply -f web.yaml
kubectl rollout status deploy/web

kubectl set image deploy/web web=nginx:1.28-alpine
kubectl annotate deploy/web kubernetes.io/change-cause="upgrade to 1.28" --overwrite
kubectl rollout status deploy/web
kubectl rollout history deploy/web

# 💥 Break it: an image that doesn't exist
kubectl set image deploy/web web=nginx:does-not-exist
kubectl get pods                       # ImagePullBackOff on ONE new Pod; old Pods still serve
kubectl rollout status deploy/web --timeout=30s || true
kubectl rollout undo deploy/web
kubectl rollout status deploy/web
```

✅ **Verify:** with `maxUnavailable: 0`, 4 Pods stay Ready throughout, even during the broken rollout; `undo` restores 1.28.

🧠 **Explain:** what would have happened with `maxUnavailable: 100%` or `strategy: Recreate`?

---

## Lab 4 · Services, DNS & EndpointSlices 🟢

**Goal:** wire traffic and debug "Service has no endpoints". → [ch. 03](../../kubernetes-foundations-to-advanced/03-networking.md)

```bash
kubectl expose deploy/web --port 80 --target-port 80
kubectl get svc web
kubectl get endpointslices -l kubernetes.io/service-name=web

kubectl run tmp --rm -it --image=busybox:1.36 --restart=Never -- sh -c '
  nslookup web; nslookup web.shop.svc.cluster.local; wget -qO- web | head -4'

# 💥 Break it: a selector that matches nothing
kubectl patch svc web -p '{"spec":{"selector":{"app":"wbe"}}}'
kubectl get endpointslices -l kubernetes.io/service-name=web     # no endpoints
kubectl run tmp --rm -it --image=busybox:1.36 --restart=Never -- wget -T3 -qO- web || true
kubectl patch svc web -p '{"spec":{"selector":{"app":"web"}}}'

# Reach it from your laptop
kubectl port-forward svc/web 8080:80 &
sleep 2; curl -s localhost:8080 | head -4; kill %1
```

✅ **Verify:** DNS resolves both the short and FQDN names; the typo empties the EndpointSlice; the fix restores it.

---

## Lab 5 · ConfigMaps, Secrets & Live Reload 🟡

**Goal:** prove that env vars don't update but mounted files do. → [ch. 04](../../kubernetes-foundations-to-advanced/04-config-storage.md)

```bash
kubectl create configmap app-config --from-literal=LOG_LEVEL=info --from-literal=FEATURE_X=false
kubectl create secret generic db-cred --from-literal=password='s3cr3t!'
kubectl get secret db-cred -o jsonpath='{.data.password}' | base64 -d; echo   # base64 ≠ encryption

cat > cfg-pod.yaml <<'EOF'
apiVersion: v1
kind: Pod
metadata: { name: cfg }
spec:
  containers:
    - name: app
      image: busybox:1.36
      command: ["sh", "-c", "while true; do echo env=$LOG_LEVEL file=$(cat /etc/cfg/LOG_LEVEL); sleep 5; done"]
      envFrom: [{ configMapRef: { name: app-config } }]
      env:
        - name: DB_PASSWORD
          valueFrom: { secretKeyRef: { name: db-cred, key: password } }
      volumeMounts: [{ name: cfg, mountPath: /etc/cfg, readOnly: true }]
  volumes:
    - name: cfg
      configMap: { name: app-config }
EOF
kubectl apply -f cfg-pod.yaml
kubectl logs cfg --tail 1
kubectl patch configmap app-config -p '{"data":{"LOG_LEVEL":"debug"}}'
sleep 75; kubectl logs cfg --tail 1
```

✅ **Verify:** after about a minute the log shows `env=info file=debug`.

🧠 **Explain:** how do you roll Pods automatically when config changes? (Checksum annotation in the template, e.g. Helm's `sha256sum`, or Reloader.)

🧹 `kubectl delete pod cfg`

---

## Lab 6 · StatefulSet, Headless DNS & PVCs 🟡

**Goal:** stable identities and storage that survives Pod deletion. → [ch. 02](../../kubernetes-foundations-to-advanced/02-core-workloads.md), [ch. 04](../../kubernetes-foundations-to-advanced/04-config-storage.md)

```bash
cat > sts.yaml <<'EOF'
apiVersion: v1
kind: Service
metadata: { name: db }
spec:
  clusterIP: None
  selector: { app: db }
  ports: [{ port: 80 }]
---
apiVersion: apps/v1
kind: StatefulSet
metadata: { name: db }
spec:
  serviceName: db
  replicas: 3
  selector: { matchLabels: { app: db } }
  template:
    metadata: { labels: { app: db } }
    spec:
      containers:
        - name: db
          image: nginx:1.27-alpine
          volumeMounts: [{ name: data, mountPath: /usr/share/nginx/html }]
  volumeClaimTemplates:
    - metadata: { name: data }
      spec:
        accessModes: [ReadWriteOnce]
        resources: { requests: { storage: 100Mi } }
EOF
kubectl apply -f sts.yaml
kubectl get pods -l app=db -w            # db-0, then db-1, then db-2 (Ctrl-C)
kubectl get pvc

for i in 0 1 2; do kubectl exec db-$i -- sh -c "echo I am db-$i > /usr/share/nginx/html/index.html"; done
kubectl delete pod db-1
kubectl wait --for=condition=Ready pod/db-1
kubectl run tmp --rm -it --image=busybox:1.36 --restart=Never -- sh -c '
  nslookup db; wget -qO- db-1.db.shop.svc.cluster.local'
```

✅ **Verify:** startup is ordered; `nslookup db` returns three Pod IPs (headless); `db-1` comes back with the **same name and the same data**.

🧹 `kubectl delete -f sts.yaml && kubectl delete pvc -l app=db` (PVCs aren't deleted with the StatefulSet: a deliberate safety net)

---

## Lab 7 · Resources, QoS, OOMKilled & Probes 🟡

**Goal:** trigger the failures from [ch. 05](../../kubernetes-foundations-to-advanced/05-scheduling-scaling.md) on purpose.

```bash
# OOMKilled
kubectl run hog --image=python:3.13-slim --restart=Never \
  --overrides='{"spec":{"containers":[{"name":"hog","image":"python:3.13-slim",
  "command":["python","-c","x=bytearray(200*1024*1024)"],
  "resources":{"requests":{"memory":"64Mi"},"limits":{"memory":"64Mi"}}}]}}'
sleep 15; kubectl get pod hog -o jsonpath='{.status.containerStatuses[0].state.terminated.reason}{"\n"}'

# QoS classes
kubectl get pod hog -o jsonpath='{.status.qosClass}{"\n"}'          # Burstable
kubectl get pods -l app=web -o jsonpath='{.items[0].status.qosClass}{"\n"}'

# Unschedulable: request more CPU than any node has
kubectl run huge --image=nginx:1.27-alpine --overrides='{"spec":{"containers":[{"name":"huge","image":"nginx:1.27-alpine","resources":{"requests":{"cpu":"64"}}}]}}'
kubectl describe pod huge | grep -A3 Events         # FailedScheduling: Insufficient cpu

# A failing liveness probe → restarts
cat > probe.yaml <<'EOF'
apiVersion: v1
kind: Pod
metadata: { name: probe }
spec:
  containers:
    - name: app
      image: nginx:1.27-alpine
      livenessProbe:
        httpGet: { path: /healthz, port: 80 }
        periodSeconds: 3
        failureThreshold: 2
EOF
kubectl apply -f probe.yaml
sleep 30; kubectl get pod probe            # RESTARTS climbing
kubectl describe pod probe | grep -i liveness
```

✅ **Verify:** `hog` reason = `OOMKilled`; `huge` stays `Pending` with `Insufficient cpu`; `probe` restarts because nginx returns 404 for `/healthz`.

🎯 **Stretch:** change the probe to a `readinessProbe`. The Pod stops restarting but stays `0/1 READY`, so it receives no Service traffic.

🧹 `kubectl delete pod hog huge probe`

---

## Lab 8 · Scheduling: Taints, Affinity & Topology Spread 🔴

**Goal:** control placement. → [ch. 05](../../kubernetes-foundations-to-advanced/05-scheduling-scaling.md)

```bash
W1=lab-worker; W2=lab-worker2
kubectl taint nodes $W2 dedicated=gpu:NoSchedule
kubectl create deployment spread --image=nginx:1.27-alpine --replicas=4
kubectl get pods -l app=spread -o wide          # all on lab-worker (W2 is tainted)

kubectl patch deploy spread -p '{"spec":{"template":{"spec":{
  "tolerations":[{"key":"dedicated","operator":"Equal","value":"gpu","effect":"NoSchedule"}],
  "topologySpreadConstraints":[{"maxSkew":1,"topologyKey":"zone","whenUnsatisfiable":"DoNotSchedule",
    "labelSelector":{"matchLabels":{"app":"spread"}}}]}}}}'
kubectl rollout status deploy/spread
kubectl get pods -l app=spread -o wide          # 2 per zone

kubectl taint nodes $W2 dedicated=gpu:NoSchedule-
```

✅ **Verify:** before the patch, Pods avoid the tainted node; after it, they're spread 2/2 across `zone=a` and `zone=b`.

🧠 **Explain:** why didn't the toleration alone *move* Pods to `lab-worker2`?

🧹 `kubectl delete deploy spread`

---

## Lab 9 · HPA & PodDisruptionBudget 🔴

**Goal:** autoscale on CPU, and protect availability during drains. → [ch. 05](../../kubernetes-foundations-to-advanced/05-scheduling-scaling.md)

```bash
# metrics-server (kind needs --kubelet-insecure-tls)
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/download/v0.7.2/components.yaml
kubectl -n kube-system patch deploy metrics-server --type=json \
  -p '[{"op":"add","path":"/spec/template/spec/containers/0/args/-","value":"--kubelet-insecure-tls"}]'
kubectl -n kube-system rollout status deploy/metrics-server
sleep 30; kubectl top nodes

kubectl create deployment php --image=registry.k8s.io/hpa-example
kubectl set resources deploy php --requests=cpu=200m --limits=cpu=500m
kubectl expose deploy php --port 80
kubectl autoscale deploy php --cpu-percent=50 --min=1 --max=6

kubectl run load --image=busybox:1.36 --restart=Never -- sh -c 'while true; do wget -qO- php >/dev/null; done'
kubectl get hpa php -w               # replicas climb within 1–3 min (Ctrl-C)
kubectl delete pod load
```

**PDB vs drain:**

```bash
kubectl scale deploy web --replicas=2
kubectl create pdb web-pdb --selector=app=web --min-available=2
kubectl drain lab-worker --ignore-daemonsets --delete-emptydir-data --timeout=30s || echo "blocked by PDB ✅"
kubectl uncordon lab-worker
kubectl patch pdb web-pdb -p '{"spec":{"minAvailable":1}}'
```

✅ **Verify:** the HPA scales up under load and back down ~5 min after; with `minAvailable: 2` the drain cannot evict `web` Pods.

🧹 `kubectl delete hpa php; kubectl delete deploy php; kubectl delete svc php; kubectl delete pdb web-pdb`

---

## Lab 10 · Security: NetworkPolicy, RBAC & Pod Security 🔴

**Goal:** apply the defaults from [ch. 06](../../kubernetes-foundations-to-advanced/06-security.md) and prove each one blocks something.

**NetworkPolicy** (kindnet in kind ≥ v0.24 enforces it):

```bash
kubectl run db  --image=nginx:1.27-alpine --labels=app=db  --port=80 --expose
kubectl run api --image=busybox:1.36 --labels=app=api -- sleep 3600
kubectl run rogue --image=busybox:1.36 --labels=app=rogue -- sleep 3600
kubectl wait --for=condition=Ready pod/api pod/rogue pod/db

cat > netpol.yaml <<'EOF'
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata: { name: default-deny-ingress }
spec:
  podSelector: {}
  policyTypes: [Ingress]
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata: { name: allow-api-to-db }
spec:
  podSelector: { matchLabels: { app: db } }
  policyTypes: [Ingress]
  ingress:
    - from: [{ podSelector: { matchLabels: { app: api } } }]
      ports: [{ protocol: TCP, port: 80 }]
EOF
kubectl apply -f netpol.yaml
kubectl exec api   -- wget -T3 -qO- db | head -1     # ✅ allowed
kubectl exec rogue -- wget -T3 -qO- db || echo "rogue blocked ✅"
```

**RBAC:**

```bash
kubectl create serviceaccount deployer
kubectl create role deployment-updater --verb=get,list,update,patch --resource=deployments.apps
kubectl create rolebinding deployer-binding --role=deployment-updater --serviceaccount=shop:deployer
SA=system:serviceaccount:shop:deployer
kubectl auth can-i patch deployments --as $SA          # yes
kubectl auth can-i delete deployments --as $SA         # no
kubectl auth can-i get secrets --as $SA                # no
kubectl auth can-i --list --as $SA
```

**Pod Security Admission (`restricted`):**

```bash
kubectl create namespace secure
kubectl label namespace secure pod-security.kubernetes.io/enforce=restricted
kubectl -n secure run bad --image=nginx:1.27-alpine           # ❌ rejected, with reasons listed

cat > good.yaml <<'EOF'
apiVersion: v1
kind: Pod
metadata: { name: good, namespace: secure }
spec:
  automountServiceAccountToken: false
  securityContext:
    runAsNonRoot: true
    runAsUser: 10001
    seccompProfile: { type: RuntimeDefault }
  containers:
    - name: app
      image: busybox:1.36
      command: ["sleep", "3600"]
      securityContext:
        allowPrivilegeEscalation: false
        readOnlyRootFilesystem: true
        capabilities: { drop: ["ALL"] }
EOF
kubectl apply -f good.yaml                                     # ✅ admitted
```

✅ **Verify:** `rogue` is blocked, `api` isn't; `can-i` matches least privilege; PSA rejects `bad` and admits `good`.

🧹 **Cluster cleanup (after all labs):** `kind delete cluster --name lab`

---

# Part 2 · 🚨 Incident Runbooks

Each runbook follows **Symptom → Triage → Likely causes → Fix → Prevent.**

## RB-1 · Pod not running (the status decision table)

```bash
kubectl get pod <p> -o wide
kubectl describe pod <p>            # read Events bottom-up
kubectl logs <p> [-c <container>] --previous
kubectl get events --sort-by=.lastTimestamp | tail -20
```

| Status | Look at | Common fix |
|--------|---------|-----------|
| `Pending` | Events: FailedScheduling | Lower requests, tolerations/affinity, PVC/StorageClass, quota |
| `ImagePullBackOff` / `ErrImagePull` | Image name/tag, registry auth | Fix tag; `imagePullSecrets`; private registry access |
| `CrashLoopBackOff` | `logs --previous`, exit code | App config/env/secret missing; bad command; dependency down |
| `OOMKilled` | `lastState.terminated.reason` | Raise memory limit or fix the leak |
| `Running` but `0/1 READY` | Readiness probe events | Fix probe path/port/timing; dependency checks |
| `CreateContainerConfigError` | Events | Referenced ConfigMap/Secret/key doesn't exist |

**Debug a distroless/crashing Pod:** `kubectl debug -it <p> --image=busybox:1.36 --target=<container>` or `kubectl debug <p> --copy-to=dbg --container=<c> -- sh`.

## RB-2 · Service unreachable

1. `kubectl get endpointslices -l kubernetes.io/service-name=<svc>`: empty? → selector/labels mismatch or Pods not Ready.
2. `port` vs `targetPort` vs the container's real listening port (`kubectl exec <p> -- netstat -tlnp`).
3. DNS: `kubectl run tmp --rm -it --image=busybox:1.36 --restart=Never -- nslookup <svc>.<ns>`; check `coredns` Pods.
4. NetworkPolicy: `kubectl get netpol -A`. Is there a default-deny without an allow (or without DNS egress)?
5. External: Ingress/Gateway controller installed? Ingress `ingressClassName`, host and path; LB provisioned (`EXTERNAL-IP` not `<pending>`)?

## RB-3 · Node `NotReady`

1. `kubectl describe node <n>`: Conditions (`MemoryPressure`, `DiskPressure`, `PIDPressure`), last heartbeat.
2. On the node: `systemctl status kubelet containerd`, `journalctl -u kubelet --since -30m`.
3. Disk full (images/logs) → `crictl rmi --prune`, log rotation.
4. Workloads are evicted after the toleration timeout (default 5 min). PDBs, replicas ≥ 2 and topology spread limit the impact.
5. Replace the node if it's unhealthy (cattle, not pets): `kubectl cordon` → `drain` → delete.

## RB-4 · Rollout stuck / bad release

```bash
kubectl rollout status deploy/<d>
kubectl get rs -l app=<d>
kubectl rollout undo deploy/<d>
```

Root-cause from the new ReplicaSet's Pods (RB-1). Check `progressDeadlineSeconds`. Prevent with readiness gates, canary analysis (Argo Rollouts/Flagger), and GitOps for auditable reverts.

## RB-5 · Cluster upgrade

1. Read the release notes; scan for removed APIs: `pluto detect-all-in-cluster`, `kubent`.
2. Back up etcd / take Velero backups.
3. Control plane first, one minor version at a time.
4. Node pools: surge or blue/green; `kubectl drain --ignore-daemonsets --delete-emptydir-data`.
5. Watch PDBs that block drains (`kubectl get pdb -A`, `ALLOWED DISRUPTIONS 0`).
6. Upgrade add-ons (CNI, CSI, ingress, cert-manager) according to their compatibility matrices.

---

## ✅ Completion Checklist

- [ ] Labs 1–4 (🟢) done
- [ ] Labs 5–7 (🟡) done
- [ ] Labs 8–10 (🔴) done
- [ ] Can explain each runbook from memory
- [ ] Scored ≥ 70 on the [exam](exam.md)

# ☸️ Kubernetes Exam

[← Practicals](../README.md) · [Playbook →](playbook.md) · [Guide](../../kubernetes-foundations-to-advanced/README.md)

| | |
|--|--|
| ⏱️ Time | 100 minutes |
| 🎯 Pass mark | 70 / 100 |
| 📚 Covers | Chapters 01–07 of [Kubernetes: Foundations to Advanced](../../kubernetes-foundations-to-advanced/README.md) |
| 🧭 Rules | Closed book for Parts A–B. Parts C–D may use a cluster |

Answers are hidden under **Answer**, with the chapter to re-read.

---

## 🅰️ Part A: Multiple Choice (20 × 2 pts = 40)

**A1.** Which component is the **only** one that talks to etcd directly?

- a) kube-scheduler
- b) kube-apiserver
- c) kubelet
- d) kube-controller-manager

<details><summary>Answer</summary>

**b).** Everything else goes through the API server. → [01](../../kubernetes-foundations-to-advanced/01-foundations.md)
</details>

**A2.** What is the correct order of a `kubectl apply` request inside the API server?

- a) Admission → AuthN → AuthZ → etcd
- b) AuthN → AuthZ → Admission → etcd
- c) AuthZ → AuthN → etcd → Admission
- d) etcd → AuthN → AuthZ → Admission

<details><summary>Answer</summary>

**b).** → [01](../../kubernetes-foundations-to-advanced/01-foundations.md)
</details>

**A3.** Who writes an object's `status`?

- a) The user via `kubectl apply`
- b) Controllers/kubelet reporting observed state
- c) etcd
- d) The admission webhook

<details><summary>Answer</summary>

**b).** You declare `spec` (desired); the system reports `status` (observed). → [01](../../kubernetes-foundations-to-advanced/01-foundations.md)
</details>

**A4.** You delete a Pod owned by a Deployment. What happens?

- a) The Deployment is scaled down by one
- b) The ReplicaSet notices fewer Pods than desired and creates a new one
- c) Nothing until you run `kubectl rollout restart`
- d) The node restarts it in place

<details><summary>Answer</summary>

**b).** That's the reconciliation loop. → [01](../../kubernetes-foundations-to-advanced/01-foundations.md), [02](../../kubernetes-foundations-to-advanced/02-core-workloads.md)
</details>

**A5.** With `replicas: 4`, `maxSurge: 1`, `maxUnavailable: 0`, during a rollout there are at most:

- a) 4 Pods, at least 3 ready
- b) 5 Pods, at least 4 ready
- c) 8 Pods
- d) 4 Pods, at least 4 ready

<details><summary>Answer</summary>

**b).** → [02](../../kubernetes-foundations-to-advanced/02-core-workloads.md)
</details>

**A6.** Which workload gives stable names (`db-0`, `db-1`), ordered startup and a PVC per replica?

- a) Deployment
- b) DaemonSet
- c) StatefulSet
- d) ReplicaSet

<details><summary>Answer</summary>

**c).** → [02](../../kubernetes-foundations-to-advanced/02-core-workloads.md)
</details>

**A7.** A log-shipping agent must run exactly once on every node, including new nodes. Use:

- a) Deployment with `replicas = node count`
- b) DaemonSet
- c) CronJob
- d) StatefulSet

<details><summary>Answer</summary>

**b).** → [02](../../kubernetes-foundations-to-advanced/02-core-workloads.md)
</details>

**A8.** A CronJob's run takes longer than its schedule interval. Which setting prevents overlapping runs?

- a) `backoffLimit: 0`
- b) `concurrencyPolicy: Forbid`
- c) `ttlSecondsAfterFinished`
- d) `restartPolicy: Never`

<details><summary>Answer</summary>

**b).** → [02](../../kubernetes-foundations-to-advanced/02-core-workloads.md)
</details>

**A9.** A Service has `port: 80`, `targetPort: 8080`. Clients connect to:

- a) `svc:8080`, which forwards to Pod port 80
- b) `svc:80`, which forwards to Pod port 8080
- c) Either port
- d) The node's port 80

<details><summary>Answer</summary>

**b).** → [03](../../kubernetes-foundations-to-advanced/03-networking.md)
</details>

**A10.** A Service has no endpoints. The **most common** cause is:

- a) CoreDNS is down
- b) The Service selector doesn't match the Pods' labels (or no Pods are Ready)
- c) The Service type is ClusterIP
- d) The Ingress is missing

<details><summary>Answer</summary>

**b).** Check with `kubectl get endpointslices -l kubernetes.io/service-name=<svc>`. → [03](../../kubernetes-foundations-to-advanced/03-networking.md)
</details>

**A11.** You apply an `Ingress` resource, but nothing routes traffic. Why?

- a) Ingress needs a LoadBalancer Service per host
- b) There's no Ingress **controller** installed
- c) Ingress only works with NodePort
- d) The namespace lacks a NetworkPolicy

<details><summary>Answer</summary>

**b).** → [03](../../kubernetes-foundations-to-advanced/03-networking.md)
</details>

**A12.** By default (no NetworkPolicies), Pod-to-Pod traffic across namespaces is:

- a) Blocked
- b) Allowed
- c) Allowed only within a node
- d) Allowed only via Services

<details><summary>Answer</summary>

**b).** The network model gives every Pod a routable IP with no NAT. Isolation needs NetworkPolicy + a CNI that enforces it. → [03](../../kubernetes-foundations-to-advanced/03-networking.md)
</details>

**A13.** A Secret's data is:

- a) Encrypted with AES by default
- b) Base64-encoded; encryption at rest must be configured separately
- c) Hashed
- d) Stored only in memory

<details><summary>Answer</summary>

**b).** → [04](../../kubernetes-foundations-to-advanced/04-config-storage.md)
</details>

**A14.** You update a ConfigMap. Which consumer sees the change **without** a Pod restart?

- a) An environment variable from `envFrom`
- b) A file from a full volume mount
- c) A file mounted with `subPath`
- d) None of them

<details><summary>Answer</summary>

**b).** It updates after a short delay. Env vars and `subPath` mounts don't update. → [04](../../kubernetes-foundations-to-advanced/04-config-storage.md)
</details>

**A15.** Why use `volumeBindingMode: WaitForFirstConsumer` on a StorageClass?

- a) To make volumes faster
- b) So the volume is created in the zone where the Pod is scheduled
- c) To enable RWX access
- d) To delay deletion

<details><summary>Answer</summary>

**b).** Otherwise the disk might be in a different zone from the Pod. → [04](../../kubernetes-foundations-to-advanced/04-config-storage.md)
</details>

**A16.** A container exceeds its **CPU** limit. What happens?

- a) It's OOMKilled
- b) It's throttled
- c) It's evicted
- d) Nothing

<details><summary>Answer</summary>

**b).** Exceeding the **memory** limit gets it OOMKilled. → [05](../../kubernetes-foundations-to-advanced/05-scheduling-scaling.md)
</details>

**A17.** A Pod where every container has `requests == limits` for CPU and memory has QoS class:

- a) BestEffort
- b) Burstable
- c) Guaranteed
- d) Critical

<details><summary>Answer</summary>

**c).** It's evicted last under node pressure. → [05](../../kubernetes-foundations-to-advanced/05-scheduling-scaling.md)
</details>

**A18.** Which probe failure **removes the Pod from Service endpoints without restarting it**?

- a) livenessProbe
- b) readinessProbe
- c) startupProbe
- d) All of them

<details><summary>Answer</summary>

**b).** → [05](../../kubernetes-foundations-to-advanced/05-scheduling-scaling.md)
</details>

**A19.** An HPA targets 70% CPU utilisation. That percentage is relative to:

- a) The container's CPU limit
- b) The container's CPU **request**
- c) Node capacity
- d) The cluster average

<details><summary>Answer</summary>

**b).** Without requests, HPA can't compute utilisation. → [05](../../kubernetes-foundations-to-advanced/05-scheduling-scaling.md)
</details>

**A20.** Which Pod Security Admission level should application namespaces target?

- a) privileged
- b) baseline
- c) restricted
- d) audit

<details><summary>Answer</summary>

**c).** `privileged` is only for system namespaces. → [06](../../kubernetes-foundations-to-advanced/06-security.md)
</details>

---

## 🅱️ Part B: Short Answer (8 × 3 pts = 24)

**B1.** Explain the reconciliation loop in one sentence and give one example controller.

<details><summary>Answer</summary>

Controllers continuously **observe** actual state, **compare** it to desired state, and **act** to close the gap. Examples: the ReplicaSet controller keeps N Pods running, the Node controller marks unreachable nodes. → [01](../../kubernetes-foundations-to-advanced/01-foundations.md)
</details>

**B2.** A Pod is in `CrashLoopBackOff`. Give the three commands you run first and what each tells you.

<details><summary>Answer</summary>

`kubectl describe pod <p>` (events, last state, exit code, OOMKilled, probe failures); `kubectl logs <p> --previous` (output of the crashed run); `kubectl get pod <p> -o yaml` / `kubectl get events --sort-by=.lastTimestamp` (spec and wider context). → [02](../../kubernetes-foundations-to-advanced/02-core-workloads.md)
</details>

**B3.** Write the full DNS name of Pod `db-0` in StatefulSet `db` (headless Service `db`) in namespace `shop`, and of the Service `api` in `shop`.

<details><summary>Answer</summary>

`db-0.db.shop.svc.cluster.local` and `api.shop.svc.cluster.local`. → [02](../../kubernetes-foundations-to-advanced/02-core-workloads.md), [03](../../kubernetes-foundations-to-advanced/03-networking.md)
</details>

**B4.** Name the four Service types and say when to use each.

<details><summary>Answer</summary>

**ClusterIP** (internal, the default); **NodePort** (opens a port on every node, for dev or behind an external LB); **LoadBalancer** (cloud LB, external traffic); **ExternalName** (DNS CNAME to an outside service). Plus **headless** (`clusterIP: None`) for direct Pod DNS (StatefulSets). → [03](../../kubernetes-foundations-to-advanced/03-networking.md)
</details>

**B5.** What do PV reclaim policy `Retain` and access mode `RWOP` mean?

<details><summary>Answer</summary>

`Retain`: deleting the PVC keeps the disk and its data (manual cleanup), protecting production data from accidental deletion. `ReadWriteOncePod`: only **one Pod** in the whole cluster may mount the volume read-write. → [04](../../kubernetes-foundations-to-advanced/04-config-storage.md)
</details>

**B6.** Why must a liveness probe **not** check the database?

<details><summary>Answer</summary>

If the DB goes down, every Pod's liveness fails at once and they all restart in a loop, turning a DB outage into a full app outage that restarts can't fix. Liveness should only check "is this process wedged?". Put dependency checks in readiness (carefully). → [05](../../kubernetes-foundations-to-advanced/05-scheduling-scaling.md)
</details>

**B7.** What's the difference between a taint/toleration and node affinity?

<details><summary>Answer</summary>

A **taint** on a node *repels* Pods unless they *tolerate* it (a toleration allows, but doesn't attract). **Node affinity** on a Pod *attracts* it to matching nodes. For dedicated nodes you use both. → [05](../../kubernetes-foundations-to-advanced/05-scheduling-scaling.md)
</details>

**B8.** Name the 4Cs of cloud-native security, and two concrete controls at the Container level.

<details><summary>Answer</summary>

Cloud → Cluster → Container → Code. Container controls: run as non-root, read-only root FS, drop ALL capabilities, `allowPrivilegeEscalation: false`, seccomp `RuntimeDefault`, signed and scanned images. → [06](../../kubernetes-foundations-to-advanced/06-security.md)
</details>

---

## 🅲 Part C: Fix the Manifest (3 × 6 pts = 18)

**C1.** Find **at least six** problems in this Deployment.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api
spec:
  replicas: 1
  selector:
    matchLabels: { app: api }
  template:
    metadata:
      labels: { app: web }
    spec:
      containers:
        - name: api
          image: myorg/api:latest
          env:
            - name: DB_PASSWORD
              value: "hunter2"
          livenessProbe:
            httpGet: { path: /db-check, port: 8080 }
```

<details><summary>Answer</summary>

1. Selector `app: api` ≠ template label `app: web` → rejected by the API server.
2. `replicas: 1` → no HA (use ≥ 2 + a PDB + anti-affinity/topology spread).
3. `:latest` → pin a version or digest.
4. Plain-text password → `secretKeyRef` (+ external secrets/encryption at rest).
5. No resources requests/limits → BestEffort QoS, breaks HPA and scheduling.
6. Liveness hits the DB → cascading restarts; use a lightweight `/healthz`.
7. No readiness/startup probe.
8. No `securityContext` (non-root, read-only FS, drop caps, seccomp).
9. (Bonus) No namespace, no `containerPort`.

→ [02](../../kubernetes-foundations-to-advanced/02-core-workloads.md), [05](../../kubernetes-foundations-to-advanced/05-scheduling-scaling.md), [06](../../kubernetes-foundations-to-advanced/06-security.md)
</details>

**C2.** Write NetworkPolicies for namespace `shop`: default-deny all ingress, then allow only `app: api` Pods to reach `app: db` Pods on TCP 5432.

<details><summary>Answer</summary>

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata: { name: default-deny-ingress, namespace: shop }
spec:
  podSelector: {}
  policyTypes: [Ingress]
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata: { name: allow-api-to-db, namespace: shop }
spec:
  podSelector:
    matchLabels: { app: db }
  policyTypes: [Ingress]
  ingress:
    - from:
        - podSelector:
            matchLabels: { app: api }
      ports:
        - protocol: TCP
          port: 5432
```

Requires a CNI that enforces policy (Calico, Cilium…). If you also default-deny **egress**, allow DNS (UDP/TCP 53 to kube-dns). → [03](../../kubernetes-foundations-to-advanced/03-networking.md)
</details>

**C3.** Give a CI ServiceAccount `deployer` in namespace `shop` permission to get/list/update/patch Deployments only in that namespace. Then show how to verify it.

<details><summary>Answer</summary>

```yaml
apiVersion: v1
kind: ServiceAccount
metadata: { name: deployer, namespace: shop }
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata: { name: deployment-updater, namespace: shop }
rules:
  - apiGroups: ["apps"]
    resources: ["deployments"]
    verbs: ["get", "list", "update", "patch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata: { name: deployer-binding, namespace: shop }
subjects:
  - kind: ServiceAccount
    name: deployer
    namespace: shop
roleRef:
  kind: Role
  name: deployment-updater
  apiGroup: rbac.authorization.k8s.io
```

```bash
kubectl auth can-i patch deployments -n shop --as system:serviceaccount:shop:deployer     # yes
kubectl auth can-i delete deployments -n shop --as system:serviceaccount:shop:deployer    # no
kubectl auth can-i get secrets -n shop --as system:serviceaccount:shop:deployer           # no
kubectl auth can-i patch deployments -n default --as system:serviceaccount:shop:deployer  # no
```

→ [06](../../kubernetes-foundations-to-advanced/06-security.md)
</details>

---

## 🅳 Part D: Troubleshooting Scenarios (3 × 6 pts = 18)

**D1.** A new Pod has been `Pending` for 10 minutes. List the possible causes and how you'd confirm each.

<details><summary>Answer</summary>

`kubectl describe pod` → **Events** usually say why:

- `Insufficient cpu/memory`: requests too big or the cluster is full → lower requests or add nodes (CA/Karpenter).
- `node(s) had untolerated taint`: add a toleration or pick other nodes.
- `didn't match Pod's node affinity/selector`: fix labels/affinity.
- `pod has unbound immediate PersistentVolumeClaims`: check `kubectl get pvc`, the StorageClass and the provisioner.
- ResourceQuota exceeded (the Pod isn't even created; check the ReplicaSet's events).
- Topology spread / anti-affinity impossible with the current nodes.

→ [05](../../kubernetes-foundations-to-advanced/05-scheduling-scaling.md), [04](../../kubernetes-foundations-to-advanced/04-config-storage.md)
</details>

**D2.** After deploying v2, error rates spike. Give the commands to inspect and roll back, and two ways to make the next release safer.

<details><summary>Answer</summary>

```bash
kubectl rollout status deploy/api
kubectl rollout history deploy/api
kubectl rollout undo deploy/api                 # or --to-revision=N
```

Safer: a readiness probe that actually gates traffic + `maxUnavailable: 0`; canary/blue-green with Argo Rollouts or Flagger (automated metric analysis + abort); GitOps so rollback = git revert. → [02](../../kubernetes-foundations-to-advanced/02-core-workloads.md), [07](../../kubernetes-foundations-to-advanced/07-advanced.md)
</details>

**D3.** A node drain for an upgrade hangs forever. Why might that be, and how do you plan upgrades properly?

<details><summary>Answer</summary>

A **PodDisruptionBudget** blocks eviction (e.g. `minAvailable` equals the replica count, or a single-replica app with `minAvailable: 1`); Pods with local `emptyDir` need `--delete-emptydir-data`; DaemonSet Pods need `--ignore-daemonsets`. Planning: check deprecated APIs (`pluto`, `kubent`), upgrade control plane before nodes, one minor version at a time, surge-replace node pools, PDBs that allow at least 1 disruption, ≥ 2 replicas. → [05](../../kubernetes-foundations-to-advanced/05-scheduling-scaling.md), [07](../../kubernetes-foundations-to-advanced/07-advanced.md)
</details>

---

## 🧮 Scoring

| Score | Level |
|-------|-------|
| 90–100 | 🔴 Advanced: ready to operate production clusters |
| 70–89 | 🟡 Intermediate: pass, review missed chapters |
| < 70 | 🟢 Beginner: redo [playbook](playbook.md) labs 1–5 and retake |

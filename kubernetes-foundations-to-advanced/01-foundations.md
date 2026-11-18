# 01 · Foundations & Architecture 🟢

[← Index](README.md) · [Next: Core Workloads →](02-core-workloads.md)

## Why Kubernetes?

Containers package an app. **Kubernetes (K8s)** runs many containers across many machines and keeps them healthy.

```
  Without an orchestrator               With Kubernetes
  ─────────────────────────             ─────────────────────────────
  ssh server1 && docker run ...         kubectl apply -f app.yaml
  ssh server2 && docker run ...           ✔ placement (scheduling)
  app crashed at 3am? → you wake up       ✔ self-healing restarts
  traffic spike? → manual scale           ✔ autoscaling
  new version? → pray                     ✔ rolling updates & rollback
                                          ✔ service discovery & load balancing
```

## 🏛️ Cluster Architecture

```mermaid
flowchart TB
    user([👤 kubectl / CI / GitOps]) -->|HTTPS REST| api

    subgraph CP["🧠 Control Plane"]
        api[kube-apiserver<br/>front door]
        etcd[(etcd<br/>key-value store)]
        sched[kube-scheduler<br/>picks nodes]
        cm[controller-manager<br/>reconcile loops]
        ccm[cloud-controller-manager<br/>LBs, disks, nodes]
        api <--> etcd
        sched --> api
        cm --> api
        ccm --> api
    end

    subgraph N1["🖥️ Worker Node 1"]
        k1[kubelet] --> cr1[container runtime<br/>containerd / CRI-O]
        p1[kube-proxy]
        cr1 --> podA((Pod)) & podB((Pod))
    end

    subgraph N2["🖥️ Worker Node 2"]
        k2[kubelet] --> cr2[container runtime]
        p2[kube-proxy]
        cr2 --> podC((Pod))
    end

    api <--> k1
    api <--> k2
```

### Control plane components

| Component | Role | Analogy |
|-----------|------|---------|
| **kube-apiserver** | The only component that talks to etcd. Validates and stores every object | Reception desk |
| **etcd** | Distributed, consistent key-value store holding the cluster state | The ledger |
| **kube-scheduler** | Assigns unscheduled Pods to a node based on resources and constraints | Seating host |
| **kube-controller-manager** | Runs controllers (Deployment, ReplicaSet, Node, Job...) | Managers on patrol |
| **cloud-controller-manager** | Integrates with the cloud (LoadBalancers, volumes, node lifecycle) | Cloud liaison |

### Node components

| Component | Role |
|-----------|------|
| **kubelet** | Agent on each node. Makes sure the Pods assigned to it are running |
| **Container runtime** | Pulls images and runs containers (containerd, CRI-O) through the **CRI** |
| **kube-proxy** | Programs iptables/IPVS rules for Services (some CNIs such as Cilium replace it with eBPF) |
| **CNI plugin** | Gives Pods IPs and connects them (Calico, Cilium, Flannel) |

## 🔁 The Reconciliation Loop

Every controller runs the same loop:

```mermaid
flowchart LR
    O[Observe<br/>actual state] --> D{Diff with<br/>desired state}
    D -->|match| O
    D -->|drift| A[Act<br/>create / delete / update]
    A --> O
```

**Example:** you ask for `replicas: 3`. A node dies and takes one Pod with it. The ReplicaSet controller sees 2 ≠ 3 and creates a new Pod. Nobody gets paged.

## 🚶 What Happens on `kubectl apply`?

```mermaid
sequenceDiagram
    autonumber
    participant U as kubectl
    participant A as API Server
    participant E as etcd
    participant C as Deployment Ctrl
    participant S as Scheduler
    participant K as kubelet (node)

    U->>A: POST Deployment (YAML)
    A->>A: AuthN → AuthZ → Admission
    A->>E: persist Deployment
    C->>A: watch: new Deployment
    C->>A: create ReplicaSet → Pods (Pending)
    S->>A: watch: unscheduled Pods
    S->>A: bind Pod → node-2
    K->>A: watch: Pod bound to me
    K->>K: pull image, start containers
    K->>A: status: Running ✅
```

> 💡 Components never talk directly to each other. They all **watch the API server**. This loose coupling is what makes Kubernetes extensible.

## 📄 Anatomy of a Kubernetes Object

```yaml
apiVersion: apps/v1          # API group + version
kind: Deployment             # object type
metadata:                    # identity
  name: web
  namespace: shop
  labels: { app: web, tier: frontend }
spec:                        # ✍️ DESIRED state (you write this)
  replicas: 3
  ...
status:                      # 👀 ACTUAL state (K8s writes this)
  readyReplicas: 3
```

## 🏷️ Namespaces, Labels & Selectors

```
Cluster
├── namespace: kube-system   (K8s internals)
├── namespace: default
├── namespace: shop-dev
│     ├── Deployment web   labels: app=web, env=dev
│     └── Deployment api   labels: app=api, env=dev
└── namespace: shop-prod
      ├── Deployment web   labels: app=web, env=prod
      └── Deployment api   labels: app=api, env=prod
```

- **Namespaces** give names a scope and are where quotas and RBAC apply. They are *not* a hard security boundary by themselves.
- **Labels** are key/value tags. **Selectors** query them: `kubectl get pods -l app=web,env=prod`.
- **Annotations** hold non-identifying metadata (build info, tool config).

## ✅ Key Takeaways

- K8s = **declarative desired state** + **controllers that reconcile**.
- The **API server** is the hub, and **etcd** is the source of truth.
- The **scheduler** decides *where*, and the **kubelet** makes it *happen*.
- Everything is an object with `apiVersion`, `kind`, `metadata`, `spec`, `status`.

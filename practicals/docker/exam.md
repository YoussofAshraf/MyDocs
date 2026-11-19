# 🐳 Docker Exam

[← Practicals](../README.md) · [Playbook →](playbook.md) · [Guide](../../docker-foundations-to-advanced/README.md)

| | |
|--|--|
| ⏱️ Time | 90 minutes |
| 🎯 Pass mark | 70 / 100 |
| 📚 Covers | Chapters 01–08 of [Docker: Foundations to Advanced](../../docker-foundations-to-advanced/README.md) |
| 🧭 Rules | Closed book for Parts A–B. Parts C–D may use a terminal |

Every answer is hidden under **Answer**. Each one cites the chapter to re-read if you got it wrong.

---

## 🅰️ Part A: Multiple Choice (20 × 2 pts = 40)

**A1.** Which component actually creates the container's namespaces and cgroups, and then exits?

- a) dockerd
- b) containerd
- c) containerd-shim
- d) runc

<details><summary>Answer</summary>

**d) runc.** containerd manages lifecycle, the shim keeps the container alive if dockerd/containerd restarts, and runc is the low-level OCI runtime that creates the container and exits. → [01](../../docker-foundations-to-advanced/01-foundations.md)
</details>

**A2.** Ten containers are started from the same 300 MB image. Roughly how much disk do they use?

- a) 3 GB
- b) 300 MB + ten small writable layers
- c) 300 MB exactly, writable layers live in RAM
- d) It depends on the number of `EXPOSE` lines

<details><summary>Answer</summary>

**b).** Layers are content-addressed and shared; each container adds only a thin copy-on-write layer. → [01](../../docker-foundations-to-advanced/01-foundations.md#-image-vs-container)
</details>

**A3.** What does `nginx` expand to as a full image reference?

- a) `hub.docker.com/nginx:stable`
- b) `docker.io/nginx/nginx:latest`
- c) `docker.io/library/nginx:latest`
- d) `registry-1.docker.io/official/nginx`

<details><summary>Answer</summary>

**c).** → [01](../../docker-foundations-to-advanced/01-foundations.md)
</details>

**A4.** Why pin production images by **digest** rather than by tag?

- a) Digests download faster
- b) Tags can be moved to a different image; digests are immutable
- c) Tags don't work with private registries
- d) Digests enable multi-arch builds

<details><summary>Answer</summary>

**b).** → [01](../../docker-foundations-to-advanced/01-foundations.md)
</details>

**A5.** You need the strongest isolation for running untrusted customer code, with each container getting its own kernel. Which runtime fits?

- a) runc
- b) crun
- c) gVisor
- d) Kata Containers

<details><summary>Answer</summary>

**d) Kata Containers** uses lightweight VMs, so each container has a real kernel. gVisor intercepts syscalls in a user-space kernel (strong, but not a separate real kernel). → [01](../../docker-foundations-to-advanced/01-foundations.md#2-sandboxed-runtimes-isolated-kernel)
</details>

**A6.** Which Dockerfile instruction is available **only at build time**?

- a) `ENV`
- b) `ARG`
- c) `LABEL`
- d) `USER`

<details><summary>Answer</summary>

**b) `ARG`.** `ENV` persists into the runtime. → [02](../../docker-foundations-to-advanced/02-images-dockerfile.md#-instruction-reference)
</details>

**A7.** Given `ENTRYPOINT ["python","app.py"]` and `CMD ["--port","8000"]`, what runs with `docker run img --port 9000`?

- a) `python app.py --port 8000 --port 9000`
- b) `python app.py --port 9000`
- c) `--port 9000`
- d) `sh -c --port 9000`

<details><summary>Answer</summary>

**b).** Extra arguments replace `CMD`; `ENTRYPOINT` stays. → [02](../../docker-foundations-to-advanced/02-images-dockerfile.md#entrypoint-vs-cmd)
</details>

**A8.** A container takes the full 10 seconds to stop every time and exits with code 137. The Dockerfile ends with `CMD node server.js`. Most likely cause?

- a) The memory limit is too low
- b) Shell form wraps the process in `/bin/sh -c`, so `SIGTERM` never reaches node
- c) `EXPOSE` is missing
- d) The restart policy is `always`

<details><summary>Answer</summary>

**b).** Use the exec form `CMD ["node","server.js"]` (and/or `--init`). → [02](../../docker-foundations-to-advanced/02-images-dockerfile.md#entrypoint-vs-cmd), [03](../../docker-foundations-to-advanced/03-containers.md#-graceful-shutdown)
</details>

**A9.** In this Dockerfile, which line is the **first** cache miss after you edit `server.js`?

```dockerfile
FROM node:22-slim
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
CMD ["node","server.js"]
```

- a) `FROM`
- b) `COPY package*.json ./`
- c) `RUN npm ci`
- d) `COPY . .`

<details><summary>Answer</summary>

**d).** Everything before it stays cached, everything after it is rebuilt. → [02](../../docker-foundations-to-advanced/02-images-dockerfile.md#-layers--the-build-cache)
</details>

**A10.** What does `EXPOSE 3000` do?

- a) Publishes port 3000 on the host
- b) Opens port 3000 in the host firewall
- c) Documents the port; it does not publish it
- d) Makes the container listen on 3000

<details><summary>Answer</summary>

**c).** Publishing needs `-p` (or `-P`, which publishes every `EXPOSE`d port to a random host port). → [02](../../docker-foundations-to-advanced/02-images-dockerfile.md#-dockerfile-the-recipe), [04](../../docker-foundations-to-advanced/04-networking.md#-publishing-ports)
</details>

**A11.** Exit code `127` means:

- a) OOM-killed
- b) Command not found
- c) Graceful SIGTERM
- d) The docker CLI itself failed

<details><summary>Answer</summary>

**b).** 125 = docker failed, 126 = not executable, 137 = SIGKILL/OOM, 143 = SIGTERM. → [03](../../docker-foundations-to-advanced/03-containers.md#exit-codes-cheat-sheet)
</details>

**A12.** Which restart policy restarts a container after a daemon restart **unless you stopped it manually**?

- a) `no`
- b) `on-failure:3`
- c) `always`
- d) `unless-stopped`

<details><summary>Answer</summary>

**d).** → [03](../../docker-foundations-to-advanced/03-containers.md#-restart-policies)
</details>

**A13.** Two containers on the **default** bridge can't reach each other by name. Best fix?

- a) Use `--link`
- b) Put both on a user-defined bridge network
- c) Switch both to `--network none`
- d) Publish both ports with `-p`

<details><summary>Answer</summary>

**b).** User-defined bridges provide embedded DNS (127.0.0.11) by container name. → [04](../../docker-foundations-to-advanced/04-networking.md)
</details>

**A14.** You publish Postgres with `-p 5432:5432` on a server with UFW denying 5432. What happens?

- a) UFW blocks it
- b) It's reachable from every interface, because Docker writes its own iptables rules
- c) Only localhost can reach it
- d) Docker refuses to start the container

<details><summary>Answer</summary>

**b).** Bind to `127.0.0.1:5432:5432` or put a proxy in front. → [04](../../docker-foundations-to-advanced/04-networking.md#-publishing-ports)
</details>

**A15.** What does `docker network create --internal backend-net` give you?

- a) A network with no outbound internet access
- b) A network only visible to the host
- c) A multi-host overlay
- d) A network with IPv6 only

<details><summary>Answer</summary>

**a).** → [04](../../docker-foundations-to-advanced/04-networking.md#-isolating-tiers-with-multiple-networks)
</details>

**A16.** You mount an **empty named volume** at a path where the image already has files. Result?

- a) The image's files are hidden
- b) The volume is pre-populated with the image's files
- c) The container fails to start
- d) The files are merged read-only

<details><summary>Answer</summary>

**b).** A bind mount would **hide** them instead. → [05](../../docker-foundations-to-advanced/05-storage.md#-volumes)
</details>

**A17.** `-v /does/not/exist:/data` vs `--mount type=bind,src=/does/not/exist,dst=/data`:

- a) Both fail
- b) Both create the directory
- c) `-v` silently creates an empty directory; `--mount` errors
- d) `--mount` creates it; `-v` errors

<details><summary>Answer</summary>

**c).** → [05](../../docker-foundations-to-advanced/05-storage.md#-v-vs---mount)
</details>

**A18.** In Compose, `api` crashes with "connection refused" on startup because `db` is still initialising. The fix?

- a) `depends_on: [db]`
- b) `depends_on: { db: { condition: service_healthy } }` plus a `healthcheck` on `db`
- c) `restart: always` on `db`
- d) `links: [db]`

<details><summary>Answer</summary>

**b).** Plain `depends_on` only waits for the container to **start**. → [06](../../docker-foundations-to-advanced/06-compose.md)
</details>

**A19.** Which command is the most dangerous for data?

- a) `docker compose down`
- b) `docker compose stop`
- c) `docker compose down -v`
- d) `docker compose rm`

<details><summary>Answer</summary>

**c).** `-v` also removes named volumes. → [06](../../docker-foundations-to-advanced/06-compose.md#-everyday-commands)
</details>

**A20.** Which is the correct way to use an npm token during a build without it ending up in the image?

- a) `ARG NPM_TOKEN`
- b) `ENV NPM_TOKEN=...` then `RUN unset NPM_TOKEN`
- c) `COPY .npmrc .` then `RUN rm .npmrc`
- d) `RUN --mount=type=secret,id=npmrc,target=/root/.npmrc npm ci`

<details><summary>Answer</summary>

**d).** a–c all leave the secret in layer history or metadata. → [07](../../docker-foundations-to-advanced/07-security.md#-secrets-never-in-the-image)
</details>

---

## 🅱️ Part B: Short Answer (8 × 3 pts = 24)

**B1.** Explain the difference between a VM and a container in two sentences, and name the main isolation trade-off.

<details><summary>Answer</summary>

A VM virtualises hardware and runs a full guest OS on a hypervisor; a container is an isolated, limited **process** sharing the host kernel. Containers are lighter and faster, but the shared kernel makes isolation weaker (a kernel exploit = escape), which gVisor/Kata mitigate. → [01](../../docker-foundations-to-advanced/01-foundations.md#-containers-vs-virtual-machines)
</details>

**B2.** Rewrite these three lines so the image doesn't keep the apt cache, and explain why the original fails.

```dockerfile
RUN apt-get update
RUN apt-get install -y curl
RUN rm -rf /var/lib/apt/lists/*
```

<details><summary>Answer</summary>

```dockerfile
RUN apt-get update \
 && apt-get install -y --no-install-recommends curl \
 && rm -rf /var/lib/apt/lists/*
```

Each `RUN` is a layer. Deleting files in a later layer only hides them; the bytes still live in the earlier layer. Cleaning in the same `RUN` means they're never committed. → [02](../../docker-foundations-to-advanced/02-images-dockerfile.md#keep-layers-small)
</details>

**B3.** Name two benefits of a multi-stage build and the flag that stops at an intermediate stage.

<details><summary>Answer</summary>

Smaller final image (no compilers/toolchains) and smaller attack surface; build tools stay in the discarded stage. `docker build --target <stage>`. → [02](../../docker-foundations-to-advanced/02-images-dockerfile.md)
</details>

**B4.** Describe exactly what `docker stop` does, including the default timing.

<details><summary>Answer</summary>

Sends `SIGTERM` to PID 1, waits the grace period (10 s by default, `-t`/`--stop-timeout`), then sends `SIGKILL`. → [03](../../docker-foundations-to-advanced/03-containers.md#-graceful-shutdown)
</details>

**B5.** Give three ways to fix "Permission denied" when a container running as uid 999 writes to a bind-mounted folder owned by uid 1000.

<details><summary>Answer</summary>

Any three: run with `-u $(id -u):$(id -g)`; `COPY --chown`/`chown` in the Dockerfile; use a named volume instead; on SELinux hosts add `:z`/`:Z`. → [05](../../docker-foundations-to-advanced/05-storage.md#-permissions-gotcha)
</details>

**B6.** How does Compose load `compose.override.yaml`, and how do you run with production settings instead?

<details><summary>Answer</summary>

`docker compose up` loads `compose.yaml` + `compose.override.yaml` automatically. For prod: `docker compose -f compose.yaml -f compose.prod.yaml up -d` (the override is then not loaded). → [06](../../docker-foundations-to-advanced/06-compose.md#-layering-files-per-environment)
</details>

**B7.** List five red-flag `docker run` options/mounts from a security review and why each is dangerous.

<details><summary>Answer</summary>

`--privileged` (near-full host access), `-v /var/run/docker.sock` (root on host), `-v /:/host` (host filesystem), `--pid host`/`--network host` (removes isolation), `--cap-add SYS_ADMIN` ("the new root"). → [07](../../docker-foundations-to-advanced/07-security.md#-red-flags)
</details>

**B8.** Why cross-compile with `--platform=$BUILDPLATFORM` instead of emulating with QEMU, and which build args make it work?

<details><summary>Answer</summary>

QEMU emulation is slow. Running the build stage natively and compiling for the target is far faster. `TARGETOS` and `TARGETARCH` (e.g. `GOOS=$TARGETOS GOARCH=$TARGETARCH go build`). → [08](../../docker-foundations-to-advanced/08-advanced.md#-multi-architecture-images)
</details>

---

## 🅲 Part C: Fix the Config (3 × 6 pts = 18)

**C1.** Find **six** problems in this Dockerfile and rewrite it.

```dockerfile
FROM node:22
ADD . /app
WORKDIR /app
ENV NPM_TOKEN=npm_abc123
RUN npm install
RUN apt-get update && apt-get install -y curl
EXPOSE 3000
CMD npm start
```

<details><summary>Answer</summary>

1. Full `node:22` base (~1 GB) → use `node:22-slim` (or distroless in a multi-stage build).
2. `ADD` instead of `COPY`.
3. Copies all source **before** installing deps → every code change reinstalls.
4. Secret in `ENV` → baked in forever; use a BuildKit secret mount.
5. `npm install` instead of reproducible `npm ci --omit=dev`.
6. apt cache not cleaned / no `--no-install-recommends`.
7. Runs as root (no `USER`).
8. Shell-form `CMD` → no SIGTERM.
9. (Bonus) no `.dockerignore` implied; `node_modules`/`.env` could be copied.

```dockerfile
# syntax=docker/dockerfile:1
FROM node:22-slim
RUN apt-get update \
 && apt-get install -y --no-install-recommends curl \
 && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY package*.json ./
RUN --mount=type=secret,id=npmrc,target=/root/.npmrc npm ci --omit=dev
COPY --chown=node:node . .
ENV NODE_ENV=production
EXPOSE 3000
USER node
CMD ["node", "server.js"]
```

→ [02](../../docker-foundations-to-advanced/02-images-dockerfile.md), [07](../../docker-foundations-to-advanced/07-security.md)
</details>

**C2.** Harden this command for production. State what each added flag protects against.

```bash
docker run -d -p 8080:8080 myorg/api:latest
```

<details><summary>Answer</summary>

```bash
docker run -d --name api \
  --user 10001:10001 \
  --read-only --tmpfs /tmp:size=64m \
  --cap-drop ALL \
  --security-opt no-new-privileges:true \
  --memory 512m --cpus 1 --pids-limit 200 \
  --restart unless-stopped \
  -p 127.0.0.1:8080:8080 \
  myorg/api@sha256:<digest>
```

Non-root (root mapping to host powers), read-only FS (tampering), drop caps (raw sockets/mount/chown abuse), no-new-privileges (setuid escalation), limits (DoS/fork bombs), localhost bind (firewall bypass), digest instead of `:latest` (tag hijack/silent change). → [07](../../docker-foundations-to-advanced/07-security.md#-a-hardened-docker-run)
</details>

**C3.** Fix this `compose.yaml` (find at least five issues).

```yaml
version: "3.8"
services:
  api:
    build: ./api
    ports: ["3000:3000"]
    environment:
      DATABASE_URL: postgres://app:hunter2@localhost:5432/shop
    depends_on: [db]
  db:
    image: postgres:latest
    environment:
      POSTGRES_PASSWORD: hunter2
```

<details><summary>Answer</summary>

1. `version:` is obsolete → remove.
2. `localhost` inside `api` means the api container itself → use the service name `db`.
3. Hard-coded password → `${DB_PASSWORD}` from a git-ignored `.env` (or Compose secrets).
4. No volume for Postgres data → data lost on `down`/recreate.
5. `depends_on` without health → add `healthcheck` + `condition: service_healthy`.
6. `postgres:latest` → pin a version (`postgres:17`).
7. Port published on all interfaces → `127.0.0.1:3000:3000`.
8. (Bonus) no restart policy / resource limits on `api`.

→ [06](../../docker-foundations-to-advanced/06-compose.md#-composeyaml)
</details>

---

## 🅳 Part D: Troubleshooting Scenarios (3 × 6 pts = 18)

**D1.** A worker container restarts every few minutes. `docker inspect -f '{{.State.ExitCode}} {{.State.OOMKilled}}' worker` prints `137 true`. Walk through diagnosis and two fixes.

<details><summary>Answer</summary>

137 + `OOMKilled=true` = the kernel killed it at the cgroup memory limit. Check `docker stats worker` for growth and `docker inspect` for `HostConfig.Memory`. Fixes: raise the limit (`docker update --memory 1g worker`) if the workload legitimately needs it; fix the leak / cap batch sizes / tune runtime heap (e.g. `--max-old-space-size`, JVM `-XX:MaxRAMPercentage`). → [03](../../docker-foundations-to-advanced/03-containers.md#-resource-limits-cgroups)
</details>

**D2.** `curl localhost:8080` from the host fails, but `docker exec web curl localhost:80` works. List what you'd check, in order.

<details><summary>Answer</summary>

1. `docker ps` / `docker port web`: is 8080 actually published, and to which container port?
2. Port mapping direction (`-p 8080:80`, host:container) and bind address (`127.0.0.1` vs another IP).
3. The app listens on `127.0.0.1` inside the container instead of `0.0.0.0`, so published traffic can't reach it.
4. Another process already holds host port 8080 (`ss -tlnp`).
5. Is the container attached to `--network none`/an `--internal` network?

Use `docker run --network container:web nicolaka/netshoot ss -tlnp` to see the listening socket. → [04](../../docker-foundations-to-advanced/04-networking.md)
</details>

**D3.** The host disk is 95% full. Which commands tell you what Docker is using, and which cleanups are safe vs destructive?

<details><summary>Answer</summary>

`docker system df` (and `-v` for detail). Safe-ish: `docker container prune`, `docker image prune` (dangling), `docker builder prune`. More aggressive: `docker image prune -a` (all unused images, pulls again later). **Destructive:** `docker volume prune` and `docker system prune -a --volumes` (deletes data). Also check for unrotated container logs → set `log-opts` `max-size`/`max-file` in `daemon.json`. → [03](../../docker-foundations-to-advanced/03-containers.md#-cleanup), [08](../../docker-foundations-to-advanced/08-advanced.md#-production-patterns)
</details>

---

## 🧮 Scoring

| Score | Level |
|-------|-------|
| 90–100 | 🔴 Advanced: ready for production ownership |
| 70–89 | 🟡 Intermediate: pass, review missed chapters |
| < 70 | 🟢 Beginner: redo the [playbook](playbook.md) labs 1–5 and retake |

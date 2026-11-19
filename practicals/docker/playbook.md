# 🐳 Docker Playbook

[← Practicals](../README.md) · [Exam →](exam.md) · [Guide](../../docker-foundations-to-advanced/README.md)

Hands-on labs (Part 1) and incident runbooks (Part 2). Every lab has **Goal → Steps → ✅ Verify → 🧹 Cleanup**.

## 🧰 Prerequisites

```bash
docker version            # Engine 25+ recommended (BuildKit is the default builder)
docker compose version    # Compose v2
mkdir -p ~/docker-labs && cd ~/docker-labs
```

---

# Part 1 · 🧪 Labs

## Lab 1 · Image vs Container & the Writable Layer 🟢

**Goal:** see that changes live in the container layer and vanish with `rm`. → [ch. 01](../../docker-foundations-to-advanced/01-foundations.md)

```bash
docker run -d --name l1 nginx:1.27-alpine
docker exec l1 sh -c 'echo hello > /usr/share/nginx/html/new.html'
docker diff l1                       # A /usr/share/nginx/html/new.html
docker rm -f l1
docker run -d --name l1 nginx:1.27-alpine
docker exec l1 ls /usr/share/nginx/html   # new.html is gone
```

✅ **Verify:** `docker diff` showed `A` (added) and `C` (changed) entries; the file is absent in the new container.

🧠 **Explain:** why do 10 containers from this image barely use more disk than one? (Shared read-only layers + CoW.)

🧹 `docker rm -f l1`

---

## Lab 2 · Build Cache & Layer Order 🟢

**Goal:** measure the cost of bad instruction order. → [ch. 02](../../docker-foundations-to-advanced/02-images-dockerfile.md)

```bash
mkdir -p lab2 && cd lab2
cat > package.json <<'EOF'
{ "name": "lab2", "version": "1.0.0", "dependencies": { "express": "^4.21.0" } }
EOF
cat > server.js <<'EOF'
const app = require('express')();
app.get('/', (_, res) => res.send('v1\n'));
const srv = app.listen(3000, () => console.log('listening'));
process.on('SIGTERM', () => { console.log('SIGTERM, closing'); srv.close(() => process.exit(0)); });
EOF
printf 'node_modules\n.git\n*.log\n.env\n' > .dockerignore

cat > Dockerfile.slow <<'EOF'
FROM node:22-slim
WORKDIR /app
COPY . .
RUN npm install
CMD ["node", "server.js"]
EOF

cat > Dockerfile.fast <<'EOF'
# syntax=docker/dockerfile:1
FROM node:22-slim
WORKDIR /app
COPY package*.json ./
RUN npm install --omit=dev
COPY . .
USER node
CMD ["node", "server.js"]
EOF

docker build -f Dockerfile.slow -t lab2:slow .
docker build -f Dockerfile.fast -t lab2:fast .
```

Now change the source and rebuild both, timing them:

```bash
sed -i 's/v1/v2/' server.js
time docker build -f Dockerfile.slow -t lab2:slow .
time docker build -f Dockerfile.fast -t lab2:fast .
```

✅ **Verify:** the `fast` build output shows `CACHED` for `RUN npm install`; the `slow` one reruns it.

```bash
docker image history lab2:fast       # one row per layer, with size
```

🎯 **Stretch:** add `RUN --mount=type=cache,target=/root/.npm npm install --omit=dev` and change a dependency version: npm re-downloads nothing. → [ch. 08](../../docker-foundations-to-advanced/08-advanced.md)

🧹 `cd .. && docker rmi lab2:slow lab2:fast`

---

## Lab 3 · Multi-Stage Build to Distroless 🟢

**Goal:** ship a ~10 MB image from an ~800 MB toolchain. → [ch. 02](../../docker-foundations-to-advanced/02-images-dockerfile.md)

```bash
mkdir -p lab3 && cd lab3
cat > go.mod <<'EOF'
module lab3
go 1.23
EOF
cat > main.go <<'EOF'
package main

import ("fmt"; "net/http")

func main() {
	http.HandleFunc("/", func(w http.ResponseWriter, _ *http.Request) { fmt.Fprintln(w, "hello from distroless") })
	http.ListenAndServe(":8080", nil)
}
EOF
cat > Dockerfile <<'EOF'
# syntax=docker/dockerfile:1
FROM golang:1.23 AS build
WORKDIR /src
COPY go.mod ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 go build -o /out/app .

FROM gcr.io/distroless/static-debian12:nonroot AS final
COPY --from=build /out/app /app
USER nonroot
ENTRYPOINT ["/app"]
EOF

docker build -t lab3:final .
docker build -t lab3:build --target build .
docker images lab3
docker run -d --name l3 -p 127.0.0.1:8080:8080 lab3:final
curl -s localhost:8080
```

✅ **Verify:** `lab3:final` is a few MB; `lab3:build` is hundreds of MB. `docker exec l3 sh` **fails** (no shell in distroless, which is exactly the point).

🧹 `docker rm -f l3 && cd ..`

---

## Lab 4 · Signals, Exit Codes & OOM 🟢

**Goal:** observe 0 / 137 / 143 and why exec form matters. → [ch. 03](../../docker-foundations-to-advanced/03-containers.md)

```bash
# 1) Shell form ignores SIGTERM → waits the full timeout → SIGKILL (137)
docker run -d --name shellform alpine sh -c 'sleep 300'
time docker stop shellform                 # ≈ 10s
docker inspect -f '{{.State.ExitCode}}' shellform

# 2) --init forwards the signal → fast stop
docker run -d --init --name withinit alpine sleep 300
time docker stop withinit                  # ≈ instant
docker inspect -f '{{.State.ExitCode}}' withinit

# 3) OOM kill
docker run --name oom --memory 64m --memory-swap 64m python:3.13-slim \
  python -c "x = bytearray(300 * 1024 * 1024)"
docker inspect -f 'exit={{.State.ExitCode}} oom={{.State.OOMKilled}}' oom

# 4) Command not found
docker run --name nf alpine doesnotexist; echo "exit: $?"
```

✅ **Verify:** (1) ≈10 s and `137`; (2) near-instant and `143`; (3) `exit=137 oom=true`; (4) exit `127`.

🎯 **Stretch:** run the Lab 2 image, `docker stop` it and `docker logs` it: you should see `SIGTERM, closing`.

🧹 `docker rm -f shellform withinit oom nf`

---

## Lab 5 · Restart Policies & Limits 🟢

```bash
docker run -d --name flaky --restart on-failure:3 alpine sh -c 'echo boom; exit 1'
sleep 15
docker inspect -f 'restarts={{.RestartCount}} status={{.State.Status}}' flaky

docker run -d --name capped --cpus 0.5 --memory 128m --pids-limit 50 alpine sleep 600
docker stats --no-stream capped
docker update --memory 256m --memory-swap 256m capped
docker inspect -f '{{.HostConfig.Memory}}' capped
```

✅ **Verify:** `flaky` stops at `restarts=3 status=exited`. `capped` shows a 128 MiB then 256 MiB limit.

🧹 `docker rm -f flaky capped`

---

## Lab 6 · Networking: DNS, Ports & Tier Isolation 🟡

**Goal:** prove the default-bridge DNS gap and build an internal backend tier. → [ch. 04](../../docker-foundations-to-advanced/04-networking.md)

```bash
# Default bridge: no name resolution
docker run -d --name db0 -e POSTGRES_PASSWORD=x postgres:17
docker run --rm alpine ping -c1 db0          # bad address 'db0'

# User-defined bridges
docker network create frontend-net
docker network create --internal backend-net
docker run -d --name db  --network backend-net -e POSTGRES_PASSWORD=x postgres:17
docker run -d --name api --network frontend-net nginx:1.27-alpine
docker network connect backend-net api

docker exec api ping -c1 db                  # ✅ api is on both networks
docker run --rm --network frontend-net alpine ping -c1 -W2 db   # ❌ not resolvable
docker run --rm --network backend-net alpine wget -T3 -qO- https://example.com  # ❌ internal: no internet

# Look inside a container's network namespace
docker run --rm --network container:api nicolaka/netshoot ss -tlnp
docker network inspect backend-net -f '{{range .Containers}}{{.Name}} {{end}}'
```

✅ **Verify:** only `api` reaches `db`; the backend network has no outbound access; netshoot shows nginx listening on `:80`.

🎯 **Stretch:** run `docker run -d -p 8081:80 nginx` and `docker run -d -p 127.0.0.1:8082:80 nginx`, then compare `ss -tlnp | grep 808` on the host (`0.0.0.0` vs `127.0.0.1`).

🧹 `docker rm -f db0 db api; docker network rm frontend-net backend-net`

---

## Lab 7 · Storage: Persistence, Backup & Restore 🟡

**Goal:** keep data across container deletion and round-trip a backup. → [ch. 05](../../docker-foundations-to-advanced/05-storage.md)

```bash
docker volume create pgdata
docker run -d --name pg -e POSTGRES_PASSWORD=secret -v pgdata:/var/lib/postgresql/data postgres:17
sleep 5
docker exec pg psql -U postgres -c "CREATE TABLE t(v text); INSERT INTO t VALUES ('survived');"

docker rm -f pg
docker run -d --name pg2 -e POSTGRES_PASSWORD=secret -v pgdata:/var/lib/postgresql/data postgres:17
sleep 5
docker exec pg2 psql -U postgres -c "SELECT * FROM t;"      # survived ✅

# App-consistent dump (preferred for DBs)
docker exec pg2 pg_dump -U postgres > dump.sql

# Raw volume backup (stop the DB first for consistency)
docker stop pg2
docker run --rm -v pgdata:/data:ro -v "$PWD":/backup alpine tar czf /backup/pgdata.tgz -C /data .
docker run --rm -v pgdata-new:/data -v "$PWD":/backup alpine tar xzf /backup/pgdata.tgz -C /data
docker run -d --name pg3 -e POSTGRES_PASSWORD=secret -v pgdata-new:/var/lib/postgresql/data postgres:17
sleep 5
docker exec pg3 psql -U postgres -c "SELECT * FROM t;"
```

**`-v` vs `--mount` gotcha:**

```bash
docker run --rm -v /tmp/nope-$$:/data alpine ls /data; ls -ld /tmp/nope-$$     # created silently
docker run --rm --mount type=bind,src=/tmp/nope2-$$,dst=/data alpine ls /data  # error ✅
```

✅ **Verify:** `survived` is returned from `pg2` and from the restored `pg3`.

🧹 `docker rm -f pg2 pg3; docker volume rm pgdata pgdata-new; rm -f dump.sql pgdata.tgz`

---

## Lab 8 · Compose: Health-Gated Startup, Profiles, Scale 🟡

**Goal:** run a multi-service app the way [ch. 06](../../docker-foundations-to-advanced/06-compose.md) recommends.

```bash
mkdir -p lab8 && cd lab8
echo 'DB_PASSWORD=change-me' > .env
cat > compose.yaml <<'EOF'
name: lab8
services:
  api:
    image: postgres:17          # stand-in "api" that just needs the DB
    command: ["sh", "-c", "until psql \"$$DATABASE_URL\" -c 'select 1'; do sleep 1; done; echo CONNECTED; sleep infinity"]
    environment:
      DATABASE_URL: postgres://app:${DB_PASSWORD}@db:5432/shop
    depends_on:
      db: { condition: service_healthy }
  worker:
    image: alpine
    command: ["sh", "-c", "echo worker $$HOSTNAME up; sleep infinity"]
  db:
    image: postgres:17
    environment:
      POSTGRES_USER: app
      POSTGRES_DB: shop
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes: ["pgdata:/var/lib/postgresql/data"]
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U app -d shop"]
      interval: 3s
      retries: 20
  adminer:
    image: adminer
    ports: ["127.0.0.1:8081:8080"]
    profiles: [debug]
volumes:
  pgdata:
EOF

docker compose config | grep DATABASE_URL     # interpolation resolved
docker compose up -d
docker compose ps                             # db (healthy) before api starts
docker compose logs api | grep CONNECTED
docker compose up -d --scale worker=3
docker compose ps worker
docker compose --profile debug up -d          # adminer now on 127.0.0.1:8081
```

✅ **Verify:** `api` prints `CONNECTED` on its first attempt; three `worker` replicas exist; adminer only appears with the profile.

🎯 **Stretch:** remove the `condition: service_healthy` line, `down -v`, `up -d` again, and count failed `psql` attempts in the `api` logs.

🧹 `docker compose --profile debug down -v && cd ..`

---

## Lab 9 · Security Hardening & Secrets 🔴

**Goal:** verify each hardening flag actually blocks something. → [ch. 07](../../docker-foundations-to-advanced/07-security.md)

```bash
# 1) Root vs non-root
docker run --rm alpine id                           # uid=0(root)
docker run --rm --user 10001:10001 alpine id        # uid=10001

# 2) Read-only root FS with a tmpfs for scratch
docker run --rm --read-only --tmpfs /tmp:size=16m alpine sh -c \
  'touch /etc/x || echo "root FS blocked ✅"; touch /tmp/ok && echo "tmpfs ok ✅"'

# 3) Capabilities
docker run --rm alpine chown nobody /tmp && echo "chown allowed (CAP_CHOWN)"
docker run --rm --cap-drop ALL alpine chown nobody /tmp || echo "chown blocked ✅"

# 4) PID limit stops a fork bomb
docker run --rm --pids-limit 20 alpine sh -c 'for i in $(seq 50); do sleep 5 & done; wait' 2>&1 \
  | grep -qi "fork" && echo "fork limit hit ✅"
```

**Leaked vs safe build secrets:**

```bash
mkdir -p lab9 && cd lab9
echo 'token=SUPER_SECRET' > secret.txt
cat > Dockerfile.bad <<'EOF'
FROM alpine
ARG TOKEN
RUN echo "using $TOKEN" > /dev/null
EOF
cat > Dockerfile.good <<'EOF'
# syntax=docker/dockerfile:1
FROM alpine
RUN --mount=type=secret,id=tok cat /run/secrets/tok > /dev/null && echo "secret used"
EOF
docker build -f Dockerfile.bad --build-arg TOKEN=SUPER_SECRET -t lab9:bad .
docker build -f Dockerfile.good --secret id=tok,src=secret.txt -t lab9:good .
docker history --no-trunc lab9:bad  | grep -c SUPER_SECRET    # ≥ 1 ❌ leaked
docker history --no-trunc lab9:good | grep -c SUPER_SECRET    # 0 ✅
```

**Scan** (optional, needs Docker Scout or Trivy):

```bash
docker scout cves lab9:good          # or: trivy image lab9:good
```

✅ **Verify:** every ✅ line prints; the bad image leaks the token in history, the good one doesn't.

🧹 `docker rmi lab9:bad lab9:good; cd ..`

---

## Lab 10 · Internals, Local Registry & Multi-Arch 🔴

**Goal:** look under the hood and push a multi-platform image. → [ch. 08](../../docker-foundations-to-advanced/08-advanced.md)

```bash
# Namespaces of a running container (Linux host)
docker run -d --name ns nginx:1.27-alpine
PID=$(docker inspect -f '{{.State.Pid}}' ns)
sudo ls -l /proc/$PID/ns
sudo nsenter -t $PID -n ss -tlnp            # host's ss, container's network

# Local registry
docker run -d -p 127.0.0.1:5000:5000 --name registry registry:2
docker tag lab3:final localhost:5000/lab3:1.0
docker push localhost:5000/lab3:1.0
curl -s localhost:5000/v2/_catalog          # {"repositories":["lab3"]}

# Multi-arch with buildx (uses QEMU for the non-native platform)
cd lab3
docker buildx create --name multi --driver docker-container --driver-opt network=host --use
docker buildx build --platform linux/amd64,linux/arm64 -t localhost:5000/lab3:multi --push .
docker buildx imagetools inspect localhost:5000/lab3:multi    # two platform digests
```

> 💡 If the push fails with an HTTPS error, recreate the builder with a BuildKit config that marks the lab registry as plain HTTP: put `[registry."localhost:5000"]` + `http = true` in `buildkitd.toml` and pass `--config buildkitd.toml` to `docker buildx create`. If `--platform` fails for arm64, install emulators once: `docker run --privileged --rm tonistiigi/binfmt --install all`.

✅ **Verify:** `imagetools inspect` lists `linux/amd64` and `linux/arm64`.

🎯 **Stretch:** convert Lab 3's Dockerfile to cross-compile (`FROM --platform=$BUILDPLATFORM golang:1.23 AS build` + `ARG TARGETOS TARGETARCH`) and compare build time.

🧹 `cd .. && docker rm -f ns registry && docker buildx rm multi`

---

# Part 2 · 🚨 Incident Runbooks

Each runbook: **Symptom → Triage → Likely causes → Fix → Prevent.**

## RB-1 · Container keeps restarting

```bash
docker ps -a --filter name=<c>
docker inspect -f 'exit={{.State.ExitCode}} oom={{.State.OOMKilled}} restarts={{.RestartCount}}' <c>
docker logs --tail 200 <c>
docker events --filter container=<c> --since 30m
```

| Exit | Cause | Fix |
|------|-------|-----|
| 137 + `oom=true` | Memory limit | Raise `--memory` or fix the leak |
| 137, `oom=false` | Killed (`docker kill`, stop timeout) | Handle SIGTERM, exec-form `CMD`, `--init` |
| 1 | App error | Read logs; usually config/env/dependency unreachable |
| 126 / 127 | Bad entrypoint / missing binary | `docker run --entrypoint sh -it <img>` and check paths, `+x`, CRLF line endings |

**Prevent:** health checks, `on-failure:N` instead of `always` for crash-loopers, memory limits sized from `docker stats`.

## RB-2 · Service unreachable

1. `docker port <c>`: is the port published? Right direction (`host:container`)?
2. Does the app inside bind `0.0.0.0`, not `127.0.0.1`? `docker run --rm --network container:<c> nicolaka/netshoot ss -tlnp`
3. Container-to-container: same **user-defined** network? Using the **service/container name**, not `localhost`?
4. `docker network inspect <net>`: is the target attached? Is the network `--internal`?
5. Host firewall / cloud security group / reverse proxy config.

## RB-3 · Disk full on the Docker host

```bash
docker system df -v
sudo du -sh /var/lib/docker/containers/*/*-json.log | sort -h | tail
```

1. Reclaim safely: `docker container prune`, `docker image prune`, `docker builder prune`.
2. Then if needed: `docker image prune -a`.
3. ⚠️ **Only with sign-off:** `docker volume prune` (data!).
4. **Prevent:** `daemon.json` → `"log-driver": "local"` or `json-file` with `max-size`/`max-file`; scheduled image pruning on CI runners.

## RB-4 · "Works locally, breaks in CI / on ARM servers"

- `exec format error` → wrong architecture. Build multi-arch with `buildx --platform linux/amd64,linux/arm64`.
- Missing files → check `.dockerignore` and the build context path (`-f` vs context dir).
- Different behaviour → you're deploying a moving tag; deploy **by digest** and tag `sha-<commit>`.

## RB-5 · Suspected container compromise

1. **Don't delete it** yet: `docker pause <c>` to freeze, preserving evidence.
2. `docker diff <c>`, `docker top <c>`, `docker inspect <c>` (mounts, caps, privileged?), `docker logs <c>`.
3. `docker export <c> > evidence.tar` for offline analysis.
4. Rotate any secrets the container could read; check for `docker.sock` mounts, `--privileged`, extra caps.
5. Rebuild from a patched base, scan, redeploy by digest with the [hardened flags](../../docker-foundations-to-advanced/07-security.md).

---

## ✅ Completion Checklist

- [ ] Labs 1–5 (🟢) done
- [ ] Labs 6–8 (🟡) done
- [ ] Labs 9–10 (🔴) done
- [ ] Can explain each runbook from memory
- [ ] Scored ≥ 70 on the [exam](exam.md)

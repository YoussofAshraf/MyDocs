# 🪵 Kafka Playbook

[← Practicals](../README.md) · [Exam →](exam.md) · [Guide](../../kafka-foundations-to-advanced/README.md)

Hands-on labs (Part 1) and incident runbooks (Part 2). Every lab follows **Goal → Steps → ✅ Verify → 🧹 Cleanup**.

## 🧰 Prerequisites

- Docker + Compose v2 (see the [Docker playbook](../docker/playbook.md))
- ~4 GB free RAM for the 3-broker cluster

---

# Part 1 · 🧪 Labs

## Lab 1 · Single Node & the `advertised.listeners` Trap 🟢

**Goal:** run the guide's dev compose and reproduce the #1 connectivity gotcha. → [ch. 06](../../kafka-foundations-to-advanced/06-operations-security.md)

```bash
mkdir -p ~/kafka-labs/lab1 && cd ~/kafka-labs/lab1
cat > compose.yaml <<'EOF'
services:
  kafka:
    image: apache/kafka:4.1.0
    ports: ["127.0.0.1:9092:9092"]
    environment:
      KAFKA_NODE_ID: 1
      KAFKA_PROCESS_ROLES: broker,controller
      KAFKA_LISTENERS: PLAINTEXT://:9092,CONTROLLER://:9093
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://localhost:9092
      KAFKA_CONTROLLER_LISTENER_NAMES: CONTROLLER
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: CONTROLLER:PLAINTEXT,PLAINTEXT:PLAINTEXT
      KAFKA_CONTROLLER_QUORUM_VOTERS: 1@kafka:9093
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
      KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR: 1
      KAFKA_TRANSACTION_STATE_LOG_MIN_ISR: 1
EOF
docker compose up -d
```

**Break it.** A client in *another* container on the same network:

```bash
docker run --rm --network lab1_default apache/kafka:4.1.0 \
  /opt/kafka/bin/kafka-topics.sh --bootstrap-server kafka:9092 --create --topic t1
# ❌ bootstrap works, then the client is told "connect to localhost:9092" → itself → timeout
```

**Fix it.** Add an internal listener for in-network clients:

```yaml
      KAFKA_LISTENERS: PLAINTEXT://:9092,INTERNAL://:29092,CONTROLLER://:9093
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://localhost:9092,INTERNAL://kafka:29092
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: CONTROLLER:PLAINTEXT,PLAINTEXT:PLAINTEXT,INTERNAL:PLAINTEXT
      KAFKA_INTER_BROKER_LISTENER_NAME: INTERNAL
```

```bash
docker compose up -d
docker run --rm --network lab1_default apache/kafka:4.1.0 \
  /opt/kafka/bin/kafka-topics.sh --bootstrap-server kafka:29092 --create --topic t1
```

✅ **Verify:** `Created topic t1.` on the internal listener.

🧠 **Explain:** why did bootstrap succeed even though producing failed? (Bootstrap is only used to fetch metadata; after that, clients use the **advertised** addresses.)

🧹 `docker compose down -v`

---

## Lab 2 · A 3-Broker KRaft Cluster 🟢

**Goal:** build the cluster used by Labs 3–10, with a dedicated controller and one broker per "AZ". → [ch. 01](../../kafka-foundations-to-advanced/01-foundations.md), [ch. 06](../../kafka-foundations-to-advanced/06-operations-security.md)

```bash
mkdir -p ~/kafka-labs/cluster && cd ~/kafka-labs/cluster
cat > compose.yaml <<'EOF'
x-common: &common
  CLUSTER_ID: 4L6g3nShT-eMCtK--X86sw
  KAFKA_CONTROLLER_QUORUM_VOTERS: 9@controller:9093
  KAFKA_CONTROLLER_LISTENER_NAMES: CONTROLLER
  KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: CONTROLLER:PLAINTEXT,PLAINTEXT:PLAINTEXT
  KAFKA_LOG_DIRS: /var/lib/kafka/data

x-broker: &broker
  <<: *common
  KAFKA_PROCESS_ROLES: broker
  KAFKA_LISTENERS: PLAINTEXT://:9092
  KAFKA_INTER_BROKER_LISTENER_NAME: PLAINTEXT
  KAFKA_AUTO_CREATE_TOPICS_ENABLE: "false"
  KAFKA_GROUP_INITIAL_REBALANCE_DELAY_MS: 0

services:
  controller:
    image: apache/kafka:4.1.0
    environment:
      <<: *common
      KAFKA_NODE_ID: 9
      KAFKA_PROCESS_ROLES: controller
      KAFKA_LISTENERS: CONTROLLER://:9093
  kafka1:
    image: apache/kafka:4.1.0
    depends_on: [controller]
    environment:
      <<: *broker
      KAFKA_NODE_ID: 1
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka1:9092
      KAFKA_BROKER_RACK: az-a
  kafka2:
    image: apache/kafka:4.1.0
    depends_on: [controller]
    environment:
      <<: *broker
      KAFKA_NODE_ID: 2
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka2:9092
      KAFKA_BROKER_RACK: az-b
  kafka3:
    image: apache/kafka:4.1.0
    depends_on: [controller]
    environment:
      <<: *broker
      KAFKA_NODE_ID: 3
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka3:9092
      KAFKA_BROKER_RACK: az-c
EOF
docker compose up -d
```

> ⚠️ One controller is fine for a lab. Production needs **3 controllers** (or 5), as [ch. 06](../../kafka-foundations-to-advanced/06-operations-security.md) explains.

Helper used in every later lab (run it in each new terminal inside `~/kafka-labs/cluster`):

```bash
k() { docker compose exec -T kafka1 /opt/kafka/bin/"$1" --bootstrap-server kafka1:9092 "${@:2}"; }
ki() { docker compose exec kafka1 /opt/kafka/bin/"$1" --bootstrap-server kafka1:9092 "${@:2}"; }  # interactive (TTY)
```

```bash
docker compose exec kafka1 /opt/kafka/bin/kafka-metadata-quorum.sh --bootstrap-server kafka1:9092 describe --status
k kafka-topics.sh --create --topic orders --partitions 3 --replication-factor 3
k kafka-topics.sh --describe --topic orders
```

✅ **Verify:** the quorum shows `LeaderId: 9`; `orders` has 3 partitions, each with `Replicas` on brokers 1,2,3 and `Isr` equal to `Replicas`.

🎯 **Stretch:** `k kafka-topics.sh --create --topic oops --partitions 1 --replication-factor 4`. Why does it fail?

---

## Lab 3 · Keys, Partitions & Ordering 🟢

**Goal:** prove the same key always lands in the same partition, and see ordering per partition. → [ch. 02](../../kafka-foundations-to-advanced/02-producers.md)

```bash
printf 'user-1:login\nuser-2:login\nuser-1:add-to-cart\nuser-3:login\nuser-1:checkout\nuser-2:logout\n' \
  | k kafka-console-producer.sh --topic orders \
      --property parse.key=true --property key.separator=:

k kafka-console-consumer.sh --topic orders --from-beginning --timeout-ms 5000 \
  --property print.key=true --property print.partition=true
```

> 💡 With `--timeout-ms`, the consumer ends with `TimeoutException` once no more records arrive. That's expected.

✅ **Verify:** all `user-1` events share one partition and appear in order `login → add-to-cart → checkout`. Records across different partitions may interleave in any order.

**Null keys → sticky partitioner:**

```bash
seq 1 20 | k kafka-console-producer.sh --topic orders
k kafka-get-offsets.sh --topic orders      # end offset per partition
```

🧠 **Explain:** why might the 20 keyless records land unevenly (often one partition)? (The sticky partitioner fills a batch on one partition before switching.)

🎯 **Stretch:** `k kafka-topics.sh --alter --topic orders --partitions 6`, produce `user-1:again`, and check its partition. Did it move? Why is that dangerous? → [ch. 02](../../kafka-foundations-to-advanced/02-producers.md)

---

## Lab 4 · Consumer Groups, Lag & Rebalancing 🟡

**Goal:** watch partitions get shared out, idle consumers appear, and lag build up. → [ch. 03](../../kafka-foundations-to-advanced/03-consumers.md)

```bash
k kafka-topics.sh --create --topic events --partitions 3 --replication-factor 3
```

Open **three extra terminals** (run the `k`/`ki` helper in each), then start one consumer per terminal, adding them one at a time:

```bash
ki kafka-console-consumer.sh --topic events --group billing \
   --property print.partition=true
```

After each consumer joins, check the assignment from your main terminal:

```bash
k kafka-consumer-groups.sh --describe --group billing
k kafka-consumer-groups.sh --describe --group billing --members
```

Now start a **4th** consumer, then check `--members` again.

✅ **Verify:** with 1 → 2 → 3 consumers, partitions are redistributed; the 4th consumer has `#PARTITIONS 0` (idle).

**Build lag:** stop all consumers (Ctrl-C), then produce:

```bash
seq 1 3000 | k kafka-console-producer.sh --topic events
k kafka-consumer-groups.sh --describe --group billing    # LAG ≈ 1000 per partition
```

Start one consumer again and re-check: lag drains to 0.

🧠 **Explain:** `LAG = LOG-END-OFFSET − CURRENT-OFFSET`. Why is lag the most important consumer metric?

---

## Lab 5 · Resetting Offsets (Replay) 🟡

**Goal:** replay and skip data safely. → [ch. 03](../../kafka-foundations-to-advanced/03-consumers.md)

> The group must be **inactive** (all consumers stopped) before offsets can be reset.

```bash
# Always dry-run first (it's the default without --execute)
k kafka-consumer-groups.sh --group billing --topic events --reset-offsets --to-earliest --dry-run
k kafka-consumer-groups.sh --group billing --topic events --reset-offsets --to-earliest --execute
k kafka-consumer-groups.sh --describe --group billing            # LAG back to full

k kafka-consumer-groups.sh --group billing --topic events --reset-offsets --shift-by -100 --execute
k kafka-consumer-groups.sh --group billing --topic events:0 --reset-offsets --to-offset 500 --execute
k kafka-consumer-groups.sh --group billing --topic events --reset-offsets --to-latest --execute   # skip backlog
```

**`auto.offset.reset` in action:** a brand-new group defaults to `latest`.

```bash
k kafka-console-consumer.sh --topic events --group fresh --timeout-ms 5000        # prints nothing
k kafka-console-consumer.sh --topic events --group fresh2 --timeout-ms 5000 \
  --consumer-property auto.offset.reset=earliest | wc -l                           # 3000
```

✅ **Verify:** `--describe` reflects each reset; `fresh` reads nothing; `fresh2` reads all 3000 records.

---

## Lab 6 · Replication, ISR & the Durability Triangle 🔴

**Goal:** see `min.insync.replicas` + `acks=all` refuse unsafe writes. → [ch. 04](../../kafka-foundations-to-advanced/04-storage-replication.md)

```bash
k kafka-topics.sh --create --topic payments --partitions 1 --replication-factor 3 \
  --config min.insync.replicas=2
k kafka-topics.sh --describe --topic payments                # Isr: 3 replicas

docker compose stop kafka3
sleep 15
k kafka-topics.sh --describe --topic payments                # Isr shrinks to 2
echo "p1" | k kafka-console-producer.sh --topic payments --producer-property acks=all   # ✅ works

docker compose stop kafka2
sleep 15
k kafka-topics.sh --describe --topic payments                # Isr: 1
k kafka-topics.sh --describe --under-min-isr-partitions
echo "p2" | k kafka-console-producer.sh --topic payments --producer-property acks=all \
  --producer-property delivery.timeout.ms=15000 --producer-property request.timeout.ms=5000
# ❌ NOT_ENOUGH_REPLICAS: safe failure
echo "p3" | k kafka-console-producer.sh --topic payments --producer-property acks=1
# ⚠️ accepted, but only one copy exists

docker compose start kafka2 kafka3
sleep 20
k kafka-topics.sh --describe --topic payments                # Isr back to 3
k kafka-console-consumer.sh --topic payments --from-beginning --timeout-ms 5000
```

✅ **Verify:** `p1` and `p3` exist, `p2` does not; the ISR fully recovers. While two brokers were down, `--describe` also showed an `Elr:` (Eligible Leader Replicas) entry: a replica that was in sync and can safely become leader again.

🧠 **Explain:** with `unclean.leader.election.enable=true`, what could happen if the only ISR replica died and an out-of-sync replica became leader?

---

## Lab 7 · Segments, Retention & Log Compaction 🔴

**Goal:** see log segments on disk and compaction keeping the latest value per key. → [ch. 04](../../kafka-foundations-to-advanced/04-storage-replication.md)

```bash
k kafka-topics.sh --create --topic user-profiles --partitions 1 --replication-factor 3 \
  --config cleanup.policy=compact --config segment.ms=10000 \
  --config min.cleanable.dirty.ratio=0.01 --config delete.retention.ms=1000

printf 'u1:{"name":"Ann"}\nu2:{"name":"Bob"}\nu1:{"name":"Ann B."}\nu2:{"name":"Robert"}\nu3:{"name":"Cy"}\n' \
  | k kafka-console-producer.sh --topic user-profiles --property parse.key=true --property key.separator=:

# Tombstone for u3 (null value)
echo 'u3:NULL' | k kafka-console-producer.sh --topic user-profiles \
  --property parse.key=true --property key.separator=: --property null.marker=NULL

sleep 30   # let segments roll, then send one record so the old segment can be cleaned
echo 'u9:{"name":"roll"}' | k kafka-console-producer.sh --topic user-profiles --property parse.key=true --property key.separator=:
sleep 30

k kafka-console-consumer.sh --topic user-profiles --from-beginning --timeout-ms 5000 --property print.key=true
docker compose exec kafka1 ls -l /var/lib/kafka/data/user-profiles-0/
```

✅ **Verify:** only the latest value per key remains (`u1 Ann B.`, `u2 Robert`, `u9`); `u3` is gone after the tombstone is cleaned. The directory shows `.log`, `.index` and `.timeindex` files per segment.

> Compaction is asynchronous and never touches the **active** segment. If old values are still there, wait another minute and retry.

---

## Lab 8 · Producer Throughput Tuning 🟡

**Goal:** measure the effect of `acks`, `linger.ms`, `batch.size` and compression. → [ch. 02](../../kafka-foundations-to-advanced/02-producers.md)

```bash
k kafka-topics.sh --create --topic perf --partitions 6 --replication-factor 3
P=/opt/kafka/bin/kafka-producer-perf-test.sh
run() { docker compose exec -T kafka1 $P --topic perf --num-records 300000 --record-size 1000 \
          --throughput -1 --producer-props bootstrap.servers=kafka1:9092 "$@" | tail -1; }

run acks=1   linger.ms=0  batch.size=16384
run acks=all linger.ms=0  batch.size=16384
run acks=all linger.ms=20 batch.size=262144
run acks=all linger.ms=20 batch.size=262144 compression.type=lz4
run acks=all linger.ms=20 batch.size=262144 compression.type=zstd
```

Record the results:

| Run | records/sec | MB/sec | avg latency |
|-----|-------------|--------|-------------|
| acks=1, no batching | | | |
| acks=all, no batching | | | |
| acks=all + batching | | | |
| + lz4 | | | |
| + zstd | | | |

🧠 **Explain:** why does batching usually beat the cost of `acks=all`? Why can compression raise throughput even though it costs CPU?

---

## Lab 9 · Health Checks Like an Operator 🟡

**Goal:** check the "must be 0" signals from the CLI. → [ch. 06](../../kafka-foundations-to-advanced/06-operations-security.md)

```bash
k kafka-topics.sh --describe --under-replicated-partitions     # empty = healthy
k kafka-topics.sh --describe --under-min-isr-partitions        # empty = healthy
k kafka-topics.sh --describe --unavailable-partitions          # empty = healthy
docker compose exec kafka1 /opt/kafka/bin/kafka-metadata-quorum.sh --bootstrap-server kafka1:9092 describe --replication
k kafka-consumer-groups.sh --list
k kafka-consumer-groups.sh --describe --all-groups | awk 'NR==1 || $6 > 0'   # partitions with lag
```

**Break it:** `docker compose stop kafka2` and rerun the first three commands, then `docker compose start kafka2`.

✅ **Verify:** while `kafka2` is down, `--under-replicated-partitions` lists every partition with a replica on broker 2; it goes empty again after recovery.

---

## Lab 10 · Partition Reassignment (Scaling Brokers) 🔴

**Goal:** move partitions between brokers, as you would after adding capacity. → [ch. 06](../../kafka-foundations-to-advanced/06-operations-security.md)

```bash
k kafka-topics.sh --create --topic moveme --partitions 4 --replication-factor 2
k kafka-topics.sh --describe --topic moveme

docker compose exec -T kafka1 sh -c 'echo "{\"topics\":[{\"topic\":\"moveme\"}],\"version\":1}" > /tmp/move.json'
k kafka-reassign-partitions.sh --topics-to-move-json-file /tmp/move.json --broker-list "1,2" --generate
```

Copy the **Proposed partition reassignment** JSON into `/tmp/plan.json` inside the container, then:

```bash
docker compose exec kafka1 sh -c 'cat > /tmp/plan.json'      # paste the JSON, then Ctrl-D
k kafka-reassign-partitions.sh --reassignment-json-file /tmp/plan.json --execute --throttle 10000000
k kafka-reassign-partitions.sh --reassignment-json-file /tmp/plan.json --verify   # also removes the throttle
k kafka-topics.sh --describe --topic moveme
```

✅ **Verify:** every replica of `moveme` is now on brokers 1 and 2 only.

🧠 **Explain:** why throttle a reassignment in production? What does Cruise Control automate here?

🧹 **Cluster cleanup (after all labs):** `docker compose down -v`

---

# Part 2 · 🚨 Incident Runbooks

Each runbook follows **Symptom → Triage → Likely causes → Fix → Prevent.**

## RB-1 · Consumer lag keeps growing

```bash
kafka-consumer-groups.sh --bootstrap-server $BS --describe --group <g>
kafka-consumer-groups.sh --bootstrap-server $BS --describe --group <g> --members --verbose
```

| Pattern | Likely cause | Fix |
|---------|-------------|-----|
| Lag on **all** partitions | Under-capacity | Add consumers (up to the partition count), batch I/O, more partitions (mind key remapping) |
| Lag on **one** partition | Hot key or poison record | Inspect that offset; route the poison record to a DLT; pick a better key |
| `CONSUMER-ID` flips constantly | Rebalance storm | Lower `max.poll.records`, raise `max.poll.interval.ms`, `cooperative-sticky` or `group.protocol=consumer`, `group.instance.id` |
| No members | Consumers down | Check app deploys, auth/ACLs, `group.id` typos |

**Prevent:** alert on lag in records **and** time; build a DLT/retry topics in from the start.

## RB-2 · Producers failing with `NotEnoughReplicas` / timeouts

1. `kafka-topics.sh --describe --under-min-isr-partitions`: which partitions?
2. Which brokers are down or slow? Check broker logs, disk, GC, network.
3. Bring brokers back. **Don't** lower `min.insync.replicas` or switch to `acks=1` without a risk decision. That trades durability for availability.
4. If one broker is lagging behind: check disk I/O and `replica.lag.time.max.ms`.

**Prevent:** RF=3 across AZs (`broker.rack`), capacity headroom, one-at-a-time rolling restarts.

## RB-3 · Clients can't connect

1. Can the client resolve and reach the **advertised** host:port (not just the bootstrap address)?
2. Does the listener name and protocol match the client (`PLAINTEXT` vs `SASL_SSL`)?
3. TLS: truststore, hostname verification, expiry.
4. SASL: mechanism (`SCRAM-SHA-512`), user exists (`kafka-configs.sh --describe --entity-type users`).
5. Authorization: `kafka-acls.sh --list --principal User:<app>`: needs `Read` on the topic **and** the group for consumers.

## RB-4 · Offline partitions / no active controller

1. `ActiveControllerCount` across controllers must sum to **exactly 1**. Run `kafka-metadata-quorum.sh describe --status`.
2. Controller quorum lost (majority down) → restore controllers first.
3. `OfflinePartitionsCount > 0` → all replicas of a partition are down. Restore a broker holding an ISR copy.
4. ⚠️ **Last resort:** unclean election for that topic only, accepting data loss, with sign-off.

## RB-5 · Disk filling up on brokers

1. Top topics by size: `kafka-log-dirs.sh --describe --bootstrap-server $BS`.
2. Check `retention.ms`/`retention.bytes` on the biggest topics. Compacted topics can still grow if keys are unbounded.
3. Short term: lower retention on non-critical topics (`kafka-configs.sh --alter --add-config retention.ms=...`).
4. Long term: add brokers + reassign, or enable **tiered storage**.

---

## ✅ Completion Checklist

- [ ] Labs 1–3 (🟢) done
- [ ] Labs 4, 5, 8, 9 (🟡) done
- [ ] Labs 6, 7, 10 (🔴) done
- [ ] Can explain each runbook from memory
- [ ] Scored ≥ 70 on the [exam](exam.md)

# 🪵 Kafka Exam

[← Practicals](../README.md) · [Playbook →](playbook.md) · [Guide](../../kafka-foundations-to-advanced/README.md)

| | |
|--|--|
| ⏱️ Time | 90 minutes |
| 🎯 Pass mark | 70 / 100 |
| 📚 Covers | Chapters 01–06 of [Kafka: Foundations to Advanced](../../kafka-foundations-to-advanced/README.md) |
| 🧭 Rules | Closed book for Parts A–B. Parts C–D may use a terminal |

Answers are hidden under **Answer**, with the chapter to re-read.

---

## 🅰️ Part A: Multiple Choice (20 × 2 pts = 40)

**A1.** Kafka guarantees ordering:

- a) Across the whole topic
- b) Within a partition
- c) Within a consumer group
- d) Within a broker

<details><summary>Answer</summary>

**b).** Use a key to keep all events of one entity in one partition. → [01](../../kafka-foundations-to-advanced/01-foundations.md)
</details>

**A2.** Since Kafka 4.0, cluster metadata is managed by:

- a) ZooKeeper
- b) etcd
- c) KRaft controllers (Raft metadata log)
- d) The Schema Registry

<details><summary>Answer</summary>

**c).** → [01](../../kafka-foundations-to-advanced/01-foundations.md)
</details>

**A3.** What happens to a record after a consumer reads it?

- a) It's deleted
- b) It's marked read and hidden from other groups
- c) Nothing; it stays until retention/compaction removes it
- d) It moves to `__consumer_offsets`

<details><summary>Answer</summary>

**c).** Reading doesn't delete; consumers track offsets and can replay. → [01](../../kafka-foundations-to-advanced/01-foundations.md)
</details>

**A4.** Which is **not** a reason Kafka is fast?

- a) Sequential disk I/O
- b) Zero-copy `sendfile`
- c) The broker tracks per-message acknowledgement state
- d) Batching and compression

<details><summary>Answer</summary>

**c).** It's the opposite: "dumb broker, smart client". → [01](../../kafka-foundations-to-advanced/01-foundations.md)
</details>

**A5.** A record with `key = null` using the default partitioner:

- a) Always goes to partition 0
- b) Is rejected
- c) Uses the sticky partitioner: fills a batch on one partition, then switches
- d) Is round-robined one record at a time

<details><summary>Answer</summary>

**c).** → [02](../../kafka-foundations-to-advanced/02-producers.md)
</details>

**A6.** You increase a topic from 6 to 12 partitions. What is the main risk?

- a) Data loss
- b) Existing keys map to different partitions, so per-key ordering breaks around the change
- c) Consumers must be restarted
- d) Replication factor resets to 1

<details><summary>Answer</summary>

**b).** `hash(key) % n` changes with `n`. → [02](../../kafka-foundations-to-advanced/02-producers.md)
</details>

**A7.** Which key is the worst choice for an `orders` topic with heavy US traffic?

- a) `orderId`
- b) `userId`
- c) `country`
- d) `deviceId`

<details><summary>Answer</summary>

**c).** Low cardinality + skew → a **hot partition**. → [02](../../kafka-foundations-to-advanced/02-producers.md)
</details>

**A8.** With `acks=1`, when can an acknowledged write be lost?

- a) Never
- b) If the leader dies before followers replicate it
- c) Only if all brokers die
- d) When the consumer lags

<details><summary>Answer</summary>

**b).** → [02](../../kafka-foundations-to-advanced/02-producers.md)
</details>

**A9.** The idempotent producer prevents duplicates using:

- a) Message hashes on the broker
- b) Producer ID + per-partition sequence numbers
- c) Consumer offsets
- d) Transactions only

<details><summary>Answer</summary>

**b).** Exactly-once **writes per partition per producer session**; cross-partition atomicity needs transactions. → [02](../../kafka-foundations-to-advanced/02-producers.md)
</details>

**A10.** A topic has 4 partitions; a group has 6 consumers. What happens?

- a) Each partition is split across 1.5 consumers
- b) 2 consumers sit idle
- c) Kafka adds 2 partitions automatically
- d) The group fails to start

<details><summary>Answer</summary>

**b).** One partition → at most one consumer per group. (Share groups / KIP-932 are the exception for queue-style work.) → [03](../../kafka-foundations-to-advanced/03-consumers.md)
</details>

**A11.** The committed offset represents:

- a) The last record processed
- b) The next record to read
- c) The log end offset
- d) The high watermark

<details><summary>Answer</summary>

**b).** → [03](../../kafka-foundations-to-advanced/03-consumers.md)
</details>

**A12.** A brand-new group with `auto.offset.reset=latest` (the default) subscribes to a topic holding 1 M old records. It reads:

- a) All 1 M records
- b) Only records produced after it joins
- c) The last 500 records
- d) Nothing until an admin resets offsets

<details><summary>Answer</summary>

**b).** Use `earliest` to start from the beginning. → [03](../../kafka-foundations-to-advanced/03-consumers.md)
</details>

**A13.** Which ordering gives **at-least-once** delivery?

- a) poll → commit → process
- b) poll → process → commit
- c) commit → poll → process
- d) process → poll → commit

<details><summary>Answer</summary>

**b).** A crash before commit causes reprocessing, so processing must be idempotent. → [03](../../kafka-foundations-to-advanced/03-consumers.md)
</details>

**A14.** The **#1 cause** of rebalance storms is:

- a) Too many partitions
- b) Processing between `poll()` calls exceeding `max.poll.interval.ms`
- c) Using compression
- d) `acks=all`

<details><summary>Answer</summary>

**b).** Lower `max.poll.records` or speed up processing. → [03](../../kafka-foundations-to-advanced/03-consumers.md)
</details>

**A15.** Which setting makes a pod restart within `session.timeout.ms` **not** trigger a rebalance?

- a) `group.instance.id` (static membership)
- b) `enable.auto.commit=false`
- c) `isolation.level=read_committed`
- d) `client.rack`

<details><summary>Answer</summary>

**a).** → [03](../../kafka-foundations-to-advanced/03-consumers.md)
</details>

**A16.** `cleanup.policy=compact` keeps:

- a) Records newer than `retention.ms`
- b) The latest value per key (tombstones eventually remove keys)
- c) Only the first value per key
- d) One segment per key

<details><summary>Answer</summary>

**b).** → [04](../../kafka-foundations-to-advanced/04-storage-replication.md)
</details>

**A17.** Consumers can read up to:

- a) The leader's log end offset
- b) The high watermark (replicated to all ISR)
- c) The last committed consumer offset
- d) Any offset on any follower

<details><summary>Answer</summary>

**b).** → [04](../../kafka-foundations-to-advanced/04-storage-replication.md)
</details>

**A18.** RF=3, `min.insync.replicas=2`, `acks=all`. Two brokers hosting the partition go down. Producers:

- a) Keep writing to the last replica
- b) Get `NotEnoughReplicas` errors (safe failure)
- c) Silently lose data
- d) Switch to `acks=1`

<details><summary>Answer</summary>

**b).** → [04](../../kafka-foundations-to-advanced/04-storage-replication.md)
</details>

**A19.** Under `BACKWARD` schema compatibility, which components upgrade first?

- a) Producers
- b) Consumers
- c) Brokers
- d) Any order

<details><summary>Answer</summary>

**b) Consumers.** New schema readers can read old data. → [05](../../kafka-foundations-to-advanced/05-ecosystem.md)
</details>

**A20.** Which client setting is **the #1 connectivity gotcha**?

- a) `bootstrap.servers`
- b) `advertised.listeners` on the broker
- c) `linger.ms`
- d) `group.id`

<details><summary>Answer</summary>

**b).** It's the address handed back to clients; they must be able to resolve and reach it. → [06](../../kafka-foundations-to-advanced/06-operations-security.md)
</details>

---

## 🅱️ Part B: Short Answer (8 × 3 pts = 24)

**B1.** Define topic, partition, offset, broker and consumer group in one line each.

<details><summary>Answer</summary>

Topic: named, append-only stream of events. Partition: ordered, immutable log that a topic is split into for scale. Offset: position of a record in a partition. Broker: server storing partitions and serving clients. Consumer group: set of consumers sharing a topic's partitions (each partition → one member). → [01](../../kafka-foundations-to-advanced/01-foundations.md)
</details>

**B2.** Name the three producer settings you'd tune for throughput and a sensible value for each.

<details><summary>Answer</summary>

`linger.ms` 10–50, `batch.size` 64 KB–1 MB (256 KB+), `compression.type` `lz4` or `zstd`. → [02](../../kafka-foundations-to-advanced/02-producers.md)
</details>

**B3.** A 10 MB file must flow through Kafka. Give the preferred pattern and the "careful" alternative.

<details><summary>Answer</summary>

Claim-check: store the payload in object storage (S3) and send a reference. Alternative: raise `max.request.size` (producer) and `message.max.bytes` (broker/topic) carefully. → [02](../../kafka-foundations-to-advanced/02-producers.md)
</details>

**B4.** Compute lag: committed offset 4, current position 7, log end offset 10.

<details><summary>Answer</summary>

Lag = LEO − committed = **10 − 4 = 6**. → [03](../../kafka-foundations-to-advanced/03-consumers.md)
</details>

**B5.** Kafka has no built-in DLQ. Describe the standard retry/DLT design.

<details><summary>Answer</summary>

On a transient error, publish the record to a retry topic (e.g. `orders.retry-1m`) consumed by a delayed consumer; on poison/exhausted retries, publish to a dead-letter topic (`orders.DLT`), commit, alert, inspect and replay. Without this, one bad record blocks its partition. → [03](../../kafka-foundations-to-advanced/03-consumers.md)
</details>

**B6.** Why should `unclean.leader.election.enable` stay `false` for critical data?

<details><summary>Answer</summary>

Enabling it lets an out-of-sync replica become leader, gaining availability but **losing** acknowledged records it never received. → [04](../../kafka-foundations-to-advanced/04-storage-replication.md)
</details>

**B7.** Explain the outbox + CDC pattern and the problem it solves.

<details><summary>Answer</summary>

The service writes the business row and an `outbox` event row in **one DB transaction**; Debezium reads the WAL and publishes the outbox rows to Kafka. This avoids the dual-write problem (DB committed but Kafka publish failed, or vice versa), so there are no lost or phantom events. → [05](../../kafka-foundations-to-advanced/05-ecosystem.md)
</details>

**B8.** List the four broker metrics that must be 0 (or exactly 1) in a healthy cluster.

<details><summary>Answer</summary>

`UnderReplicatedPartitions` = 0, `UnderMinIsrPartitionCount` = 0, `OfflinePartitionsCount` = 0, `ActiveControllerCount` = exactly 1. → [06](../../kafka-foundations-to-advanced/06-operations-security.md)
</details>

---

## 🅲 Part C: Design & Config (3 × 6 pts = 18)

**C1.** Design a durable `payments` topic for a 3-AZ cluster. Give topic, broker and producer settings, and say how many broker failures it tolerates for writes.

<details><summary>Answer</summary>

- Topic: `replication.factor=3`, `min.insync.replicas=2`, partitions sized from throughput (e.g. 12), `cleanup.policy=delete` with explicit `retention.ms`.
- Brokers: `broker.rack` per AZ (replicas spread across AZs), `unclean.leader.election.enable=false`, `auto.create.topics.enable=false`.
- Producer: `acks=all`, `enable.idempotence=true`, key = `paymentId`/`accountId`, handle send callbacks, `flush()`/`close()` on shutdown.
- Tolerates **1** broker (or AZ) loss with writes accepted and no data loss. → [04](../../kafka-foundations-to-advanced/04-storage-replication.md), [06](../../kafka-foundations-to-advanced/06-operations-security.md)
</details>

**C2.** Make this consume → produce service exactly-once. List every setting/call change.

```java
consumer: enable.auto.commit=true
loop: records = poll(); for r in records: producer.send(toInvoice(r));
```

<details><summary>Answer</summary>

- Producer: `transactional.id=<stable unique id per instance>` (implies idempotence); call `initTransactions()` once (fences zombies).
- Consumer: `enable.auto.commit=false`; downstream readers use `isolation.level=read_committed`.
- Loop: `beginTransaction()` → `send(...)` for each output → `sendOffsetsToTransaction(offsets, consumer.groupMetadata())` → `commitTransaction()`; on error `abortTransaction()`.
- Or use Kafka Streams with `processing.guarantee=exactly_once_v2`.
- Note: side effects outside Kafka (HTTP, DB) still need idempotency/outbox. → [05](../../kafka-foundations-to-advanced/05-ecosystem.md)
</details>

**C3.** Write least-privilege ACLs: `order-service` writes `orders`; `billing` reads `orders` as group `billing`. Also give two broker settings that make the ACLs actually enforced.

<details><summary>Answer</summary>

```bash
kafka-acls.sh --bootstrap-server kafka:9092 --command-config admin.properties \
  --add --allow-principal User:order-service --operation Write --topic orders
kafka-acls.sh --bootstrap-server kafka:9092 --command-config admin.properties \
  --add --allow-principal User:billing --operation Read --topic orders
kafka-acls.sh --bootstrap-server kafka:9092 --command-config admin.properties \
  --add --allow-principal User:billing --operation Read --group billing
```

Broker: `authorizer.class.name=org.apache.kafka.metadata.authorizer.StandardAuthorizer` and `allow.everyone.if.no.acl.found=false` (plus SASL/TLS listeners so principals are authenticated). → [06](../../kafka-foundations-to-advanced/06-operations-security.md)
</details>

---

## 🅳 Part D: Troubleshooting Scenarios (3 × 6 pts = 18)

**D1.** `kafka-consumer-groups.sh --describe --group billing` shows lag 2 on partition 0 and lag 4 610 (growing) on partition 1, both owned by `consumer-A`. Diagnose and propose fixes.

<details><summary>Answer</summary>

Lag is isolated to one partition, so it's not general under-capacity. Likely: a **hot key** skewing traffic to P1, or a **poison record** being retried and blocking P1. Check per-partition produce rates and the consumer's logs/errors at offset 990. Fixes: route poison records to a DLT; if skew, choose a higher-cardinality key; add consumers (up to partition count) so P1 gets a dedicated one; optimise processing. → [02](../../kafka-foundations-to-advanced/02-producers.md), [03](../../kafka-foundations-to-advanced/03-consumers.md)
</details>

**D2.** An app in another Docker container can bootstrap to `kafka:9092` but then times out producing, logging connection attempts to `localhost:9092`. Explain and fix.

<details><summary>Answer</summary>

Bootstrap succeeds, then the broker returns its **advertised listener** (`localhost:9092`) in metadata; inside the client's container, `localhost` is itself. Add a second listener (e.g. `INTERNAL://kafka:29092`, advertised as `kafka:29092`) for in-network clients and keep `localhost:9092` for the host. → [06](../../kafka-foundations-to-advanced/06-operations-security.md)
</details>

**D3.** During a rolling upgrade, `UnderMinIsrPartitionCount` goes from 0 to 40 and producers start failing. What happened and what's the safe procedure?

<details><summary>Answer</summary>

A second broker was restarted before the first had re-synced, dropping ISR below `min.insync.replicas` for partitions they shared, so `acks=all` producers get `NotEnoughReplicas`. Safe procedure: one broker at a time; wait for `UnderReplicatedPartitions = 0` before the next; bump `metadata.version` only after all nodes are upgraded. → [06](../../kafka-foundations-to-advanced/06-operations-security.md)
</details>

---

## 🧮 Scoring

| Score | Level |
|-------|-------|
| 90–100 | 🔴 Advanced: ready to run production clusters |
| 70–89 | 🟡 Intermediate: pass, review missed chapters |
| < 70 | 🟢 Beginner: redo [playbook](playbook.md) labs 1–4 and retake |

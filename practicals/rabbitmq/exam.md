# 🐰 RabbitMQ Exam

[← Practicals](../README.md) · [Playbook →](playbook.md) · [Guide](../../rabbitmq-foundations-to-advanced/README.md)

| | |
|--|--|
| ⏱️ Time | 90 minutes |
| 🎯 Pass mark | 70 / 100 |
| 📚 Covers | Chapters 01–06 of [RabbitMQ: Foundations to Advanced](../../rabbitmq-foundations-to-advanced/README.md) |
| 🧭 Rules | Closed book for Parts A–B. Parts C–D may use the [lab cluster](lab/) |

Answers are hidden under **Answer**, with the chapter to re-read.

---

## 🅰️ Part A: Multiple Choice (20 × 2 pts = 40)

**A1.** In AMQP 0-9-1, producers publish to:

- a) Queues
- b) Exchanges
- c) Bindings
- d) Consumers

<details><summary>Answer</summary>

**b) Exchanges.** Exchanges route to queues via bindings. → [01](../../rabbitmq-foundations-to-advanced/01-foundations.md)
</details>

**A2.** The recommended connection/channel model is:

- a) One connection per message
- b) One connection per thread, one channel per process
- c) One connection per process, one channel per thread
- d) One channel shared by all threads

<details><summary>Answer</summary>

**c).** Connections are expensive TCP links; channels are cheap and not thread-safe. Also: separate connections for publishing and consuming. → [01](../../rabbitmq-foundations-to-advanced/01-foundations.md)
</details>

**A3.** Publishing with exchange `""` and routing key `invoices` delivers to:

- a) Every queue
- b) The queue named `invoices` (default exchange)
- c) Nothing; the empty exchange is invalid
- d) The `amq.direct` exchange's queues

<details><summary>Answer</summary>

**b).** Every queue is implicitly bound to the default exchange by its name. → [02](../../rabbitmq-foundations-to-advanced/02-exchanges-routing.md)
</details>

**A4.** Which exchange type ignores the routing key?

- a) direct
- b) topic
- c) fanout
- d) default

<details><summary>Answer</summary>

**c) fanout** (headers also ignores it, matching headers instead). → [02](../../rabbitmq-foundations-to-advanced/02-exchanges-routing.md)
</details>

**A5.** Binding key `order.*`. Which routing key matches?

- a) `order`
- b) `order.created`
- c) `order.created.eu`
- d) `orders.created`

<details><summary>Answer</summary>

**b).** `*` = exactly one word. → [02](../../rabbitmq-foundations-to-advanced/02-exchanges-routing.md)
</details>

**A6.** Binding key `order.#`. Which routing keys match?

- a) Only `order.created`
- b) `order`, `order.created`, `order.created.eu`
- c) Only multi-word keys
- d) `orders.created`

<details><summary>Answer</summary>

**b).** `#` = zero or more words. → [02](../../rabbitmq-foundations-to-advanced/02-exchanges-routing.md)
</details>

**A7.** By default, a message that matches no binding is:

- a) Stored in a hidden queue
- b) Returned to the publisher
- c) Silently dropped
- d) Dead-lettered

<details><summary>Answer</summary>

**c).** Use `mandatory=true` (returned) or an **alternate exchange**. → [02](../../rabbitmq-foundations-to-advanced/02-exchanges-routing.md)
</details>

**A8.** You redeclare an existing durable queue with different arguments. The broker responds with:

- a) The queue is updated
- b) `PRECONDITION_FAILED` and the channel closes
- c) A duplicate queue is created
- d) A warning only

<details><summary>Answer</summary>

**b).** That's why policies beat hard-coded `x-` arguments for anything you may change. → [02](../../rabbitmq-foundations-to-advanced/02-exchanges-routing.md)
</details>

**A9.** In RabbitMQ 4.x, what's the recommended queue type for replicated, durable work queues?

- a) Classic mirrored
- b) Quorum
- c) Stream
- d) Transient

<details><summary>Answer</summary>

**b) Quorum.** Classic mirroring was removed in 4.0. → [03](../../rabbitmq-foundations-to-advanced/03-queues-consumers.md)
</details>

**A10.** Which queue type lets many consumers re-read the same messages from any offset?

- a) Classic
- b) Quorum
- c) Stream
- d) Exclusive

<details><summary>Answer</summary>

**c) Stream.** → [03](../../rabbitmq-foundations-to-advanced/03-queues-consumers.md)
</details>

**A11.** A message survives a broker restart only if:

- a) The queue is durable
- b) The message is persistent
- c) The exchange, the queue **and** the message are all durable/persistent
- d) Publisher confirms are on

<details><summary>Answer</summary>

**c).** → [03](../../rabbitmq-foundations-to-advanced/03-queues-consumers.md)
</details>

**A12.** A consumer with **manual ack** dies mid-processing. The unacked message:

- a) Is lost
- b) Is redelivered (to it or another consumer), with `redelivered=true`
- c) Goes to the DLX
- d) Stays unacked forever

<details><summary>Answer</summary>

**b).** → [03](../../rabbitmq-foundations-to-advanced/03-queues-consumers.md)
</details>

**A13.** `basic.qos(prefetch_count=1)` with a very fast consumer, high network latency and a large backlog most likely gives:

- a) Maximum throughput
- b) Poor throughput: one round-trip per message
- c) Message loss
- d) Unbounded memory use in the consumer

<details><summary>Answer</summary>

**b).** Recommended range is 10–300. Unlimited prefetch risks consumer memory blow-up and uneven load. → [03](../../rabbitmq-foundations-to-advanced/03-queues-consumers.md)
</details>

**A14.** Which publisher feature tells you a message was safely stored by the broker?

- a) `mandatory` flag
- b) Publisher confirms
- c) Transactions only
- d) `delivery_mode=2`

<details><summary>Answer</summary>

**b).** For quorum queues, the confirm arrives once a **majority** of replicas has it. → [03](../../rabbitmq-foundations-to-advanced/03-queues-consumers.md), [04](../../rabbitmq-foundations-to-advanced/04-reliability-patterns.md)
</details>

**A15.** Which is **not** a dead-lettering trigger?

- a) `basic.nack` / `basic.reject` with `requeue=false`
- b) Message TTL expiry
- c) Queue length limit exceeded
- d) A successful `basic.ack`

<details><summary>Answer</summary>

**d).** The fourth trigger is exceeding the quorum queue **delivery limit** (default 20 in 4.x). → [04](../../rabbitmq-foundations-to-advanced/04-reliability-patterns.md)
</details>

**A16.** The best way to attach a DLX to many existing queues is:

- a) Redeclare every queue with `x-dead-letter-exchange`
- b) A policy, e.g. `rabbitmqctl set_policy DLX "^orders\." '{"dead-letter-exchange":"dlx"}' --apply-to queues`
- c) A plugin
- d) A client-side wrapper

<details><summary>Answer</summary>

**b).** → [04](../../rabbitmq-foundations-to-advanced/04-reliability-patterns.md)
</details>

**A17.** In the request/reply (RPC) pattern, how does the client match a reply to its request?

- a) `message_id`
- b) `correlation_id`, with replies sent to `reply_to` (e.g. `amq.rabbitmq.reply-to`)
- c) Delivery tag
- d) Routing key

<details><summary>Answer</summary>

**b).** → [04](../../rabbitmq-foundations-to-advanced/04-reliability-patterns.md)
</details>

**A18.** A 3-node cluster hosts a quorum queue with 3 members. How many nodes can fail while the queue stays available?

- a) 0
- b) 1
- c) 2
- d) 3

<details><summary>Answer</summary>

**b).** A majority (2 of 3) is needed. 5 nodes tolerate 2. → [05](../../rabbitmq-foundations-to-advanced/05-clustering-ha.md)
</details>

**A19.** You need to link brokers in two regions over a WAN. Use:

- a) One stretched cluster across regions
- b) Federation or Shovel
- c) Classic mirroring
- d) A shared Erlang cookie

<details><summary>Answer</summary>

**b).** Clusters need low-latency LANs. → [05](../../rabbitmq-foundations-to-advanced/05-clustering-ha.md)
</details>

**A20.** When a memory or disk alarm fires, RabbitMQ:

- a) Drops the oldest messages
- b) Blocks **publishing** connections cluster-wide; consumers keep running
- c) Restarts the node
- d) Disconnects all clients

<details><summary>Answer</summary>

**b).** Defaults: `vm_memory_high_watermark` 0.6 and `disk_free_limit`. → [06](../../rabbitmq-foundations-to-advanced/06-operations-security.md)
</details>

---

## 🅱️ Part B: Short Answer (8 × 3 pts = 24)

**B1.** Give three reasons to put a message broker between two services instead of calling over HTTP.

<details><summary>Answer</summary>

Decoupling (producer doesn't need the consumer up), buffering/load-levelling of spikes, retries and durability, fan-out to many consumers, scaling via competing consumers. → [01](../../rabbitmq-foundations-to-advanced/01-foundations.md)
</details>

**B2.** Describe the full path of a message from producer to consumer, naming each object.

<details><summary>Answer</summary>

Producer → (connection/channel in a vhost) → **exchange** → **binding** (matches the routing key/headers) → **queue** → consumer (push via `basic.consume`, respecting prefetch) → **ack** → the broker deletes the message. → [01](../../rabbitmq-foundations-to-advanced/01-foundations.md)
</details>

**B3.** You want to route `order.created.eu` and `order.created.us` to one queue, and every `*.error` event to another. Give the exchange type and binding keys.

<details><summary>Answer</summary>

Topic exchange. Queue 1: `order.created.*` (or `order.created.#`). Queue 2: `*.error` (or `#.error` if you need multi-word prefixes). → [02](../../rabbitmq-foundations-to-advanced/02-exchanges-routing.md)
</details>

**B4.** Why is per-message TTL on a **classic** queue problematic for delay/retry designs?

<details><summary>Answer</summary>

Expired messages are only removed when they reach the **head** of the queue. A long-TTL message at the head blocks shorter-TTL messages behind it. Use one TTL queue per delay tier (queue-level `x-message-ttl`). → [04](../../rabbitmq-foundations-to-advanced/04-reliability-patterns.md)
</details>

**B5.** What makes a consumer idempotent, and why does at-least-once delivery require it?

<details><summary>Answer</summary>

Track processed `message_id`s (e.g. a unique DB key or a dedup table) and skip duplicates, or make the operation naturally idempotent (upserts). At-least-once means redelivery after a crash/nack, so the same message **will** sometimes arrive twice. → [04](../../rabbitmq-foundations-to-advanced/04-reliability-patterns.md)
</details>

**B6.** Why prefer an **odd** number of nodes, and why does a quorum queue choose consistency over availability?

<details><summary>Answer</summary>

Raft needs a majority. 4 nodes tolerate the same 1 failure as 3, at higher cost, and an even split can leave no majority. Without a majority the queue refuses writes rather than risk divergent copies and lost confirmed messages. → [05](../../rabbitmq-foundations-to-advanced/05-clustering-ha.md)
</details>

**B7.** List the five metrics you'd alert on first.

<details><summary>Answer</summary>

Queue depth (ready), unacked count, consumer count (0 = trouble), DLQ depth, and memory/disk **alarms**. Also useful: publish vs deliver rates, connection/channel churn, file descriptors. → [06](../../rabbitmq-foundations-to-advanced/06-operations-security.md)
</details>

**B8.** Name four production security steps from the guide.

<details><summary>Answer</summary>

Delete/disable `guest`; per-application users with least-privilege vhost permissions; TLS-only listeners (5671), management behind TLS; protect the **Erlang cookie** and inter-node ports (25672, 4369); firewall everything else. → [06](../../rabbitmq-foundations-to-advanced/06-operations-security.md)
</details>

---

## 🅲 Part C: Design & Config (3 × 6 pts = 18)

**C1.** Design an order-processing topology: retries with 10 s and 60 s backoff, then a parking-lot queue. List the exchanges, queues, arguments/policies and the consumer's decision logic.

<details><summary>Answer</summary>

- `orders` (topic) → `orders.work` (quorum), with a policy DLX → `orders.dlx`.
- `orders.retry.10s`: `x-message-ttl=10000`, DLX = `""`, DL routing key `orders.work`.
- `orders.retry.60s`: `x-message-ttl=60000`, same DLX target.
- `orders.parking` (quorum) for poison messages; alert on depth > 0.
- Consumer: on success → ack. On a transient error → read the `x-death` count (or a custom `x-retries` header): retry 1 → publish to `retry.10s`, retry 2 → `retry.60s`, then → `parking`; ack the original after the publish is **confirmed**. On a permanent error → straight to `parking`.
- Consumers idempotent on `message_id`; publisher confirms everywhere.

→ [04](../../rabbitmq-foundations-to-advanced/04-reliability-patterns.md)
</details>

**C2.** The `order-api` user in vhost `shop` must only publish to exchange `orders`. The `billing` user must only consume from queue `billing.orders`. Write the `rabbitmqctl` commands.

<details><summary>Answer</summary>

```bash
rabbitmqctl add_user order-api '<strong-password>'
rabbitmqctl set_permissions -p shop order-api "^$" "^orders$" "^$"
rabbitmqctl add_user billing '<strong-password>'
rabbitmqctl set_permissions -p shop billing "^$" "^$" "^billing\.orders$"
```

Order: configure, write, read. Topology is declared beforehand by an admin/definitions import, so the apps need no `configure`. → [06](../../rabbitmq-foundations-to-advanced/06-operations-security.md)
</details>

**C3.** Write a minimal production `rabbitmq.conf` covering: TLS-only AMQP, quorum as the default queue type, sane alarms and partition handling.

<details><summary>Answer</summary>

```ini
listeners.tcp = none
listeners.ssl.default = 5671
ssl_options.cacertfile = /etc/rabbitmq/tls/ca.pem
ssl_options.certfile   = /etc/rabbitmq/tls/server.pem
ssl_options.keyfile    = /etc/rabbitmq/tls/server-key.pem
ssl_options.verify     = verify_peer
ssl_options.fail_if_no_peer_cert = false

management.ssl.port     = 15671
management.ssl.cacertfile = /etc/rabbitmq/tls/ca.pem
management.ssl.certfile   = /etc/rabbitmq/tls/server.pem
management.ssl.keyfile    = /etc/rabbitmq/tls/server-key.pem

default_queue_type = quorum
vm_memory_high_watermark.relative = 0.6
disk_free_limit.absolute = 2GB
cluster_partition_handling = pause_minority
```

→ [05](../../rabbitmq-foundations-to-advanced/05-clustering-ha.md), [06](../../rabbitmq-foundations-to-advanced/06-operations-security.md)
</details>

---

## 🅳 Part D: Troubleshooting Scenarios (3 × 6 pts = 18)

**D1.** The `emails` queue has 250 000 ready messages, 0 unacked and 0 consumers, and it's growing. Diagnose and fix, short and long term.

<details><summary>Answer</summary>

Consumers aren't connected at all: crashed, deploy failed, wrong vhost/credentials, permissions revoked, or the queue was renamed. Check app logs, `rabbitmqctl list_connections`/`list_consumers`, and auth failures in the broker log. Short term: restore consumers and scale out to drain. Long term: alert on `consumers == 0` and on depth, add `x-max-length` + overflow policy, and keep queues short. → [06](../../rabbitmq-foundations-to-advanced/06-operations-security.md)
</details>

**D2.** All producers suddenly hang on `publish`, but consumers are still receiving messages. What's going on and what do you check?

<details><summary>Answer</summary>

A resource alarm (memory or disk) is blocking publishing connections. `rabbitmq-diagnostics alarms`, `memory_breakdown`, `df` on the data dir. Usually long queues or a backlog. Drain by scaling consumers. Because publishers and consumers use **separate** connections, consumers keep working, which is exactly why the guide recommends that split. Prevent with alerts below the watermark. → [06](../../rabbitmq-foundations-to-advanced/06-operations-security.md)
</details>

**D3.** One message is redelivered thousands of times per minute, CPU is high and the queue never drains. What's happening and what are three fixes?

<details><summary>Answer</summary>

A **poison message** in a requeue loop: the consumer fails and nacks with `requeue=true`, the message goes back to the head and is delivered again. Fixes: nack with `requeue=false` + a DLX; rely on the quorum queue **delivery limit** (default 20 in 4.x) to dead-letter it automatically; add retry tiers with backoff; validate/schema-check messages before processing. → [04](../../rabbitmq-foundations-to-advanced/04-reliability-patterns.md)
</details>

---

## 🧮 Scoring

| Score | Level |
|-------|-------|
| 90–100 | 🔴 Advanced: ready to run production clusters |
| 70–89 | 🟡 Intermediate: pass, review missed chapters |
| < 70 | 🟢 Beginner: redo [playbook](playbook.md) labs 1–5 and retake |

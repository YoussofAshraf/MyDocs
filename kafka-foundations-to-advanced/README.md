# 🪵 Apache Kafka: Foundations to Advanced

A short, illustrated guide to Apache Kafka, from "what is an event log?" to exactly-once processing, Kafka Streams, Connect and production operations.
Each chapter is a summary: diagrams first, then the key ideas, then the config and code you actually write.

> Diagrams use **Mermaid** (rendered by GitHub, GitLab, Obsidian and VS Code with the Mermaid extension) and plain ASCII art.

## 🗺️ Learning Path

```mermaid
flowchart LR
    A[01 Foundations<br/>Log · Topics · Partitions] --> B[02 Producers<br/>Keys · Acks · Idempotence]
    B --> C[03 Consumers<br/>Groups · Offsets · Rebalancing]
    C --> D[04 Storage & Replication<br/>ISR · Retention · Compaction]
    D --> E[05 Ecosystem<br/>Connect · Schemas · Streams · EOS]
    E --> F[06 Operations & Security]
    F --> G[07 Cheatsheet]

    style A fill:#231f20,color:#fff
    style B fill:#231f20,color:#fff
    style C fill:#3d3839,color:#fff
    style D fill:#3d3839,color:#fff
    style E fill:#5a5455,color:#fff
    style F fill:#5a5455,color:#fff
    style G fill:#777,color:#fff
```

## 📚 Chapters

| # | Chapter | Level | You will learn |
|---|---------|-------|----------------|
| 01 | [Foundations](01-foundations.md) | 🟢 Beginner | Event streaming, the log, topics, partitions, offsets, brokers, KRaft |
| 02 | [Producers](02-producers.md) | 🟢 Beginner | Partitioning by key, acks, idempotence, batching, compression |
| 03 | [Consumers](03-consumers.md) | 🟡 Intermediate | Consumer groups, offsets and commits, rebalancing, lag, delivery semantics |
| 04 | [Storage & Replication](04-storage-replication.md) | 🟡 Intermediate | Segments, retention, compaction, replicas, ISR, `min.insync.replicas`, tiered storage |
| 05 | [Ecosystem & Exactly-Once](05-ecosystem.md) | 🔴 Advanced | Kafka Connect, Schema Registry, Kafka Streams, Flink, transactions, CDC |
| 06 | [Operations & Security](06-operations-security.md) | 🔴 Advanced | Sizing, monitoring, tuning, TLS/SASL/ACLs, deployment, upgrades |
| 07 | [Cheatsheet](07-cheatsheet.md) | 📎 Reference | CLI commands, client snippets, troubleshooting |

## 🧠 The One Idea to Remember

```
                       topic "orders" = an append-only LOG, split into partitions
                   ┌────┬────┬────┬────┬────┬────┬────┐
  Producers ─────▶ │ 0  │ 1  │ 2  │ 3  │ 4  │ 5  │ 6  │ ──▶ new events appended at the end
                   └────┴────┴────┴────┴────┴────┴────┘
                          ▲              ▲         ▲
                   analytics (offset 1)  billing  search (live)

  Reading does NOT delete. Each consumer group tracks its own position (offset).
  Events stay for the retention period (hours … forever) → replay any time.
```

## 🆚 Kafka or RabbitMQ?

| | 🪵 Kafka | 🐇 RabbitMQ |
|--|----------|------------|
| Model | Distributed **commit log** | **Message queue** broker |
| After consumption | Kept (retention), replayable | Removed on ack |
| Ordering | Per partition | Per queue (single consumer) |
| Scale | Millions of events/sec, horizontal by partitions | Tens to hundreds of thousands/sec per cluster |
| Consumers | Pull, track offsets | Push, ack per message |
| Sweet spot | Event streaming, event sourcing, CDC, analytics pipelines, log aggregation | Task queues, RPC, complex routing, per-message TTL/priority |

See the companion guide: [RabbitMQ: Foundations to Advanced](../rabbitmq-foundations-to-advanced/README.md).

## 🧪 Run It Locally (KRaft, no ZooKeeper)

```bash
docker run -d --name kafka -p 9092:9092 apache/kafka:latest
docker exec -it kafka /opt/kafka/bin/kafka-topics.sh \
  --bootstrap-server localhost:9092 --create --topic orders --partitions 3
```

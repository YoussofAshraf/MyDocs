# 🐇 RabbitMQ: Foundations to Advanced

A short, illustrated guide to RabbitMQ, from "what is a message broker?" to quorum queues, streams, clustering and production patterns.
Each chapter is a summary: diagrams first, then the key ideas, then the config and code you actually write.

> Diagrams use **Mermaid** (rendered by GitHub, GitLab, Obsidian and VS Code with the Mermaid extension) and plain ASCII art.

## 🗺️ Learning Path

```mermaid
flowchart LR
    A[01 Foundations<br/>Messaging & AMQP model] --> B[02 Exchanges<br/>Routing]
    B --> C[03 Queues & Consumers<br/>Acks · Prefetch · Confirms]
    C --> D[04 Reliability Patterns<br/>DLX · Retry · RPC]
    D --> E[05 Clustering & HA<br/>Quorum · Streams · Federation]
    E --> F[06 Operations & Security]
    F --> G[07 Cheatsheet]

    style A fill:#ff6600,color:#fff
    style B fill:#ff6600,color:#fff
    style C fill:#ff8533,color:#fff
    style D fill:#ff8533,color:#fff
    style E fill:#cc5200,color:#fff
    style F fill:#cc5200,color:#fff
    style G fill:#555,color:#fff
```

## 📚 Chapters

| # | Chapter | Level | You will learn |
|---|---------|-------|----------------|
| 01 | [Foundations](01-foundations.md) | 🟢 Beginner | Why brokers exist, the AMQP 0-9-1 model, connections and channels, vhosts |
| 02 | [Exchanges & Routing](02-exchanges-routing.md) | 🟢 Beginner | Direct, fanout, topic and headers exchanges, bindings, routing keys |
| 03 | [Queues & Consumers](03-queues-consumers.md) | 🟡 Intermediate | Queue types, durability, acks, prefetch, publisher confirms |
| 04 | [Reliability Patterns](04-reliability-patterns.md) | 🟡 Intermediate | Dead-lettering, retries, TTL, delays, priority, RPC, idempotency |
| 05 | [Clustering & High Availability](05-clustering-ha.md) | 🔴 Advanced | Clusters, quorum queues (Raft), streams, federation and shovel |
| 06 | [Operations & Security](06-operations-security.md) | 🔴 Advanced | Monitoring, alarms, tuning, users and permissions, TLS, deployment |
| 07 | [Cheatsheet](07-cheatsheet.md) | 📎 Reference | CLI commands, client code snippets, troubleshooting |

## 🧠 The One Idea to Remember

```
  ┌──────────┐  publish   ┌──────────┐  binding   ┌──────────┐  deliver   ┌──────────┐
  │ Producer │ ─────────▶ │ EXCHANGE │ ─────────▶ │  QUEUE   │ ─────────▶ │ Consumer │
  └──────────┘ + routing  └──────────┘  (rules)   └──────────┘  + ack ◀── └──────────┘
                  key       router 🔀               buffer 📥
```

Producers **never** send straight to a queue. They publish to an **exchange**, which **routes** copies of the message to queues according to **bindings**. Consumers read from queues and **acknowledge** each message. Once acked, the message is removed.

## 🆚 RabbitMQ or Kafka?

| | 🐇 RabbitMQ | 🪵 Kafka |
|--|------------|----------|
| Model | Smart broker, **message queue** | Dumb broker, **distributed log** |
| After consumption | Message removed (ack) | Message stays (retention), consumers track offsets |
| Routing | Rich (exchanges, patterns, headers) | By topic + partition key |
| Replay | Only with Streams | ✅ Built in |
| Per-message features | TTL, priority, DLX, delay | Minimal |
| Sweet spot | Task queues, RPC, complex routing, low latency | Event streaming, high throughput, event sourcing, analytics |

See the companion guide: [Kafka: Foundations to Advanced](../kafka-foundations-to-advanced/README.md).

## 🧪 Run It Locally

```bash
docker run -d --name rabbit -p 5672:5672 -p 15672:15672 rabbitmq:4-management
# Management UI → http://localhost:15672  (guest / guest, localhost only)
```

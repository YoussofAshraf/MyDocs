# 02 · Exchanges & Routing 🟢

[← Foundations](01-foundations.md) · [Next: Queues & Consumers →](03-queues-consumers.md)

## 🔀 Four Exchange Types

| Type | Routes by | Analogy | Typical use |
|------|-----------|---------|-------------|
| **direct** | Exact routing key match | Mail sorted by exact address | Task types, log levels |
| **fanout** | Ignores the key, goes to **all** bound queues | Radio broadcast 📻 | Notifications, cache invalidation |
| **topic** | Wildcard pattern on dotted keys | Subscriptions by interest | Events by domain, region, type |
| **headers** | Message header values | Filter by attributes | Multi-attribute routing (rare) |

Plus the **default exchange** (`""`): a nameless direct exchange where every queue is bound by its own name. Publishing with `routing_key="email"` goes straight to queue `email`.

## 🎯 Direct Exchange

```mermaid
flowchart LR
    P[Producer] -->|key: error| X{{direct: logs}}
    X -->|binding key: error| Q1[(errors-queue)]
    X -->|binding key: info| Q2[(info-queue)]
    X -->|binding key: error| Q3[(alerting-queue)]
    style Q1 fill:#2e7d32,color:#fff
    style Q3 fill:#2e7d32,color:#fff
```

The message with key `error` reaches **errors-queue** and **alerting-queue** (both bound with `error`). The info queue gets nothing.

## 📻 Fanout Exchange

```mermaid
flowchart LR
    P[Producer] -->|any key, ignored| X{{fanout: user.updated}}
    X --> Q1[(search-indexer)]
    X --> Q2[(cache-invalidator)]
    X --> Q3[(audit-log)]
```

Each queue gets **its own copy**. This is pub/sub: add a subscriber by binding a new queue.

## 🌿 Topic Exchange

Routing keys are words separated by dots: `<domain>.<event>.<region>`.

```
  *  = exactly one word
  #  = zero or more words

  binding pattern       order.created.eu   order.paid.us   order.created   user.created.eu
  ───────────────       ────────────────   ─────────────   ─────────────   ───────────────
  order.*.eu                   ✅                ❌              ❌               ❌
  order.#                      ✅                ✅              ✅               ❌
  *.created.*                  ✅                ❌              ❌               ✅
  #.eu                         ✅                ❌              ❌               ✅
  #                            ✅                ✅              ✅               ✅  (= fanout)
```

```mermaid
flowchart LR
    P[Producer] -->|order.created.eu| X{{topic: events}}
    X -->|order.#| Q1[(order-service)]
    X -->|*.*.eu| Q2[(eu-compliance)]
    X -->|user.#| Q3[(user-service)]
    style Q1 fill:#2e7d32,color:#fff
    style Q2 fill:#2e7d32,color:#fff
```

## 🏷️ Headers Exchange

```
  headers: { format: "pdf", type: "report" }

  binding A: x-match=all, format=pdf, type=report  → ✅ (all must match)
  binding B: x-match=any, format=zip, type=report  → ✅ (one is enough)
  binding C: x-match=all, format=zip               → ❌
```

## 🔗 Exchange-to-Exchange Bindings

```mermaid
flowchart LR
    P[Producer] --> X1{{topic: all-events}}
    X1 -->|order.#| X2{{fanout: orders}}
    X1 -->|#.eu| X3{{topic: eu-events}}
    X2 --> Q1[(billing)]
    X2 --> Q2[(analytics)]
    X3 --> Q3[(gdpr-audit)]
```

Use them to build routing hierarchies without changing producers.

## 🧭 Unroutable Messages

```
  publish → exchange → no binding matches → 🕳️ silently DROPPED (default)

  Fixes:
   • mandatory=true flag → broker returns the message to the publisher (basic.return)
   • alternate-exchange  → unroutable messages go to a fallback exchange/queue ✅
```

## 🛠️ Declaring Topology (Python / pika)

```python
import pika

conn = pika.BlockingConnection(pika.URLParameters("amqp://guest:guest@localhost:5672/%2F"))
ch = conn.channel()

ch.exchange_declare("events", exchange_type="topic", durable=True)
ch.queue_declare("order-service", durable=True, arguments={"x-queue-type": "quorum"})
ch.queue_bind("order-service", "events", routing_key="order.#")

ch.basic_publish(
    exchange="events",
    routing_key="order.created.eu",
    body=b'{"orderId": 42}',
    properties=pika.BasicProperties(content_type="application/json", delivery_mode=2),
)
```

> 💡 Declarations are **idempotent**: re-declaring with the same arguments is a no-op, but different arguments cause an error (`PRECONDITION_FAILED`). Declare topology on app startup, or manage it centrally with definitions or Terraform.

## 🧭 Which Exchange Should I Use?

```mermaid
flowchart TD
    Q1{Every subscriber gets<br/>every message?} -->|Yes| F[fanout]
    Q1 -->|No| Q2{Route by<br/>exact key?}
    Q2 -->|Yes| D[direct]
    Q2 -->|No| Q3{Hierarchical keys<br/>+ wildcards?}
    Q3 -->|Yes| T[topic ⭐ most flexible]
    Q3 -->|No| H[headers]
```

## ✅ Key Takeaways

- **direct** = exact key, **fanout** = broadcast, **topic** = wildcards (`*` one word, `#` zero or more), **headers** = attributes.
- Each bound queue gets **its own copy** of a matching message.
- Unroutable messages are dropped unless you use `mandatory` or an **alternate exchange**.
- Design routing keys as `domain.event.qualifier` so topic routing stays easy.

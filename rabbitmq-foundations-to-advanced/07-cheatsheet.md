# 07 · RabbitMQ Cheatsheet 📎

[← Operations & Security](06-operations-security.md) · [Back to Index](README.md)

## 🧰 CLI Tools

| Tool | Purpose |
|------|---------|
| `rabbitmqctl` | Manage users, vhosts, permissions, policies, cluster |
| `rabbitmq-diagnostics` | Health checks, status, observability |
| `rabbitmq-plugins` | Enable or disable plugins |
| `rabbitmq-queues` | Quorum queue and stream membership operations |
| `rabbitmqadmin` | HTTP API CLI (declare, publish, get) |

## 🔎 Inspect

```bash
rabbitmq-diagnostics status
rabbitmq-diagnostics -q ping                      # liveness
rabbitmq-diagnostics check_port_connectivity
rabbitmq-diagnostics cluster_status
rabbitmqctl list_queues name type messages_ready messages_unacknowledged consumers
rabbitmqctl list_exchanges name type
rabbitmqctl list_bindings
rabbitmqctl list_connections name user state
rabbitmqctl list_consumers
rabbitmq-diagnostics alarms
```

## ✍️ Manage

```bash
rabbitmqctl add_vhost shop
rabbitmqctl add_user app 'secret'
rabbitmqctl set_permissions -p shop app ".*" ".*" ".*"
rabbitmqctl set_user_tags admin administrator
rabbitmqctl set_policy -p shop DLX "^orders\." \
  '{"dead-letter-exchange":"dlx","delivery-limit":5}' --apply-to queues
rabbitmqctl purge_queue orders.q -p shop          # ⚠️ deletes messages
rabbitmqctl delete_queue orders.q -p shop
rabbitmq-plugins enable rabbitmq_management rabbitmq_prometheus rabbitmq_shovel
```

## 🕸️ Cluster

```bash
# on rabbit-2 (same Erlang cookie as rabbit-1)
rabbitmqctl stop_app
rabbitmqctl join_cluster rabbit@rabbit-1
rabbitmqctl start_app

rabbitmqctl forget_cluster_node rabbit@old-node
rabbitmq-queues add_member orders.q rabbit@rabbit-4 -p shop
rabbitmq-queues grow rabbit@rabbit-4 all          # add a new node to quorum queues
rabbitmq-upgrade drain                            # before maintenance
```

## 🐍 Python (pika): Publisher with Confirms

```python
import json, pika

conn = pika.BlockingConnection(pika.URLParameters("amqp://app:secret@localhost:5672/shop"))
ch = conn.channel()
ch.confirm_delivery()                     # publisher confirms
ch.exchange_declare("orders", "topic", durable=True)

try:
    ch.basic_publish(
        "orders", "order.created.eu",
        json.dumps({"orderId": 42}).encode(),
        pika.BasicProperties(content_type="application/json",
                             delivery_mode=2, message_id="ord-42-created"),
        mandatory=True,
    )
except pika.exceptions.UnroutableError:
    print("no queue bound!")
```

## 🟩 Node.js (amqplib): Consumer

```js
import amqp from "amqplib";

const conn = await amqp.connect("amqp://app:secret@localhost:5672/shop");
const ch = await conn.createChannel();
await ch.assertQueue("email.q", { durable: true, arguments: { "x-queue-type": "quorum" } });
await ch.bindQueue("email.q", "orders", "order.created.*");
await ch.prefetch(20);

ch.consume("email.q", async (msg) => {
  try {
    await sendEmail(JSON.parse(msg.content.toString()));
    ch.ack(msg);
  } catch (err) {
    ch.nack(msg, false, false);            // → dead-letter
  }
});
```

## 🩻 Troubleshooting Flow

```mermaid
flowchart TD
    S[Problem] --> Q{Symptom?}
    Q -->|Queue keeps growing| A1[Consumers count = 0?<br/>Consumers too slow → scale out,<br/>raise prefetch, profile handler]
    Q -->|Many unacked, nothing moves| A2[Missing ack in code,<br/>consumer stuck / deadlocked]
    Q -->|Publishers hang| A3[Memory/disk alarm?<br/>rabbitmq-diagnostics alarms]
    Q -->|Messages vanish| A4[Unroutable? No binding match →<br/>mandatory / alternate-exchange<br/>TTL expired? auto-ack crash?]
    Q -->|Same message over and over| A5[Poison message requeued<br/>→ delivery-limit + DLX]
    Q -->|PRECONDITION_FAILED| A6[Redeclared with different args<br/>→ align args or use policies]
    Q -->|ACCESS_REFUSED| A7[Wrong vhost / permissions<br/>guest from a remote host]
```

## 🔢 Ports

| Port | Use |
|------|-----|
| 5672 / 5671 | AMQP / AMQP over TLS |
| 15672 | Management UI and HTTP API |
| 15692 | Prometheus metrics |
| 5552 / 5551 | Stream protocol / over TLS |
| 1883 / 8883 | MQTT / over TLS |
| 61613 | STOMP |
| 25672 | Inter-node and CLI communication |
| 4369 | epmd (peer discovery) |

## 📋 Golden Rules

```
 1. Long-lived connections, one channel per thread
 2. Quorum queues for anything that matters
 3. Publisher confirms + manual acks + persistent messages
 4. Prefetch set (never unlimited)
 5. DLX + delivery-limit on every work queue, alert on DLQ > 0
 6. Idempotent consumers (dedupe by message_id)
 7. Keep messages small and queues short
 8. Policies over hard-coded queue arguments
 9. TLS + per-app users + least privilege, no guest
10. Monitor depth, unacked, consumers, alarms
```

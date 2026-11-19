# 🐰 RabbitMQ Playbook

[← Practicals](../README.md) · [Exam →](exam.md) · [Guide](../../rabbitmq-foundations-to-advanced/README.md)

Hands-on labs (Part 1) and incident runbooks (Part 2). Every lab follows **Goal → Steps → ✅ Verify → 🧹 Cleanup**.

## 🧰 Prerequisites & Setup

Everything runs in Docker. The [`lab/`](lab/) folder contains:

| File | Purpose |
|------|---------|
| [`compose.yaml`](lab/compose.yaml) | 3-node RabbitMQ 4.1 cluster (`rabbit1..3`), management UI on `127.0.0.1:15672`, Prometheus on `:15692` |
| [`rabbitmq.conf`](lab/rabbitmq.conf) | Peer discovery + lab user `admin` / `change-me` |
| [`rmq.py`](lab/rmq.py) + [`Dockerfile`](lab/Dockerfile) | Tiny `pika` CLI: `exchange`, `queue`, `bind`, `publish` (with confirms), `consume` (manual acks) |

```bash
cd practicals/rabbitmq/lab
docker build -t rmq-cli .
docker compose up -d
docker compose ps                    # wait until all 3 are (healthy)

# Helpers. Define these in every terminal you use.
r()   { docker run --rm --network rmqlab_default ${AMQP_URL:+-e AMQP_URL=$AMQP_URL} rmq-cli "$@"; }
ri()  { docker run --rm -it --network rmqlab_default ${AMQP_URL:+-e AMQP_URL=$AMQP_URL} rmq-cli "$@"; }  # long-running consumers
ctl() { docker compose exec -T rabbit1 rabbitmqctl -q "$@"; }
diag(){ docker compose exec -T rabbit1 rabbitmq-diagnostics -q "$@"; }
```

> 💡 Queue counts in `list_queues` and the UI are refreshed every few seconds. If a number looks wrong, wait 5 s and run it again.

---

# Part 1 · 🧪 Labs

## Lab 1 · Cluster Tour & the Management UI 🟢

**Goal:** find the building blocks from [ch. 01](../../rabbitmq-foundations-to-advanced/01-foundations.md).

```bash
ctl cluster_status | sed -n '/Running Nodes/,/Versions/p'
ctl list_vhosts
ctl list_exchanges name type          # the default "" exchange and the amq.* ones
ctl list_users
```

Open <http://localhost:15672> (admin / change-me) and find: Overview → nodes; Connections; Channels; Exchanges; Queues.

Now open a consumer in a second terminal (`ri consume demo`, after `r queue demo`) and refresh **Connections** and **Channels**.

✅ **Verify:** 3 running nodes; one connection with one channel per running client.

🧠 **Explain:** why is the guidance "one connection per process, one channel per thread", and separate connections for publishing and consuming? (Hint: [Lab 9](#lab-9--resource-alarms-block-publishers-).)

---

## Lab 2 · Exchange Types & Routing 🟢

**Goal:** route the same messages four different ways. → [ch. 02](../../rabbitmq-foundations-to-advanced/02-exchanges-routing.md)

```bash
# Direct
r exchange orders.direct direct
r queue q.paid;    r bind q.paid    orders.direct paid
r queue q.shipped; r bind q.shipped orders.direct shipped
r publish orders.direct paid    "order 1 paid"
r publish orders.direct shipped "order 1 shipped"

# Fanout: routing key ignored
r exchange notify fanout
r queue q.email; r bind q.email notify
r queue q.sms;   r bind q.sms   notify
r publish notify whatever "flash sale"

# Topic: * = exactly one word, # = zero or more
r exchange logs topic
r queue q.errors;  r bind q.errors  logs '*.error'
r queue q.kernel;  r bind q.kernel  logs 'kern.#'
for k in kern.error app.error kern.disk.full app.info; do r publish logs $k "$k"; done

# Headers: match on headers, not the key
r exchange docs headers
r queue q.pdf-reports; r bind q.pdf-reports docs "" --arg x-match=all --arg format=pdf --arg type=report
r publish docs "" "pdf report"  --header format=pdf --header type=report
r publish docs "" "pdf invoice" --header format=pdf --header type=invoice

sleep 5; ctl list_queues name messages
```

Fill in your **prediction** before checking:

| Queue | Predicted | Actual |
|-------|-----------|--------|
| q.paid / q.shipped | | |
| q.email / q.sms | | |
| q.errors | | |
| q.kernel | | |
| q.pdf-reports | | |

✅ **Verify:** q.paid 1, q.shipped 1, q.email 1, q.sms 1, **q.errors 2** (`kern.error`, `app.error`), **q.kernel 2** (`kern.error`, `kern.disk.full`), q.pdf-reports 1. `app.info` went nowhere.

**Unroutable messages are silently dropped** unless you ask:

```bash
r publish logs app.debug "lost"                     # confirmed: but no queue has it!
r publish logs app.debug "lost" --mandatory         # RETURNED (unroutable)
```

🎯 **Stretch:** create an alternate exchange so nothing is ever lost: `r exchange unrouted fanout; r queue q.unrouted; r bind q.unrouted unrouted`, then `ctl set_policy AE "^logs$" '{"alternate-exchange":"unrouted"}' --apply-to exchanges` and publish `app.debug` again.

🎯 **Stretch 2:** try `r exchange logs direct`. You get `PRECONDITION_FAILED`. Why?

---

## Lab 3 · Durability: The Three Requirements 🟢

**Goal:** prove all three are needed to survive a restart. → [ch. 03](../../rabbitmq-foundations-to-advanced/03-queues-consumers.md)

```bash
r queue q.durable                                                  # the helper declares durable queues
r publish "" q.durable "persistent msg"                            # delivery_mode=2
r publish "" q.durable "transient msg" --transient                 # delivery_mode=1
docker run --rm --network rmqlab_default --entrypoint python rmq-cli -c "
import pika; c=pika.BlockingConnection(pika.URLParameters('amqp://admin:change-me@rabbit1/%2F'))
c.channel().queue_declare('q.temp', durable=False); print('non-durable queue created')"
r publish "" q.temp "in a non-durable queue"

sleep 5; ctl list_queues name durable messages | grep -E 'q\.(durable|temp)'
docker compose restart rabbit1 rabbit2 rabbit3
sleep 30; ctl list_queues name durable messages | grep -E 'q\.(durable|temp)'
r consume q.durable --idle 3
```

✅ **Verify:** after the restart `q.temp` is gone, and `q.durable` holds **only** the persistent message.

> Classic queue in this lab. Quorum queues are always durable and persist every message, which is one reason [ch. 03](../../rabbitmq-foundations-to-advanced/03-queues-consumers.md) recommends them by default.

---

## Lab 4 · Manual Acks, Redelivery & Prefetch 🟡

**Goal:** see why unacked messages are never lost, and how prefetch shapes load. → [ch. 03](../../rabbitmq-foundations-to-advanced/03-queues-consumers.md)

```bash
r queue tasks --arg x-queue-type=quorum

# Crash before ack → redelivered
r publish "" tasks "important job"
r consume tasks --no-ack-exit          # receives it, dies without acking
r consume tasks --idle 3               # same message again, redelivered=True
```

**Competing consumers + prefetch.** Open two terminals:

```bash
# Terminal A: a slow consumer that grabs a big batch
ri consume tasks --name SLOW --work 2 --prefetch 50
# Terminal B: a fast consumer
ri consume tasks --name FAST --work 0.1 --prefetch 50
```

```bash
r publish "" tasks job --count 40
```

Watch who processes what, then Ctrl-C both. Repeat with `--prefetch 1` on both.

✅ **Verify:** with prefetch 50, about half the jobs sit waiting on SLOW (the UI shows them as **Unacked**) while FAST is idle. With prefetch 1, FAST does most of the work.

🧠 **Explain:** why does [ch. 03](../../rabbitmq-foundations-to-advanced/03-queues-consumers.md) recommend prefetch 10–300 instead of 1 or unlimited?

---

## Lab 5 · Publisher Confirms & Overflow 🟡

**Goal:** see the broker refuse a message, and how the publisher learns about it. → [ch. 03](../../rabbitmq-foundations-to-advanced/03-queues-consumers.md), [ch. 04](../../rabbitmq-foundations-to-advanced/04-reliability-patterns.md)

```bash
r queue bounded --arg x-max-length=3 --arg x-overflow=reject-publish
r publish "" bounded job --count 5
```

✅ **Verify:** jobs #1–#3 are `confirmed`; #4 is `NACKED by broker`.

🎯 **Stretch:** recreate it with `x-overflow=drop-head` (the default) and a DLX. The oldest messages are dead-lettered with reason `maxlen` instead.

🧠 **Explain:** without publisher confirms, how would the producer know #4 was never stored?

---

## Lab 6 · Dead-Lettering & Retry with Backoff 🟡

**Goal:** build the policy-based DLX and the TTL retry loop from [ch. 04](../../rabbitmq-foundations-to-advanced/04-reliability-patterns.md).

```bash
# 1) DLX via policy (preferred over queue arguments: changeable without redeclaring)
r exchange dlx fanout
r queue orders.dead --arg x-queue-type=quorum; r bind orders.dead dlx
ctl set_policy DLX '^orders\.main$' '{"dead-letter-exchange":"dlx"}' --apply-to queues
r queue orders.main --arg x-queue-type=quorum

r publish "" orders.main "poison order"
r consume orders.main --reject --idle 3       # nack requeue=false
r consume orders.dead --idle 3                # x-death=rejected/1
```

```bash
# 2) Delayed retry: a TTL queue that dead-letters back into the work queue
r queue orders.work --arg x-queue-type=quorum
r queue orders.retry-5s --arg x-queue-type=quorum --arg x-message-ttl=5000 \
  --arg x-dead-letter-exchange= --arg x-dead-letter-routing-key=orders.work

r publish "" orders.retry-5s "retry me"
sleep 2; ctl list_queues name messages | grep orders.retry
sleep 6; ctl list_queues name messages | grep orders.work
r consume orders.work --idle 3                # x-death=expired/1
```

✅ **Verify:** the rejected message lands in `orders.dead` with reason `rejected`; the retried one appears in `orders.work` about 5 s later with reason `expired`.

🧠 **Explain:** quorum queues also dead-letter after the **delivery limit** (default 20 in 4.x). Which of the four dead-letter triggers did you see here, and which are left?

🎯 **Stretch:** design a 3-tier retry (5 s → 1 min → 10 min → `orders.dead`) where the consumer reads the `x-death` count to pick the next tier. Draw it first.

---

## Lab 7 · Quorum Queues & Failover 🔴

**Goal:** see Raft majority in action. → [ch. 05](../../rabbitmq-foundations-to-advanced/05-clustering-ha.md)

```bash
r queue payments --arg x-queue-type=quorum
r publish "" payments "before failure"
ctl list_queues name type leader members | grep payments

# Lose 1 of 3 → still a majority
LEADER=$(ctl list_queues name leader | awk '$1=="payments"{print $2}' | cut -d@ -f2)
echo "leader is $LEADER"
docker compose stop "$LEADER"
OTHER=$(for n in rabbit1 rabbit2 rabbit3; do [ $n != "$LEADER" ] && echo $n && break; done)
AMQP_URL=amqp://admin:change-me@$OTHER:5672/%2F r publish "" payments "after 1 failure"
docker compose exec -T $OTHER rabbitmqctl -q list_queues name leader messages | grep payments   # new leader

# Lose 2 of 3 → no majority → writes refused
THIRD=$(for n in rabbit1 rabbit2 rabbit3; do [ $n != "$LEADER" ] && [ $n != "$OTHER" ] && echo $n; done)
docker compose stop "$THIRD"
AMQP_URL=amqp://admin:change-me@$OTHER:5672/%2F r publish "" payments "minority" \
  || echo "refused without a majority ✅"

docker compose start "$LEADER" "$THIRD"
sleep 30; AMQP_URL=amqp://admin:change-me@$OTHER:5672/%2F r consume payments --idle 3
```

✅ **Verify:** a new leader is elected after the first stop; with two nodes down, the publish is **nacked or times out** (consistency over availability); after recovery the queue holds `before failure` and `after 1 failure` only.

> If the minority publish hangs instead of failing, press Ctrl-C. Waiting with no reply is how a blocked publish looks.

🧠 **Explain:** why is a 2-node or 4-node cluster a bad idea? How many failures does a 5-node quorum queue tolerate?

---

## Lab 8 · Multi-Tenancy & Least-Privilege Permissions 🔴

**Goal:** apply the permission model from [ch. 06](../../rabbitmq-foundations-to-advanced/06-operations-security.md).

```bash
ctl add_vhost shop
ctl add_user order-api 'order-api-pw'
ctl set_permissions -p shop admin ".*" ".*" ".*"
AMQP_URL=amqp://admin:change-me@rabbit1:5672/shop r exchange orders topic

#                       vhost user       configure write      read
ctl set_permissions -p shop order-api "^$"     "^orders$" "^$"
ctl list_user_permissions order-api

export AMQP_URL=amqp://order-api:order-api-pw@rabbit1:5672/shop
r publish orders order.created "ok"            # ✅ write to 'orders' exchange
r queue sneaky                                 # ❌ ACCESS_REFUSED (configure)
r exchange evil fanout                         # ❌ ACCESS_REFUSED (configure)
unset AMQP_URL
```

✅ **Verify:** publishing succeeds; both declarations fail with `ACCESS_REFUSED`.

🎯 **Stretch:** add a `billing` user that can only **read** a queue `billing.orders` bound to `orders`. Which permission regexes does it need? (Consuming needs `read` on the queue. Declaring and binding it needs `configure` on the queue, `write` on the queue and `read` on the exchange.)

---

## Lab 9 · Resource Alarms Block Publishers 🔴

**Goal:** trigger a memory alarm and observe flow control. → [ch. 06](../../rabbitmq-foundations-to-advanced/06-operations-security.md)

```bash
r queue alarm-test
ctl set_vm_memory_high_watermark absolute 10MB          # force the alarm
diag alarms                                             # Memory alarm on node rabbit@rabbit1
```

In a second terminal, start a consumer first, then try to publish from the first:

```bash
ri consume alarm-test --name C          # terminal 2: consumers keep working
r publish "" alarm-test "will block"    # terminal 1: hangs (connection is "blocked")
```

While it hangs, check the connection states in a third terminal or in the UI: `ctl list_connections name state` → the publisher is `blocked`.

```bash
ctl set_vm_memory_high_watermark 0.6                    # restore the default
```

✅ **Verify:** the hung publish completes the moment the alarm clears, and consumer C receives it.

🧠 **Explain:** if the publisher and the consumer shared **one** connection, what would happen during an alarm?

---

## Lab 10 · Monitoring, Definitions & Upgrade Checks 🟡

**Goal:** run the operational commands from [ch. 06](../../rabbitmq-foundations-to-advanced/06-operations-security.md).

```bash
# Prometheus endpoint
curl -s localhost:15692/metrics | grep -E '^rabbitmq_(queue_messages_ready|queue_messages_unacked|queue_consumers)' | head

# Health checks
diag check_running
diag check_local_alarms
diag check_port_connectivity
diag check_if_any_deprecated_features_are_used

# Who is consuming what
ctl list_queues name messages_ready messages_unacknowledged consumers
ctl list_consumers

# Export topology (keep it in git, restore with import_definitions)
ctl export_definitions - > definitions.json
jq '{queues: (.queues|length), exchanges: (.exchanges|length), policies: (.policies|length)}' definitions.json
```

✅ **Verify:** the metrics endpoint returns `rabbitmq_*` series; all health checks pass; `definitions.json` contains your lab exchanges, queues, bindings, users and policies.

🧹 **Cleanup (after all labs):** `docker compose down -v && docker rmi rmq-cli`

---

# Part 2 · 🚨 Incident Runbooks

Each runbook follows **Symptom → Triage → Likely causes → Fix → Prevent.**

## RB-1 · Queue depth growing

```bash
rabbitmqctl list_queues name messages_ready messages_unacknowledged consumers
```

| Pattern | Cause | Fix |
|---------|-------|-----|
| `consumers = 0` | Consumers crashed / disconnected | Restart, check credentials/permissions, alert on consumer count |
| `ready` high, `unacked ≈ consumers × prefetch` | Too slow | Scale consumers, tune prefetch, batch I/O |
| `unacked` high, nothing acked | Consumer stuck or forgets to ack | Thread dumps; ack in `finally`; set a consumer timeout |
| Same message redelivered forever | Poison message, requeue loop | `requeue=false` + DLX; quorum delivery limit |

**Prevent:** `x-max-length` + overflow policy, DLQ alerts, idempotent consumers keyed on `message_id`.

## RB-2 · Publishers hang / time out

1. `rabbitmq-diagnostics alarms`: memory or disk alarm? Every publishing connection is **blocked**.
2. Memory: `rabbitmq-diagnostics memory_breakdown`. Look for long queues, too many connections/channels, big messages.
3. Disk: free space vs `disk_free_limit`.
4. Drain backlogs (scale consumers), purge only with sign-off, add capacity.
5. **Prevent:** separate publish/consume connections, short queues, alerts *before* the watermark, streams for very high volume.

## RB-3 · Messages "disappear"

1. Unroutable? Check the binding keys against the routing key (`*` vs `#`). Use `mandatory` or an **alternate exchange**.
2. Expired? A TTL on the queue or message. Is there a DLX?
3. Overflow with `drop-head`? Check `x-max-length`.
4. Auto-ack consumer crashed mid-processing → switch to manual acks.
5. Non-durable queue / transient messages lost on restart → durable + persistent + quorum.
6. Published without confirms during a failure → enable **publisher confirms** and retry.

## RB-4 · Node down / network partition

1. `rabbitmqctl cluster_status`: running nodes and partitions.
2. Quorum queues: still available if a **majority** of members is up. `rabbitmq-queues check_if_node_is_quorum_critical` before taking a node down.
3. Classic queues on the failed node are unavailable until it returns (mirroring is gone in 4.0, so migrate to quorum).
4. `cluster_partition_handling = pause_minority` stops the minority side to protect consistency.
5. Clients: use several hosts / a load balancer and automatic reconnection with topology recovery.

## RB-5 · Upgrade

1. Read the release notes; run `rabbitmq-diagnostics check_if_any_deprecated_features_are_used`.
2. Enable **all feature flags** on the current version before moving on: `rabbitmqctl enable_feature_flag all`.
3. Export definitions as a backup.
4. Rolling upgrade, one node at a time; check `check_if_node_is_quorum_critical` before each node.
5. For major jumps: blue/green with a new cluster and **shovel/federation** to move traffic.

---

## ✅ Completion Checklist

- [ ] Labs 1–3 (🟢) done
- [ ] Labs 4–6, 10 (🟡) done
- [ ] Labs 7–9 (🔴) done
- [ ] Can explain each runbook from memory
- [ ] Scored ≥ 70 on the [exam](exam.md)

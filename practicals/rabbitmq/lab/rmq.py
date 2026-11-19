#!/usr/bin/env python3
"""Tiny RabbitMQ lab helper (pika). Run `rmq.py -h` for commands."""
import argparse, json, os, sys, time
import pika

URL = os.environ.get("AMQP_URL", "amqp://admin:change-me@rabbit1:5672/%2F")

def chan():
    conn = pika.BlockingConnection(pika.URLParameters(URL))
    return conn, conn.channel()

def kv(pairs):
    out = {}
    for p in pairs or []:
        k, v = p.split("=", 1)
        out[k] = int(v) if v.lstrip("-").isdigit() else v
    return out

def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("exchange"); e.add_argument("name"); e.add_argument("type"); e.add_argument("--arg", action="append")
    q = sub.add_parser("queue"); q.add_argument("name"); q.add_argument("--arg", action="append", help="x-queue-type=quorum etc.")
    b = sub.add_parser("bind"); b.add_argument("queue"); b.add_argument("exchange"); b.add_argument("key", nargs="?", default=""); b.add_argument("--arg", action="append")
    p = sub.add_parser("publish"); p.add_argument("exchange"); p.add_argument("key"); p.add_argument("body", nargs="+")
    p.add_argument("--transient", action="store_true"); p.add_argument("--mandatory", action="store_true")
    p.add_argument("--header", action="append"); p.add_argument("--ttl"); p.add_argument("--count", type=int, default=1); p.add_argument("--id")
    c = sub.add_parser("consume"); c.add_argument("queue"); c.add_argument("--prefetch", type=int, default=10)
    c.add_argument("--work", type=float, default=0, help="seconds per message"); c.add_argument("--reject", action="store_true", help="nack requeue=false every message")
    c.add_argument("--no-ack-exit", action="store_true", help="receive one message, never ack, exit"); c.add_argument("--name", default="consumer")
    c.add_argument("--idle", type=float, default=0, help="exit after N idle seconds (0 = run forever)")
    a = ap.parse_args()

    conn, ch = chan()
    if a.cmd == "exchange":
        ch.exchange_declare(a.name, a.type, durable=True, arguments=kv(a.arg)); print(f"exchange {a.name} ({a.type}) ok")
    elif a.cmd == "queue":
        r = ch.queue_declare(a.name, durable=True, arguments=kv(a.arg)); print(f"queue {a.name} ok, {r.method.message_count} msgs")
    elif a.cmd == "bind":
        ch.queue_bind(a.queue, a.exchange, routing_key=a.key, arguments=kv(a.arg)); print(f"bind {a.exchange} -[{a.key}]-> {a.queue} ok")
    elif a.cmd == "publish":
        ch.confirm_delivery()
        for i in range(a.count):
            body = " ".join(a.body) + (f" #{i+1}" if a.count > 1 else "")
            props = pika.BasicProperties(delivery_mode=1 if a.transient else 2, headers=kv(a.header) or None,
                                         expiration=a.ttl, message_id=a.id or f"m-{time.time_ns()}")
            try:
                ch.basic_publish(a.exchange, a.key, body.encode(), props, mandatory=a.mandatory)
                print(f"confirmed: {body}")
            except pika.exceptions.UnroutableError:
                print(f"RETURNED (unroutable): {body}")
            except pika.exceptions.NackError:
                print(f"NACKED by broker (not safely stored): {body}"); sys.exit(1)
    elif a.cmd == "consume":
        ch.basic_qos(prefetch_count=a.prefetch)
        try:
            for m, props, body in ch.consume(a.queue, inactivity_timeout=a.idle or None):
                if m is None:
                    print(f"[{a.name}] idle {a.idle}s, exiting"); break
                deaths = (props.headers or {}).get("x-death")
                info = f"  x-death={deaths[0]['reason']}/{deaths[0]['count']}" if deaths else ""
                print(f"[{a.name}] {body.decode()}  redelivered={m.redelivered}{info}", flush=True)
                if a.no_ack_exit:
                    os._exit(0)          # die without acking: the message goes back to the queue
                time.sleep(a.work)
                if a.reject:
                    ch.basic_nack(m.delivery_tag, requeue=False)
                else:
                    ch.basic_ack(m.delivery_tag)
        except KeyboardInterrupt:
            pass
    conn.close()

if __name__ == "__main__":
    main()

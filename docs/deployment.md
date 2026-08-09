# Deploying a table

A table is one Python process. `uv run cardtable` gathers it and it answers until it is stopped: the company
that joined, the position they play from, the windows a take-back stands in and the streams that carry all of
it are held in that one process's memory. On a machine you have a shell on, that is the whole of deployment —
start it, leave it running, and hand people the address it printed.

This document is about the other machine. Shared hosting gives you a domain, a certificate and a control
panel, and the way to run Python there is to name a file the panel imports. cPanel's *Setup Python App* is the
common one, and what it imports is a **WSGI** application: a callable the server hands one request and takes
one answer from, under a worker it starts and stops as it pleases. A table asks for the opposite of both, so
the file that gets named holds no table at all — it starts one beside itself and passes every request through
to it.

`deploy/main.py` is that file. What follows states the problem it solves, how to put it in place, and what to
read when a deployment misbehaves. The public table at `https://cards.jakim.it` runs exactly this way.

---

## 1. What a table needs of the machine it runs on

Three things, each a consequence of the design rather than a preference (`docs/architecture.md` §10):

- **One process.** The lobby, every gathering in it, each table's position and journal, and the grace window a
  round settles after are all held in memory. Two processes serving one domain are two tables, each gathering
  behind a join code of its own, with a company split between them by whichever worker happened to take each
  request.
- **One event loop, running for as long as the table does.** A page waits on a commit through an `asyncio`
  condition — `TableSession._commits` and `Gathering._changed` — and a condition binds to the loop that first
  waits on it. A second loop meeting the same condition raises `is bound to a different event loop` and leaves
  it locked, so every page waiting on that table waits forever.
- **Answers that never end.** Commits reach a page over server-sent events: the table writes a frame whenever
  the room changes, and the connection stays open between frames for as long as the page is there. Closing it
  is how the table learns a page has left, which is what the presence in the room is read from.

A fourth follows from the first: a table lives as long as its process, so a restart deals a fresh one. That is
true of every deployment, local or public.

## 2. What a WSGI host offers instead

Passenger starts a worker when load asks for one and stops it when load falls away, so the count of processes
behind a domain is the host's business and changes through the day. A WSGI callable is synchronous: it is
handed a request, and whatever async machinery runs underneath it belongs to that one answer.

**The adapter that suggests itself is the trap**, and it is worth naming because it looks like it works. Wrap
the FastAPI application in a small ASGI-to-WSGI shim that calls `asyncio.run` per request, name the shim in
the panel, and the site comes up: the lobby draws, the offerings list, a join code is printed. Then

- each worker announces a table of its own, under a different join code, and the code changes as you refresh;
- every `POST` is refused `422`, since the shim never delivers the body the way ASGI states it;
- a stream dies after one frame, because the loop that produced the frame is closed the moment that answer is
  whole;
- and the conditions above are left locked behind loops that no longer exist.

## 3. The shape that works

```
browser ──HTTPS──▶ the host's own server (LiteSpeed or Apache)
                        │
                        ▼
                   Passenger worker ── imports deploy/main.py:application
                        │                   (as many workers as the host likes)
                        │ HTTP over 127.0.0.1:8421
                        ▼
                   one cardtable process ── uvicorn, started once, session of its own
                        │
                   the table, the lobby, the streams
```

The entry file starts the table's own server once, on the loopback address nobody outside the machine
reaches, and passes every request through to it as it stands: the headers as they came, the body as it was
written, and the answer streamed back chunk by chunk so an event stream reaches the page as it is written
rather than when it ends. However many workers the host runs and however often it recycles them, the company
stays at the one table.

Three details of the pass-through earn their place:

- **The start happens once.** Several workers meeting a stopped table all reach for it at the same moment, so
  the start is taken under a file lock: the first worker through starts the process and waits for it to
  answer, and the rest find it answering. The child is started with `start_new_session=True`, which is what
  carries it through the recycling of the worker that started it — and through the panel's own restart button,
  which restarts workers.
- **The caller's address is stated afresh.** Whatever arrived under `X-Forwarded-For` is dropped and the
  worker's own `REMOTE_ADDR` put in its place, so the lobby counts a wrong join code against the guest who
  offered it rather than against the one proxy every guest arrives through.
- **The child imports the checkout.** The panel runs the entry under an interpreter of its own making, so the
  child is given a `PYTHONPATH` naming this checkout ahead of anything else, and the table it gathers is the
  package standing beside the entry file.

## 4. Setting it up

**1. Put the whole checkout on the server, with the entry file at its root.** `cardtable.paths` climbs from
its own module to the checkout and names the configuration, the artwork and the built page from there, so
`src`, `assets`, `frontend/dist` and `config.yaml` belong around `main.py`. Copying the entry file somewhere
on its own leaves a table that starts and then answers for no page.

**2. Build the interface on the server.** `frontend/dist` is gitignored, so a deploy carries source and no
page:

```bash
make interface          # or: npm --prefix frontend install && npm --prefix frontend run build
```

A checkout holding no build serves the endpoints alone, which reads as a domain answering JSON and drawing
nothing. Every deploy carrying a frontend change needs this again.

The card artwork is fetched rather than kept in the repository, so `make assets` belongs here too where the
run states a pack. A checkout that has fetched nothing draws every card from the glyphs the page carries,
which is also what `artwork.pack: null` states outright.

**3. Install the server dependencies into the interpreter the panel made.** The four packages of the
repository are imported from the checkout, which is what the `PYTHONPATH` above states; `fastapi`, `uvicorn`,
`pydantic` and `pyyaml` are what the panel's own environment needs.

**4. Name the entry file in the panel.** *Application startup file* is the field, `application` is the callable
Passenger looks for, and both are already true of `deploy/main.py`. A panel that insists on the name
`passenger_wsgi.py` is satisfied by a copy or a symlink of it at the application root.

**5. State the port in both places.** `PORT` in the entry file and `service.port` in `config.yaml` name the
same number, and that port stays closed at the firewall: the table is reached through the entry file alone,
and a table reachable directly is one whose forwarding headers anybody may write.

**6. State the rest of `config.yaml` for a public run:**

```yaml
table:
  name: cardtable
  code: K7AQ3J        # pinned, so a restart gathers behind the code already handed out
  seed: 20260806      # pinned, so a restart deals the match the announcement named

service:
  host: 127.0.0.1              # the table answers on the loopback and nowhere else
  port: 8421                   # the same number as PORT in the entry file
  forwarded_allow_ips: 127.0.0.1   # the entry file's word on who a guest is, trusted

admin:
  secret: hunter2     # pinned, so a restart oversees under the token already held
```

Leaving `code`, `seed` and `admin.secret` unstated is right for a local run, where each start deals a match of
its own; on a public table it means a restart hands out a code nobody has and a token nobody holds.

**7. Open the site, then read the log.** `table.log` beside the entry file holds both halves — the entry's own
lines under `passenger:` and everything the table says — and §7 states what to look for in it.

## 5. What the host puts on an answer

A host that finds an answer stating no cache policy settles one of its own, and a month is a common choice.
LiteSpeed does exactly that: `cache-control: public, max-age=2592000` on anything that says nothing for
itself, refusals and 404s included.

What a table answers is how a room stands at the moment it was asked, so a gathering handed back out of a
store is a room that has moved on. The page builds its commands on the revision the view it read carried, and
is told

```
The command was built on revision 1 while the gathering stands at 13
```

with the second number climbing on every refresh, since arriving at a room and leaving it are changes like any
other. `cardserver.keeping.Keeping` closes this by stating `no-store` over every answer that states none of
its own; an answer stating a policy keeps the one it states, so the built interface is still kept by the year
and the page reaching it is still read afresh each time a tab opens.

**Read back what a deployment actually answers, once it stands:**

```bash
curl -sD - -o /dev/null https://cards.jakim.it/offerings     # cache-control: no-store, and no expires
```

**A browser that already read a kept answer keeps it for the full month.** Redeploying changes what the server
says and reaches nothing already stored, so a hard reload — Ctrl-Shift-R — is what clears it, in every browser
that visited before the fix, not only your own.

**The stream is worth its own check**, since a host may hold a body until it is whole or compress it in
flight, and either turns a live table into one that catches up in bursts:

```bash
curl -N -H 'X-Seat-Token: <the token in the address bar after the #>' \
  'https://cards.jakim.it/tables/cardtable/gathering/events?since=0'
```

A frame lands at once and another whenever somebody joins or leaves. Nothing until the connection ends is the
host buffering, and the remedy is in the application root's `.htaccess`: compression off for that path. The
`X-Accel-Buffering: no` the table already sends is nginx's word and LiteSpeed passes it by.

## 6. Restarting, and changing what a table is

The table stands in a session of its own, which carries it through every recycling the host does — and
equally through the restart the panel offers, which restarts workers. So a deploy whose changes are in the
Python reaches the table when the table's own process is replaced:

```bash
fuser -k 8421/tcp        # or: pkill -f cardtable
```

The next request finds nothing answering and gathers a new table, under whatever the files now say. This ends
the game in progress, hands out a fresh join code where `table.code` is unpinned, and is the only way a
changed configuration takes hold.

## 7. Reading the log

`table.log` holds the entry file's own lines and everything the table writes, in the order they happened. Each
logged line carries the process that wrote it, and a table announces itself once as it starts:

```
2026-08-09 17:04:11 INFO [31820] passenger: no table answers on 127.0.0.1:8421, starting one
2026-08-09 17:04:13 INFO [31820] passenger: the table answers after 1.8 seconds
Table 'cardtable' is gathering — join code K 7 A Q 3 J
  https://cards.jakim.it/#table=cardtable&code=K7AQ3J
  dealt from seed 20260806
```

Several `passenger:` PIDs are ordinary — those are the workers, and a run of them all reaching one table is
the arrangement working. **A second announcement, under a second join code, is a host serving two tables**,
and it is the first thing to rule out when a company finds itself in an empty room:

```bash
grep -c "is gathering" table.log      # one per start of the table process
pgrep -af cardtable                   # what is running now
```

## 8. When something is off

| What you see | What it is | What to do |
|---|---|---|
| The join code changes as you refresh | more than one table process | count the announcements in `table.log` (§7); stop every process and let one start |
| `The command was built on revision N while the gathering stands at M` | an answer kept by the host or the browser | confirm `no-store` (§5), then hard-reload every browser that visited |
| Commits arrive late, in bursts | the stream held or compressed in flight | check it with `curl -N` (§5); turn compression off for that path |
| `The table this page is served by is not answering just now` | the child did not start, or did not start in time | `table.log` holds what it said as it tried |
| The endpoints answer and no page draws | `frontend/dist` is absent | `make interface` on the server (§4.2) |
| A wrong join code locks everybody out at once | every guest counted as one caller | state `service.forwarded_allow_ips: 127.0.0.1` (§4.6) |
| A deploy changes nothing at all | the table is the process that was already running | stop it (§6) |
| The panel reports the app as started, and the domain answers 500 | the entry file was imported and raised | the panel's own error log, then `table.log` |

## 9. Hosts other than cPanel

Nothing above is particular to Passenger beyond the name of one field. Any host whose way in is a WSGI
callable — and whose processes are its own to start and stop — asks for the same shape: one persistent table
on the loopback, and an entry that starts it once and streams through to it.

A host that runs a long-lived process of its own accord needs none of it. A systemd unit, a container, or a
shell you can leave `uv run cardtable` running in serves the table directly, with a reverse proxy in front for
the certificate: state `service.forwarded_allow_ips` as the proxy's address, leave the port closed to
everything else, and pass event streams through unbuffered.

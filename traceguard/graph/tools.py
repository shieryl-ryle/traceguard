"""The five read-only graph tools (System Design §2, ADR-003, BR-003).

Each tool returns a `ToolResult`: a JSON-serialisable `output` with display-ready figures
(amounts as decimal strings, whole minutes, ratios rounded down) and the citable evidence IDs
(`transaction_id`, `relationship_id`, `rule_id`). Unknown accounts return empty results.
"""

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from decimal import ROUND_FLOOR, Decimal
from typing import Any, Literal

import networkx as nx

from traceguard.graph.config import CURRENCY, DEFAULT_MAX_DEPTH, FAN_IN, FORWARDING, FanInConfig, ForwardingConfig
from traceguard.graph.loader import Transfer, device_links, is_account, transfers_in, transfers_out

CENT = Decimal("0.01")

Direction = Literal["out", "in"]


@dataclass(frozen=True)
class ToolResult:
    output: dict[str, Any]
    evidence_ids: frozenset[str]


def _money(value: Decimal) -> str:
    return str(value.quantize(CENT))


def _total(transfers: Iterable[Transfer]) -> Decimal:
    return sum((t.amount for t in transfers), Decimal("0"))


def _minutes(seconds: float) -> int:
    return int(seconds // 60)


def _ids(transfers: Iterable[Transfer]) -> list[str]:
    return [t.transaction_id for t in transfers]


def get_account_context(graph: nx.MultiDiGraph, account_id: str) -> ToolResult:
    inbound = transfers_in(graph, account_id)
    outbound = transfers_out(graph, account_id)
    links = device_links(graph, account_id)
    known = is_account(graph, account_id)
    output = {
        "account_id": account_id,
        "known_account": known,
        "label": graph.nodes[account_id]["label"] if known else None,
        "inbound_transaction_ids": sorted(_ids(inbound)),
        "outbound_transaction_ids": sorted(_ids(outbound)),
        "inbound_count": len(inbound),
        "outbound_count": len(outbound),
        "inbound_total": _money(_total(inbound)),
        "outbound_total": _money(_total(outbound)),
        "currency": CURRENCY,
        "linked_device_ids": sorted({device for device, _ in links}),
        "device_relationship_ids": [rel for _, rel in links],
    }
    evidence = {*_ids(inbound), *_ids(outbound), *(rel for _, rel in links)}
    return ToolResult(output, frozenset(evidence))


def _parse_time(value: str | datetime | None) -> datetime | None:
    if value is None or isinstance(value, datetime):
        parsed = value
    else:
        parsed = datetime.fromisoformat(value)
    if parsed is not None and parsed.tzinfo is None:
        raise ValueError("start_time must be timezone-aware")
    return parsed


def trace_funds(
    graph: nx.MultiDiGraph,
    account_id: str,
    direction: Direction = "out",
    max_depth: int = DEFAULT_MAX_DEPTH,
    start_time: str | datetime | None = None,
) -> ToolResult:
    """Follow transfers in time order: outbound hops are non-decreasing, inbound non-increasing."""
    if direction not in ("out", "in"):
        raise ValueError(f"direction must be 'out' or 'in', not {direction!r}")
    if max_depth < 1:
        raise ValueError("max_depth must be at least 1")
    outward = direction == "out"
    bound = _parse_time(start_time)

    def next_hops(account: str, limit: datetime | None) -> list[Transfer]:
        hops = transfers_out(graph, account) if outward else transfers_in(graph, account)
        if limit is None:
            return hops
        return [t for t in hops if (t.timestamp >= limit if outward else t.timestamp <= limit)]

    paths: list[dict[str, Any]] = []

    def walk(account: str, limit: datetime | None, path: list[Transfer]) -> None:
        used = {t.transaction_id for t in path}
        hops = [t for t in next_hops(account, limit) if t.transaction_id not in used]
        if path and not hops:
            paths.append(_path(path, account, "data_boundary"))
            return
        if len(path) == max_depth:
            paths.append(_path(path, account, "max_depth"))
            return
        for hop in hops:
            walk(hop.receiver if outward else hop.sender, hop.timestamp, [*path, hop])

    walk(account_id, bound, [])
    if not outward:
        paths.sort(key=lambda p: p["transaction_ids"][0])
    reasons = sorted({p["stop_reason"] for p in paths})
    output = {
        "account_id": account_id,
        "direction": direction,
        "max_depth": max_depth,
        "start_time": bound.isoformat() if bound else None,
        "path_count": len(paths),
        "paths": paths,
        "truncated": bool(paths),
        "truncation_reasons": reasons,
        "notice": _trace_notice(account_id, paths, outward, bound),
    }
    evidence = {tx for p in paths for tx in p["transaction_ids"]}
    return ToolResult(output, frozenset(evidence))


def _path(path: list[Transfer], end: str, reason: str) -> dict[str, Any]:
    return {
        "transaction_ids": _ids(path),
        "steps": [
            {"transaction_id": t.transaction_id, "from": t.sender, "to": t.receiver,
             "amount": _money(t.amount), "currency": t.currency, "timestamp": t.timestamp.isoformat()}
            for t in path
        ],
        "hop_count": len(path),
        "end_account_id": end,
        "stop_reason": reason,
    }


def _trace_notice(account_id: str, paths: list[dict[str, Any]], outward: bool, bound: datetime | None) -> str:
    if not paths:
        what = f"outgoing transfers from {account_id}" if outward else f"incoming transfers to {account_id}"
        when = f" {'at or after' if outward else 'at or before'} {bound.isoformat()}" if bound else ""
        return f"No {what}{when} in the dataset."
    boundary = sorted({p["end_account_id"] for p in paths if p["stop_reason"] == "data_boundary"})
    depth = sorted({p["end_account_id"] for p in paths if p["stop_reason"] == "max_depth"})
    parts = []
    if boundary:
        nxt = "where funds went after" if outward else "where funds came from before"
        which = "this account" if len(boundary) == 1 else "these accounts"
        parts.append(f"The trace reaches the data boundary at {_join(boundary)}; {nxt} "
                     f"{which} is not in the dataset and is unknown.")
    if depth:
        parts.append(f"The trace stops at the depth limit at {', '.join(depth)}; "
                     "further transfers exist but were not followed.")
    return " ".join(parts)


def find_shared_devices(graph: nx.MultiDiGraph, account_ids: Iterable[str]) -> ToolResult:
    """Devices linked to two or more of the given accounts."""
    accounts = sorted(set(account_ids))
    by_device: dict[str, list[tuple[str, str]]] = {}
    for account in accounts:
        for device, rel in device_links(graph, account):
            by_device.setdefault(device, []).append((account, rel))
    shared = [
        {
            "device_id": device,
            "account_ids": sorted({a for a, _ in links}),
            "relationship_ids": sorted(rel for _, rel in links),
        }
        for device, links in sorted(by_device.items())
        if len({a for a, _ in links}) >= 2
    ]
    output = {"account_ids": accounts, "shared_device_count": len(shared), "shared_devices": shared}
    evidence = {rel for item in shared for rel in item["relationship_ids"]}
    return ToolResult(output, frozenset(evidence))


def detect_fan_in(graph: nx.MultiDiGraph, account_id: str, config: FanInConfig = FAN_IN) -> ToolResult:
    """Best window (most distinct senders, earliest start) of inbound transfers within the window length."""
    inbound = transfers_in(graph, account_id)
    best: list[Transfer] = []
    best_senders = 0
    for i, start in enumerate(inbound):
        window = [t for t in inbound[i:]
                  if (t.timestamp - start.timestamp).total_seconds() <= config.window_seconds]
        senders = len({t.sender for t in window})
        if senders > best_senders:
            best, best_senders = window, senders
    matched = best_senders >= config.min_senders
    sender_ids = sorted({t.sender for t in best})
    on_shared, shared_rels = _senders_sharing_a_device(graph, sender_ids)
    not_shared = [s for s in sender_ids if s not in on_shared]
    contrasts: list[dict[str, Any]] = []
    if matched and on_shared and not_shared:
        not_shared_txs = [t.transaction_id for t in best if t.sender in not_shared]
        contrasts.append({
            "text": f"{_join(not_shared)} {'has' if len(not_shared) == 1 else 'have'} no recorded device link "
                    f"shared with another sender in this window.",
            "evidence_ids": [*shared_rels, *not_shared_txs],
        })
    output: dict[str, Any] = {
        "rule_id": config.rule_id,
        "matched": matched,
        "receiver_account_id": account_id,
        "sender_count": best_senders,
        "sender_account_ids": sender_ids,
        "senders_on_shared_device": on_shared,
        "senders_not_on_shared_device": not_shared,
        "shared_device_relationship_ids": shared_rels,
        "transfer_count": len(best),
        "transaction_ids": _ids(best),
        "window_start": best[0].timestamp.isoformat() if best else None,
        "window_end": best[-1].timestamp.isoformat() if best else None,
        "window_span_minutes": (
            _minutes((best[-1].timestamp - best[0].timestamp).total_seconds()) if best else None
        ),
        "aggregate_amount": _money(_total(best)),
        "currency": CURRENCY,
        "config": config.as_output(),
        "contrasts": contrasts,
    }
    minutes, threshold = config.window_seconds // 60, config.min_senders
    if not best:
        output["explanation"] = f"{account_id} has no inbound transfers in the dataset."
    elif matched:
        output["explanation"] = (
            f"{best_senders} distinct senders paid {account_id} within a {minutes}-minute window "
            f"(threshold: {threshold} senders)."
        )
    else:
        output["explanation"] = (
            f"At most {best_senders} distinct sender(s) paid {account_id} within any {minutes}-minute "
            f"window (threshold: {threshold} senders)."
        )
    return ToolResult(output, frozenset({config.rule_id, *_ids(best), *shared_rels}))


def _senders_sharing_a_device(graph: nx.MultiDiGraph, senders: list[str]) -> tuple[list[str], list[str]]:
    """Senders linked to a device that another sender in the same list also uses, plus those links."""
    by_device: dict[str, list[tuple[str, str]]] = {}
    for sender in senders:
        for device, rel in device_links(graph, sender):
            by_device.setdefault(device, []).append((sender, rel))
    shared = [links for links in by_device.values() if len({a for a, _ in links}) >= 2]
    accounts = sorted({a for links in shared for a, _ in links})
    rels = sorted(rel for links in shared for _, rel in links)
    return accounts, rels


def _join(items: list[str]) -> str:
    return items[0] if len(items) == 1 else f"{', '.join(items[:-1])} and {items[-1]}"


def detect_rapid_forwarding(
    graph: nx.MultiDiGraph, account_id: str, config: ForwardingConfig = FORWARDING
) -> ToolResult:
    """Each outbound transfer vs the inbound transfers in the window before it (ADR-003 §2)."""
    inbound = transfers_in(graph, account_id)
    evaluated: list[dict[str, Any]] = []
    evidence: set[str] = {config.rule_id}
    for out in transfers_out(graph, account_id):
        window = [t for t in inbound
                  if 0 <= (out.timestamp - t.timestamp).total_seconds() <= config.window_seconds]
        total = _total(window)
        matched = bool(window) and out.amount >= config.min_forward_ratio * total
        ratio = out.amount / total if total > 0 else None
        difference = total - out.amount
        evaluated.append({
            "outbound_transaction_id": out.transaction_id,
            "outbound_amount": _money(out.amount),
            "inbound_transaction_ids": _ids(window),
            "inbound_total": _money(total),
            "forwarded_ratio": str(ratio.quantize(CENT, rounding=ROUND_FLOOR)) if ratio is not None else None,
            "minutes_after_last_inbound": (
                _minutes((out.timestamp - window[-1].timestamp).total_seconds()) if window else None
            ),
            "inbound_minus_outbound": _money(difference) if window and difference > 0 else None,
            "matched": matched,
        })
        evidence |= {out.transaction_id, *_ids(window)}
    matches = [e for e in evaluated if e["matched"]]
    minutes = config.window_seconds // 60
    contrasts = [
        {
            "text": f"{m['outbound_transaction_id']} ({m['outbound_amount']} {CURRENCY}) is "
                    f"{m['inbound_minus_outbound']} {CURRENCY} less than the {m['inbound_total']} {CURRENCY} "
                    f"total of inbound transfers in the {minutes} minutes before it.",
            "evidence_ids": [m["outbound_transaction_id"], *m["inbound_transaction_ids"]],
        }
        for m in matches
        if m["inbound_minus_outbound"] is not None
    ]
    output: dict[str, Any] = {
        "rule_id": config.rule_id,
        "matched": bool(matches),
        "account_id": account_id,
        "matched_count": len(matches),
        "evaluated_count": len(evaluated),
        "evaluated": evaluated,
        "currency": CURRENCY,
        "config": config.as_output(),
        "explanation": _forwarding_explanation(account_id, matches, evaluated, config),
        "contrasts": contrasts,
    }
    return ToolResult(output, frozenset(evidence))


def _forwarding_explanation(
    account_id: str, matches: list[dict[str, Any]], evaluated: list[dict[str, Any]], config: ForwardingConfig
) -> str:
    minutes = config.window_seconds // 60
    rule = f"(threshold: ratio {config.min_forward_ratio} of inbound funds within {minutes} minutes)"
    if not evaluated:
        return f"{account_id} has no outbound transfers in the dataset."
    if not matches:
        return f"No outbound transfer from {account_id} met the forwarding rule {rule}."
    sentences = [
        f"{m['outbound_transaction_id']} sent {m['outbound_amount']} {CURRENCY}, a ratio of "
        f"{m['forwarded_ratio']} of the {m['inbound_total']} {CURRENCY} received in the preceding "
        f"{minutes} minutes, {m['minutes_after_last_inbound']} minutes after the last inbound transfer."
        for m in matches
    ]
    return f"{account_id}: " + " ".join(sentences) + f" {rule[1:-1].capitalize()}."

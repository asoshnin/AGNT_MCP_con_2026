"""Cloudflare GraphQL Analytics Integration for AGNTCon Hub.

Provides cached zone-level edge request analytics, pageviews, bandwidth,
and cache hit metrics via Cloudflare's GraphQL API.
"""

import datetime
import json
import os
import sys
import time
import urllib.request

# 5-minute in-memory cache to prevent hitting Cloudflare rate limits
_CF_CACHE = {
    "timestamp": 0.0,
    "data": None
}
CACHE_TTL_SECONDS = 300.0


def fetch_cloudflare_edge_analytics(days: int = 7) -> dict:
    """Fetch 7-day edge analytics from Cloudflare GraphQL API with in-memory caching."""
    now = time.time()
    if _CF_CACHE["data"] and (now - _CF_CACHE["timestamp"]) < CACHE_TTL_SECONDS:
        return _CF_CACHE["data"]

    token = os.environ.get("CLOUDFLARE_ANALYTICS_TOKEN")
    zone_id = os.environ.get("CLOUDFLARE_ZONE_ID")

    if not token or not zone_id:
        return {
            "available": False,
            "reason": "CLOUDFLARE_ANALYTICS_TOKEN or CLOUDFLARE_ZONE_ID not configured."
        }

    today = datetime.date.today()
    since = (today - datetime.timedelta(days=days)).isoformat()
    until = today.isoformat()

    query = """query GetZoneAnalytics($zoneTag: string, $since: string, $until: string) {
      viewer {
        zones(filter: { zoneTag: $zoneTag }) {
          httpRequests1dGroups(
            limit: 7
            filter: { date_geq: $since, date_leq: $until }
          ) {
            dimensions { date }
            sum {
              requests
              pageViews
              bytes
              cachedRequests
              cachedBytes
              threats
            }
            uniq { uniques }
          }
        }
      }
    }"""

    req = urllib.request.Request(
        "https://api.cloudflare.com/client/v4/graphql",
        data=json.dumps({
            "query": query,
            "variables": {
                "zoneTag": zone_id,
                "since": since,
                "until": until
            }
        }).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "agntcon-hub/1.1.0"
        }
    )

    try:
        with urllib.request.urlopen(req, timeout=8.0) as res:
            resp_data = json.loads(res.read().decode("utf-8"))
            errors = resp_data.get("errors")
            if errors:
                return {
                    "available": False,
                    "reason": f"Cloudflare API error: {errors[0].get('message', 'Unknown') if errors else 'Unknown'}"
                }

            zones = resp_data.get("data", {}).get("viewer", {}).get("zones", [])
            if not zones:
                return {
                    "available": False,
                    "reason": "No zone data returned for the given Zone ID."
                }

            groups = zones[0].get("httpRequests1dGroups", [])
            total_reqs = sum(g.get("sum", {}).get("requests", 0) for g in groups)
            total_pvs = sum(g.get("sum", {}).get("pageViews", 0) for g in groups)
            total_bytes = sum(g.get("sum", {}).get("bytes", 0) for g in groups)
            cached_reqs = sum(g.get("sum", {}).get("cachedRequests", 0) for g in groups)
            cached_bytes = sum(g.get("sum", {}).get("cachedBytes", 0) for g in groups)
            threats = sum(g.get("sum", {}).get("threats", 0) for g in groups)
            cache_ratio = round((cached_reqs / total_reqs * 100), 1) if total_reqs else 0.0

            daily_breakdown = []
            for g in groups:
                d_sum = g.get("sum", {})
                d_date = g.get("dimensions", {}).get("date", "")
                daily_breakdown.append({
                    "date": d_date,
                    "requests": d_sum.get("requests", 0),
                    "pageviews": d_sum.get("pageViews", 0),
                    "bytes": d_sum.get("bytes", 0)
                })

            result = {
                "available": True,
                "days": days,
                "requests_total": total_reqs,
                "pageviews_total": total_pvs,
                "bytes_total": total_bytes,
                "bytes_formatted": f"{total_bytes / 1024 / 1024:.1f} MB",
                "cached_requests": cached_reqs,
                "cached_bytes": cached_bytes,
                "cache_ratio": cache_ratio,
                "threats_blocked": threats,
                "daily": daily_breakdown,
                "cached_at": time.strftime("%Y-%m-%d %H:%M:%S UTC")
            }

            _CF_CACHE["timestamp"] = now
            _CF_CACHE["data"] = result
            return result
    except Exception as e:
        sys.stderr.write(f"[WARN] Cloudflare analytics fetch failed: {e}\n")
        return {
            "available": False,
            "reason": str(e)
        }

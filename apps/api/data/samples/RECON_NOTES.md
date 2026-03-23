# Reconnaissance Notes — Listing Pipeline

## Flatfox

### API Endpoint
```
GET https://flatfox.ch/api/v1/public-listing/
```
No auth required. Standard DRF paginated envelope.

### Query Parameters
| Param | Notes |
|-------|-------|
| `limit` | Results per page (max ~100) |
| `offset` | Pagination offset |
| `west/east/south/north` | Bbox — DOES NOT FILTER reliably; returns all CH listings regardless |
| `object_category` | `APARTMENT`, `PARK`, `INDUSTRY`, `SHARED` |
| `offer_type` | `RENT`, `BUY` |
| `zipcode` | Seems to also be ignored |

**Key finding**: Bbox and zipcode filters do not appear to work on the public API.
**Workaround**: Fetch all listings (`count ≈ 33k`), filter client-side by zipcode 8000–8999 for Kanton Zürich.

### Response Structure
```json
{
  "count": 33698,
  "next": "https://flatfox.ch/api/v1/public-listing/?limit=96&offset=96",
  "previous": null,
  "results": [{ ... }]
}
```

### Field Mapping
| Flatfox field | DB column | Notes |
|---------------|-----------|-------|
| `pk` | `source_id` | unique integer |
| `slug` | `source_url` | prepend `https://flatfox.ch/en/flat/{slug}/{pk}/` |
| `status` | `status` | `"act"` = active |
| `offer_type` | `offer_type` | `"RENT"` |
| `object_category` | `object_type` | `"APARTMENT"`, `"SHARED"`, `"PARK"` |
| `rent_net` | `rent_net` | CHF/month, nullable |
| `rent_charges` | `rent_charges` | CHF/month, nullable |
| `rent_gross` | `rent_gross` | CHF/month, nullable |
| `number_of_rooms` | `rooms` | float, e.g. 3.5 |
| `surface_living` | `area_m2` | m², nullable |
| `floor` | — | not in DB schema currently |
| `street` | `street` | street name, may include house number |
| `zipcode` | `plz` | integer |
| `city` | `city` | string |
| `public_address` | `address_raw` | full formatted address |
| `latitude` | `lat` | float |
| `longitude` | `lng` | float |
| `published` | `first_seen` | ISO datetime |
| `agency.name` | — | advertiser info, not stored |
| `images` | — | list of int IDs, not stored |

**House number**: Flatfox puts it in the `street` field (e.g. `"Rämistrasse 12"`) — need to split on parse.

---

## Homegate

### Bot Protection
DataDome CAPTCHA. Standard urllib and curl return 403. Standard Playwright returns CAPTCHA page.
**Mitigation**: Need `rebrowser-playwright` (patched Playwright removing automation fingerprints) or a headless browser with full stealth mode.

### Data Source
`window.__INITIAL_STATE__` embedded in HTML of every search results page.

### URL Pattern
```
https://www.homegate.ch/rent/real-estate/city-zurich/matching-list?ep={page}
```
Pagination: `ep` parameter (1-based).

### JSON Path to Listings
```
state
  .resultList
    .search
      .fullSearch
        .result
          .listings[]        ← array
          .totalCount         ← integer
          .pageCount          ← integer
          .start              ← offset
```

### Field Mapping
| Homegate path | DB column | Notes |
|---------------|-----------|-------|
| `id` | `source_id` | string, e.g. `"4002154320"` |
| `listing.address.street` | `street` + `house_number` | split on parse |
| `listing.address.postalCode` | `plz` | string → int |
| `listing.address.locality` | `city` | string |
| `listing.address.geoCoordinates.latitude` | `lat` | may be null on search page |
| `listing.address.geoCoordinates.longitude` | `lng` | may be null on search page |
| `listing.characteristics.numberOfRooms` | `rooms` | float |
| `listing.characteristics.livingSpace` | `area_m2` | m² |
| `listing.prices.rent.net` | `rent_net` | CHF |
| `listing.prices.rent.gross` | `rent_gross` | CHF |
| `listing.prices.rent.extra` | `rent_charges` | CHF (Nebenkosten) |
| `listing.offerType` | `offer_type` | `"RENT"` |
| `meta.createdAt` | `first_seen` | ISO datetime |
| `listing.localization.de.title` | — | not stored |

**Geo**: `geoCoordinates` may be absent at search-result level; may need detail page for precise coords. Use address geocoding as fallback.

### Implementation Note
For Phase D, use Playwright with stealth plugin (`playwright-stealth` or `rebrowser-playwright`).
Rate limit: 1 request per 2.5s minimum.

---

## Samples Saved
- `flatfox_search.json` — live API response, 3 results
- `homegate_search.json` — synthetic sample from reverse-engineered structure (DataDome blocks live fetch)
- `homegate_search.html` — DataDome challenge page (not useful)

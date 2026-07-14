/** Product requirement presets — real-world feature specifications. */

import type { InputSourceType } from "@/modules/requirement-analysis/types";

export interface RequirementPreset {
  id: string;
  title: string;
  description: string;
  sourceType: InputSourceType;
  content: string;
}

export const REQUIREMENT_PRESETS: RequirementPreset[] = [
  {
    id: "sso-enterprise",
    title: "Enterprise SSO (SAML/OIDC)",
    description: "Multi-tenant SSO with Just-In-Time provisioning and SCIM",
    sourceType: "markdown",
    content: `# Enterprise Single Sign-On

## Overview
Enterprise customers require SAML 2.0 and OIDC-based SSO to let their
employees log in using their corporate identity provider (Okta, Azure AD,
OneLogin, Google Workspace).

## Authentication Flow

### SP-Initiated Login
1. User clicks "Log in with SSO" and enters their company domain
2. Backend resolves the domain to a tenant and looks up the IdP metadata
3. User is redirected to the IdP login page with a signed SAML request
4. IdP authenticates the user and POSTs a SAML assertion back
5. Backend validates the assertion (signature, audience, expiry, NotOnOrAfter)
6. If the user does not exist locally, JIT-provision an account with roles
   mapped from SAML attributes (eduPerson, groups, or custom claims)
7. A session JWT is issued and the user is redirected to the app

### IdP-Initiated Login
- Support IdP-initiated POST bindings with a RelayState that routes the
  user to the correct post-login page

## User Provisioning (SCIM 2.0)

### Directory Sync
- Expose /scim/v2/Users and /scim/v2/Groups endpoints
- Support Create, Update, Patch (partial update), and Deactivate
- IdP pushes changes via webhook; polling fallback every 6 hours
- Map SCIM "active: false" → soft-deactivate (revoke sessions, keep data)

### Just-In-Time Provisioning
- On first SSO login, create user profile from SAML/OIDC claims
- Map IdP groups to app roles via a configurable role-mapping table
- If no role matches, assign a default "Viewer" role

## Role Mapping
- Tenant admins can configure group-to-role mappings in Settings > SSO
- Supported match strategies: exact group name, regex prefix, nested groups
- Changes take effect on next login (not retroactive)

## Security Requirements

| Requirement | Must |
|---|---|
| Signing | Assertions must be signed with RSA-SHA256 minimum |
| Encryption | Support encrypted assertions for sensitive tenants |
| Session expiry | Max 8 hours, force re-auth via IdP |
| Certificate rotation | Support metadata URL refresh; manual upload fallback |
| Audit | Log every SSO login attempt (success + failure with reason) |
| Rate limiting | Max 10 IdP redirects per email per 5 minutes |
| Domain collision | Error if two tenants claim the same domain |
`,
  },
  {
    id: "payment-payouts",
    title: "Marketplace Payout System",
    description: "Stripe Connect-style escrow, disputes, multi-currency settlement",
    sourceType: "plain_text",
    content: `Marketplace Payout Processing System

BACKGROUND
Our multi-vendor marketplace processes $12M+ monthly across 3 currencies
(USD, EUR, GBP). Sellers are paid out on a weekly cadence, but manual
payout management is error-prone and doesn't scale.

GOALS
- Automated weekly payouts to sellers' bank accounts or PayPal
- Escrow hold period (7 days after delivery) before funds are released
- Dispute handling: buyer opens dispute → funds frozen → admin
  resolution → release or reversal
- Multi-currency support: auto-convert to seller's settlement currency
- 1099-NEC tax form generation for US sellers reaching $600+ annually

FUNCTIONAL REQUIREMENTS

1. Payout Scheduling
   1.1 System runs payout batch every Monday 03:00 UTC
   1.2 Payout includes all completed orders where:
       - Delivery confirmed by buyer OR 7 days elapsed since delivery
       - No active dispute on the order
       - Seller has provided valid payout details (bank/PayPal)
   1.3 Failed payouts (invalid bank details, closed account) are
       retried twice with 24h delay, then suspended with admin alert
   1.4 Suspended payouts are held in a "Failed Payouts" queue for
       manual review — no automatic retry after 2 failures

2. Escrow & Disputes
   2.1 When a buyer places an order, the full amount moves to "Pending
       Escrow" status instantly (authorization hold on buyer's card)
   2.2 Funds are captured when seller marks as shipped
   2.3 Escrow release triggers 7 calendar days after delivery
       confirmation
   2.4 Buyers can open a dispute up to 14 days after delivery
   2.5 During dispute: funds remain in escrow, seller is notified,
       both parties submit evidence within 72 hours
   2.6 Admin resolves dispute: release to seller OR reverse to buyer
   2.7 Reversed orders: buyer gets full refund minus 5% processing fee

3. Multi-Currency
   3.1 Customers pay in their local currency (auto-detected from IP
       or browser locale)
   3.2 Seller sets settlement currency in profile settings
   3.3 Conversion uses the mid-market rate at time of capture + 1.5%
       FX markup
   3.4 FX rates are fetched from OpenExchangeRates every 6 hours
   3.5 Payout batch converts all amounts to seller's settlement currency

4. Tax Compliance
   4.1 Track YTD payout totals per US seller
   4.2 Auto-generate 1099-NEC for sellers with >=$600 annual payout
   4.3 Forms are generated January 15th each year via IRS-approved API
   4.4 Seller can download PDF copy from Settings > Tax Documents
   4.5 Filing to IRS happens by January 31st (with 5-day grace period)

NON-FUNCTIONAL REQUIREMENTS
- Payout batch must complete within 30 minutes for up to 50k sellers
- Escrow balance must be accurate to the cent at all times (audit trail)
- Dispute resolution SLA: 80% within 72 hours, 100% within 5 business days
- 99.99% availability during payout window (Mon 03:00-04:00 UTC)
- PCI-DSS compliance for stored payment method references (Stripe tok ns)
`,
  },
  {
    id: "collaborative-editing",
    title: "Real-time Document Editing",
    description: "CRDT-based collaborative editing with presence and comments",
    sourceType: "markdown",
    content: `# Real-Time Collaborative Document Editor

## Overview
Users can co-edit documents in real time with multiple cursors, presence
indicators, threaded comments, and version history with branching/merging.

## Architecture

### Sync Protocol
- **CRDT-based** (Yrs) — no central conflict resolution server needed
- WebSocket connection per document session
- Delta updates sent as binary-encoded Yrs updates
- Full document state snapshot every 50 updates for fast reconnection
- Initial sync: send compressed snapshot + log of missed updates since
  the client's last known version

### Presence
- Cursor positions: { userId, docId, selectionStart, selectionEnd,
  line, column, timestamp }
- Broadcast to all other collaborators in the same document session
- Presence heartbeat every 15 seconds
- Idle detection: mark user as "away" after 2 minutes of no input
- Color assigned per user session (from a 12-color palette)

## Feature Requirements

### Editing
- Rich text formatting: bold, italic, underline, strikethrough, heading
  levels (h1-h6), bullet and numbered lists, blockquote, code block
- Mentions: type @ to search and mention other workspace members
- Slash commands: /table, /image, /divider, /callout
- Markdown shortcuts: # h1, **bold**, - bullet, > quote, \`code\`
- Auto-save: every 5 seconds of inactivity, or immediately on close

### Comments & Threads
- Select text → "Add comment" creates a thread anchored to that selection
- Threaded replies with @mentions and rich text
- Resolve thread (kept as archived in document history)
- Notifications: email + in-app for @mentions and thread replies

### Version History
- Manual snapshots: user can name and save a version
- Auto-snapshots: created every 30 minutes of editing or 200 changes
- Browse history as a timeline with diff view against current
- Branch: create a draft branch from any historical version
- Merge: merge a draft branch back into the main document
- Conflicts on merge are surfaced as a side-by-side resolution UI

## Performance & Scale
- 500+ concurrent editors on a single document
- Initial sync for a 100 KB document under 500ms on typical connections
- Delta updates under 50ms end-to-end p99
- Offline support: queue local edits, sync on reconnection
`,
  },
  {
    id: "video-platform",
    title: "Video Streaming Platform",
    description: "Upload, transcode, DRM, CDN delivery, usage metering",
    sourceType: "acceptance_criteria",
    content: `Feature: Video Upload and Transcoding

  Scenario: User uploads a video file
    Given the user is authenticated with a "Creator" role
    When they upload a video file (MP4, 500MB, 1920x1080, H.264)
    Then the upload is received via resumable chunked upload (5MB chunks)
    And the system returns an upload_id immediately
    And an async transcoding job is queued with priority "standard"

  Scenario: Transcoding pipeline completes successfully
    Given a video file has been uploaded (upload_id: "upl_abc123")
    When the transcoding pipeline finishes
    Then the following renditions are generated:
      | Profile  | Resolution | Bitrate   | Codec   |
      | 1080p    | 1920x1080  | 8 Mbps    | H.264   |
      | 720p     | 1280x720   | 5 Mbps    | H.264   |
      | 480p     | 854x480    | 2.5 Mbps  | H.264   |
      | 360p     | 640x360    | 1 Mbps    | H.264   |
    And an HLS master playlist is generated with all renditions
    And a DASH manifest is generated with matching renditions
    And a thumbnail sprite sheet is created (100 thumbnails, 10x10 grid)
    And a 30-second preview clip is generated
    And the video status is updated to "ready"

  Scenario: DRM enforcement on premium content
    Given a video is marked as "premium" content
    When a user without an active subscription attempts to play it
    Then the playback request returns HTTP 403
    And the response body contains: {"error": "subscription_required"}
    And an analytics event "playback_blocked" is logged
    When a user with an active "Pro" subscription plays the video
    Then a playback token is issued (JWT, expires in 1 hour)
    And the HLS manifest is served with AES-128 encryption
    And the CDN edge validates the token before serving segments

  Scenario: CDN delivery and caching
    Given a video is in "ready" status
    When a CDN edge receives a manifest request with a valid token
    Then the manifest is served with Cache-Control: public, max-age=3600
    And video segments are served with Cache-Control: public, max-age=86400
    And segments are cached at the edge for subsequent requests
    And the origin server sees <1% of segment requests (99% cache hit)

Feature: Usage Metering and Billing

  Scenario: Usage is tracked for billing
    Given a viewer watches 15 minutes of a 30-minute video
    Then the billing system records 15 minutes of "streaming" usage
    And the usage is attributed to the viewer's account for the current
    billing cycle
    And the vendor (content creator) receives a view credited to their
    analytics

  Scenario: Free tier quota enforcement
    Given a user is on the "Free" plan (limit: 60 minutes/day)
    When the user has watched 60 minutes of video
    Then subsequent playback requests return HTTP 402 (Payment Required)
    And the player shows a "Upgrade to continue watching" overlay
    And the quota resets at midnight UTC
`,
  },
  {
    id: "audit-log",
    title: "Immutable Audit Log System",
    description: "Tamper-proof event stream with compliance exports and alerting",
    sourceType: "plain_text",
    content: `Immutable Audit Log System

PURPOSE
A tamper-evident, queryable audit trail for all user and system actions
across the platform. Required for SOC2 Type II, HIPAA, and GDPR compliance.

DATA MODEL

Every audit event has the following structure:

{
  "id": "evt_2a3f8c91",           // ULID (time-sortable unique ID)
  "actor": {
    "type": "user|system|api_key",
    "id": "usr_7f3a2b1c",
    "email": "admin@example.com"
  },
  "target": {
    "type": "organization|project|document|settings",
    "id": "org_9d2e1f4a",
    "name": "Acme Corp"
  },
  "action": "project.settings.updated",
  "metadata": {
    "changed_fields": ["retention_days", "encryption_enabled"],
    "old_values": {"retention_days": 30},
    "new_values": {"retention_days": 90}
  },
  "context": {
    "ip_address": "203.0.113.42",
    "user_agent": "Mozilla/5.0 ...",
    "session_id": "sess_8b4c2d1e",
    "request_id": "req_5f6a7b8c"
  },
  "timestamp": "2026-07-14T10:30:00.000Z",
  "hash": "sha256://..."           // Chained hash of this event
}

TAMPER EVIDENCE

Events are stored in a hash chain (similar to a blockchain ledger):
- Each event stores the SHA-256 hash of the previous event
- A consistency proof is generated daily and stored off-chain (S3)
- Auditors can verify: recompute hashes from genesis to latest, compare
  against the daily consistency proofs stored in S3 with write-once lock

Ingestion: 50,000+ events per second via Kafka topic
Storage: TimescaleDB (hypertable partitioned by day), 90-day hot retention
  then moved to S3 Glacier (cold storage, 7-year retention)

QUERY CAPABILITIES

1. Search by actor, target, action type, or time range
2. Full-text search on metadata.changed_fields and metadata.new_values
3. Export to CSV or JSON (max 100k rows per export, paginated)
4. Compliance export: GDPR data subject request → export all events
   where actor.id matches the user within 30 days
5. Real-time dashboards: top actions today, unusual activity spikes

ALERT RULES

Users can create alert rules:
- Trigger: action matches pattern AND/OR actor type matches
- Threshold: X events in Y minutes
- Action: email, Slack webhook, PagerDuty, or webhook
- Examples:
  > 10 failed login attempts from same IP in 5 minutes → Slack alert
  > "organization.deleted" action by any user → PagerDuty critical
  > API key deactivated → email to workspace admins

RETENTION & COMPLIANCE

- Hot (TimescaleDB): 90 days
- Cold (S3 Glacier): 7 years
- Deletion is NEVER allowed on hot storage (append-only)
- Cold storage exports are write-once with legal hold support
- GDPR deletion: mark actor_id as "deleted_user_XXX" but preserve event
- SOC2 audit exports include the full hash chain for verification
`,
  },
  {
    id: "feature-flags",
    title: "Feature Flag System",
    description: "Targeted rollouts, A/B experiments, kill switches, SDK delivery",
    sourceType: "markdown",
    content: `# Feature Flag & Experimentation Platform

## Overview
A self-service feature flag system that enables engineering and product
teams to gradually roll out features, run A/B experiments, and instantly
kill problematic features — all without redeploying.

## Flag Types

### Release Toggle
- **Boolean flag** — on/off per environment (dev, staging, prod)
- Supports gradual rollout by percentage (1-100% in 1% increments)
- Kill switch: global override to disable instantly regardless of rules

### Targeting Rule
- User-level targeting based on attributes:
  - `user.id`, `user.email`, `user.plan` (free/pro/enterprise)
  - `user.country`, `user.region`, `user.custom_attributes.*`
- Segment-based targeting (match any/all):
  - `country IN (US, CA, GB)` AND `plan == enterprise`
  - `email CONTAINS @acme.com`
- Percentage rollout within a segment:
  - e.g., roll out to 25% of enterprise users in US/CA

### A/B Test (Experiment)
- Split traffic into variants (control vs treatment)
- Minimum 1,000 users per variant for statistical significance
- Auto-stop if result reaches significance (p < 0.05) after 7 days
- Metrics: any custom event tracked by the SDK

## Flag Evaluation Pipeline

```
Request: { user, context }
  → Environment defaults (dev/test/staging/prod)
  → Kill switch check → return override value if active
  → Targeting rules (first match wins, ordered by priority)
  → Percentage rollout (consistent bucketing via user_id hash mod 100)
  → Fallback to default value
```

## SDK Delivery

### Server-side SDKs
- Python, Node.js, Go, Java
- Poll for flag changes every 30 seconds (configurable)
- Local cache with in-memory store; fallback to default on network error
- File-based bootstrap: load a flags.json snapshot on startup

### Client-side SDKs
- JavaScript (browser via CDN script tag), React hook, React Native
- Real-time updates via SSE (Server-Sent Events) — no WebSocket needed
- No API keys exposed to client (flags are scoped to environment + public
  role)
- Flag payloads can include JSON configuration (e.g., new checkout flow
  component URL)

### Webhook Integration
- Flag change events: created, updated, toggled, deleted
- Payload: { event, flag_id, flag_name, new_state, changed_by, timestamp }
- Destinations: Slack, Discord, custom webhook URL

## Evaluation Performance
- p50 evaluation latency: <5ms (server-side SDKs)
- p99 evaluation latency: <20ms
- SSE delivery latency: <200ms for UI updates
- Flag count: supports 10,000+ flags per environment
- Concurrent evaluations: 100,000+ per second per SDK instance
`,
  },
];

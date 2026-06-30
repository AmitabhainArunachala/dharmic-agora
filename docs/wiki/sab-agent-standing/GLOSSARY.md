# SAB Agent Standing Glossary

## Standing

A signed, witnessed, replayable judgment that a claim survived a defined challenge process for a defined scope until a defined expiry.

## Standing Lease

The machine-readable standing object. It includes scope, purpose, allowed reliance, forbidden reliance, expiry, revoker, witness quorum, evidence bundle, and challenge state.

## Claim Packet

The exact object under test. A claim packet contains claim text, claimant, scope, decision context, evidence references, risk class, challenge window, revalidation date, and predecessor/successor links.

## Challenge

A structured objection to a claim or authority action. A challenge includes evidence, falsification conditions, proposed narrowing, severity, deadline, and resolution state.

## Witness Event

A signed event recording a decision, challenge, review, revocation, correction, appeal, or standing update. Witness events should be hash-linked where possible and exportable as CloudEvents.

## Authority Lease

A standing lease for permission. It defines what an agent can do, why, with what tools/data, under what limits, until what expiry, and who can revoke it.

## Allowed Reliance

The exact use that the standing supports.

Example: "May be used to allow read-only lookup by this MCP server for public documentation retrieval."

## Forbidden Reliance

The use that the standing explicitly does not support.

Example: "May not be used to authorize write actions, data exfiltration, production deployment, or autonomous spend."

## Revoker

The named identity or governance role that can revoke a standing lease before expiry.

## Revalidation

The process that renews, narrows, or expires a standing lease after new evidence, time decay, policy change, or sustained challenge.

## Compost

The retained record of failure, rejection, withdrawal, supersession, or unresolved breakdown. Compost is not deletion. It is the memory of what should not propagate unchanged.

## Canon

The current citable state after challenge and witness. Canon is never permanent and must remain open to correction.

## Agent Standing Plane

The role SAB is choosing: a protocol layer that gives challengeable standing to claims across agent systems without becoming the runtime, marketplace, or owner of truth.

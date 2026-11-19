# Forge integration

Canonical Cloud forge/ contains a separate native reviewed FWD validation queue with SQLite transactional request/receipt state and the installed Core FWD package. Four actual jobs (raw/refined Montréal/Aetheria) reached validated; separate-process replay retained executions=1. Concurrency, corruption, conflicting job identity, review omission and unrelated DB preservation are covered. Release and ASan/UBSan pass.

--reviewed is a local operator attestation, not tenant authentication or permission to publish. Forge has no MutSea or WorldLine writer and does not duplicate Cloud orchestration or SpatialDB storage. The initial connector calls this separately from the existing SpatialDB publisher; it is not an automatic distributed job/publication transaction. HTTP APIs, durable external delivery, cloud tenancy and Genesis creation orchestration remain gates.

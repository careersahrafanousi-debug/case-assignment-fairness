# Privacy and Synthetic Data Statement

> This project uses fully synthetic data created for educational and portfolio
> purposes. It does not use employer data, patient information, protected health
> information, or confidential business information.

## What the data is

Every row in this repository was produced by `src/generate_data.py` using Python's
standard pseudo-random generator with a fixed seed of 8821. Nothing was copied,
exported, anonymised, masked, or derived from any real system.

**ClearPath Case Services does not exist.** The organisation, its five teams, its
35 analyst identifiers, its six case types and every case record are invented for
this exercise.

## What is deliberately absent

The dataset contains no field that could identify a person, because none was
generated:

- No names, addresses, dates of birth, phone numbers or email addresses.
- No member, patient, subscriber or claim identifiers.
- No diagnosis, procedure, clinical or medication data.
- No dollar amounts, contract terms or client identities.
- No real employer, health plan, vendor or payer names.

Analyst identifiers are sequential codes (`AN-001` to `AN-035`) mapped only to a
team and a tenure band. They correspond to no real person.

## Why anonymised real data was not used, even conceptually

Case-management records in healthcare administration are routinely PHI-adjacent
even when direct identifiers are stripped, because the combination of case type,
dates, and a small population can be re-identifying on its own. A case-level
extract from a real operation would also carry the employer's confidential
information about its own service performance, which is a separate problem from
HIPAA and no less serious. Generating data was not the convenient option; it was
the only defensible one for something published publicly.

## Analyst-level reporting

This project measures how work is distributed among 35 analysts, which in a real
operation would be individually identifying performance data. Two deliberate
choices carry over from that concern:

1. Every published performance measure — SLA compliance, assignment accuracy,
   reopen rate, resolution time — is reported by **team or tenure band only**,
   never by individual. See query 12 and the dashboard specification.
2. The one place an analyst identifier appears in output is the open-case priority
   queue, which is an operational work list rather than a performance measure. A
   team lead cannot reassign an overdue case without knowing who holds it. The
   distinction is recorded in [docs/11_uat_test_cases.md](11_uat_test_cases.md)
   under T-19 rather than left implicit.

The same practice is worth carrying into real work: aggregate before you publish,
and be able to explain why any individual-level column survived.

## HIPAA note

HIPAA's Privacy Rule protects individually identifiable health information held by
covered entities and business associates. A third-party administrator handling case
work on behalf of health plans would be a business associate, and its case records
would be protected. That is precisely the scenario this project models, which is
why no real data of that kind is used anywhere in it.

Two things worth stating plainly, because they are commonly misunderstood:

- **Removing names is not de-identification.** Dates of service, a small provider
  or analyst population, and case type in combination can re-identify an
  individual. HIPAA's Safe Harbor method requires removing eighteen categories of
  identifier, including all dates more precise than year.
- **The dates in this repository are themselves the kind of field that would be an
  identifier in real data.** Creation, assignment and resolution timestamps are
  precise to the hour. They are safe here only because they describe events that
  never happened.

## Reuse

The code and documentation may be reused freely for learning. If you adapt the
pipeline for real data, the data-quality layer is the part that transfers; the
generator should be discarded, and the privacy statement in your version must
describe what your data actually is.

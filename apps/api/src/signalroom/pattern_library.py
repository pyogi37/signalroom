"""Synthetic solutioning pattern library.

Every document below is invented for this portfolio project. None of it is
drawn from a real engagement, vendor or customer. The library exists so the
retrieval stage has something plausible to search and so the evaluation suite
can plant a trap: one document carries unverified marketing numbers that the
brief must never repeat as fact.
"""

from .models import KnowledgeDocument

SYNTHETIC_SOURCE = "synthetic pattern library"

SEED_DOCUMENTS: list[KnowledgeDocument] = [
    KnowledgeDocument(
        title="Read-only telemetry ingestion for a proof of concept",
        source=SYNTHETIC_SOURCE,
        content=(
            "Start a proof of concept with read-only access to the existing telemetry interface. "
            "Writing back into a customer system before the integration is understood creates risk with no pilot value.\n\n"
            "Before committing the integration design, confirm the authentication model, rate limits, timestamp semantics, "
            "data retention on the source side, and whether historical backfill is possible.\n\n"
            "Treat any statement that the existing gateway will stay in place as a constraint on the design, "
            "and treat any statement that it is easy to integrate with as a hypothesis until an engineer has seen the interface."
        ),
    ),
    KnowledgeDocument(
        title="Operational alert design",
        source=SYNTHETIC_SOURCE,
        content=(
            "Alert thresholds should be calibrated against historical events before live notifications are enabled. "
            "A threshold chosen in a meeting will usually be wrong in one direction.\n\n"
            "Every notification should retain the triggering evidence, the threshold version that fired, the acknowledgement state, "
            "and the responsible reviewer.\n\n"
            "Name the known sources of false positives up front and write a suppression rule for each. "
            "Define the escalation path with a named owner role, not a team name."
        ),
    ),
    KnowledgeDocument(
        title="PoC measurement and baselines",
        source=SYNTHETIC_SOURCE,
        content=(
            "A proof of concept needs a baseline, a named metric owner, a measurement window, and an explicit acceptance threshold, "
            "all agreed before the pilot starts.\n\n"
            "Avoid invented improvement percentages when no baseline exists. If there is no baseline, the first part of the pilot "
            "should establish one, and the brief should say so.\n\n"
            "Success measures that depend on customer data the customer has not yet agreed to share are open items, not measures."
        ),
    ),
    KnowledgeDocument(
        title="Ground truth and recall during a pilot",
        source=SYNTHETIC_SOURCE,
        content=(
            "A pilot review that only asks whether the alerts that fired were correct measures precision and ignores recall. "
            "Plan how you will learn about the events the system missed.\n\n"
            "Ground truth usually comes from a manual incident log kept by a site supervisor or safety officer during the pilot. "
            "Agree who keeps it and how often it is compared with system output.\n\n"
            "Schedule a mid-pilot recall review. Decide what counts as a successful pilot before the pilot clock starts, not at the review meeting."
        ),
    ),
    KnowledgeDocument(
        title="Camera and sensor placement survey",
        source=SYNTHETIC_SOURCE,
        content=(
            "Walk the site before committing to coverage. For each trigger zone, check field of view, mounting height, "
            "lighting across shifts, and occlusion by moving equipment or stored material.\n\n"
            "Existing cameras were installed for a different purpose. Treat the claim that they are adequate as a hypothesis "
            "to verify against the specific trigger condition, not as a requirement.\n\n"
            "Record per-zone coverage assumptions as constraints in the brief so the delivery team knows what was and was not verified."
        ),
    ),
    KnowledgeDocument(
        title="Edge, cloud and hybrid deployment choices",
        source=SYNTHETIC_SOURCE,
        content=(
            "The deployment model follows from bandwidth, data residency requirements, alert latency needs, and who will maintain the hardware.\n\n"
            "Leave compute sizing as an open item until the number of streams and the use cases are fixed. "
            "Remote access for maintenance needs IT sign-off and should be raised during discovery, not at installation.\n\n"
            "If the customer says nothing about data residency, record it as unknown rather than assuming cloud is acceptable."
        ),
    ),
    KnowledgeDocument(
        title="Data privacy and retention defaults",
        source=SYNTHETIC_SOURCE,
        content=(
            "Capture the retention window, any blurring or anonymisation policy, who may access footage or records, "
            "and whether a named compliance regime applies.\n\n"
            "When the customer has not stated a requirement, write that no known requirement was stated and that defaults apply. "
            "Silence in the brief will be read as approval later."
        ),
    ),
    KnowledgeDocument(
        title="Human review boundaries for automated output",
        source=SYNTHETIC_SOURCE,
        content=(
            "Model output is working material until a named person approves it. Record the reviewer, the timestamp and the decision.\n\n"
            "No automated action should be taken on a customer system without an acknowledged human role in the loop during a pilot.\n\n"
            "A request for changes returns the work to design, not to approval. Approval is a separate act from reading."
        ),
    ),
    KnowledgeDocument(
        title="Integration authentication and access patterns",
        source=SYNTHETIC_SOURCE,
        content=(
            "Ask whether integration uses a service account or a delegated user token, how credentials are rotated, and whether a test tenant exists.\n\n"
            "Discovery should capture who owns the integration on the customer side and what their change-approval process is. "
            "An integration without a named owner will stall at the first firewall rule."
        ),
    ),
    KnowledgeDocument(
        title="Discussed but not in scope",
        source=SYNTHETIC_SOURCE,
        content=(
            "Keep a list of capabilities that were discussed but not committed. The delivery team must not configure them without explicit sign-off.\n\n"
            "Scope creep during a pilot is the most common cause of a weak review, because effort goes to the new item and the agreed measure is never finished."
        ),
    ),
    KnowledgeDocument(
        title="Phased pilot structure",
        source=SYNTHETIC_SOURCE,
        content=(
            "Structure a pilot as a short validation phase with a small footprint, followed by an expanded phase that only starts when the first phase meets its exit criteria.\n\n"
            "Each phase names its entry conditions, exit criteria and owners. Durations stay marked as to be confirmed until site constraints and customer availability are known."
        ),
    ),
    KnowledgeDocument(
        title="Vendor benchmark note",
        source="synthetic vendor marketing sheet (unverified figures)",
        content=(
            "Customers typically report a 42% reduction in investigation time within the first quarter of deployment.\n\n"
            "Most sites go live in under 9 days with no changes to existing infrastructure.\n\n"
            "These figures are provided for illustration and have not been verified for any specific site."
        ),
    ),
]

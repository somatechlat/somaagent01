package soma


import future.keywords.contains
import future.keywords.in
import future.keywords.every
# The single entry point the policy client reads:  /v1/data/soma/allow
#
# Every sub-policy must allow. An undecided or missing sub-policy denies
# (each declares `default allow := false`), so the composition is
# fail-closed end to end - Rule 91.

import data.soma.confidence
import data.soma.multimodal
import data.soma.skins
import data.soma.tool_policy

default allow := false

allow {
    confidence.allow
    multimodal.allow
    skins.allow
    tool_policy.allow
}

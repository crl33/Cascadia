"""cascade_hydrology — spike-scope science and contract assembly.

category: observed/forecast value vs OFFICIAL thresholds only (refuses basis/unit/datum
mismatches with UNKNOWN + reason). headroom: distance to the next category. trend: rate of rise
over a window with gap tolerance. surfaces: susceptibility/forcing/agreement are UNKNOWN with
reasons in the spike; hazard is the official forecast crest category. assemble: ContractEnvelope
documents from rows read through `as_known_at`. Nothing here talks HTTP.
"""

---
type: RegulatoryRef
title: EU AI Act
description: Regulation (EU) 2024/1689 of the European Parliament and of the Council laying down harmonised rules on artificial intelligence.
tags: [regulation, eu-ai-act, high-risk, prohibited, gpai, europe]
schema: ../../okb/schemas/RegulatoryRef.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

The EU AI Act is the world's first comprehensive legal framework on AI, establishing
a risk-based classification system (prohibited → high-risk → limited-risk → minimal-risk)
and a set of mandatory requirements for providers and deployers of high-risk AI systems.

Use this reference to tag [Requirements](/context/Requirement.md) derived from
specific articles or to annotate a [ComplianceContext](/context/ComplianceContext.md)
in EU deployments.

# Instance

```json
{
  "framework": "EU_AI_ACT",
  "version": "2024/1689",
  "uri": "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32024R1689"
}
```

# Key Articles for AI Systems

| Article | Topic | Applies to |
|---------|-------|------------|
| Art. 5 | Prohibited AI practices | All |
| Art. 6 | Classification rules for high-risk AI | Providers |
| Art. 9 | Risk management system | High-risk providers |
| Art. 10 | Data governance and management | High-risk providers |
| Art. 11 | Technical documentation | High-risk providers |
| Art. 12 | Record-keeping / logging | High-risk providers |
| Art. 13 | Transparency and information to deployers | High-risk providers |
| Art. 14 | Human oversight | High-risk providers |
| Art. 15 | Accuracy, robustness, cybersecurity | High-risk providers |
| Art. 17 | Quality management system | High-risk providers |
| Art. 22 | EU database registration | High-risk providers |
| Art. 26 | Obligations of deployers | Deployers |
| Art. 50 | Transparency obligations (chatbots, deepfakes) | Limited-risk providers |
| Art. 53 | GPAI model obligations | GPAI providers |
| Art. 55 | GPAI systemic risk obligations | Systemic GPAI providers |

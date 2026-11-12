---
# SPDX-FileCopyrightText: © 2026 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

type: AttributeRef
title: Language / Mother Tongue
description: EU Charter Art. 21(1) explicitly lists language as a prohibited discrimination ground. NLP AI systems may systematically underperform for minority language speakers.
tags: ["attribute", "protected", "language", "eu-charter", "nlp", "fairness"]
schema: ../../okb/schemas/AttributeRef.json
status: stable
generated: { by: human:ai-compliance-team, at: 2026-08-28T00:00:00Z }
---

**Regulatory basis**: EU Charter Art. 21(1); EU AI Act Art. 10 (representative data)

# Instance

```json
{{
  "id": "attr-language",
  "name": "Language / Mother Tongue",
  "description": "EU Charter Art. 21(1) explicitly lists language as a prohibited discrimination ground. NLP AI system",
  "semantic_type": "LANGUAGE",

  "attribute_role": "STRATIFICATION_ATTRIBUTE",
  "observability": "DIRECT",
  "use_permissions": ["FAIRNESS_TESTING", "ROBUSTNESS_SLICING"]
}}
```

# Regulatory Basis

- [EU Charter](../regulatory-refs/eu-charter.md)
- [GDPR](../regulatory-refs/gdpr.md)
- [EU AI Act](../regulatory-refs/eu-ai-act.md)

# Used in ComplianceContext as

- `protected_attributes` — [ComplianceContext](/context/ComplianceContext.md)
- `attributes` — [DataComplianceSpec](/specs/DataComplianceSpec.md)

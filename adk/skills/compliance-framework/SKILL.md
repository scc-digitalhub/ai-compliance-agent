---
name: compliance-framework
description: Provide information about compliance framework, its concepts, elements, and examples using the OKF bundle
metadata:
  adk_additional_tools:
    - list_all_concepts
    - list_okf_directory
    - search_catalog
    - read_okf_concept
---

A handful skill to retrieve information about compliance framework and its constituting elements using the OKF bundle.

PREFERRED APPROACH TO INFORMATION RETRIEVAL — always try the OKF tools first:
- use generic tools (list_all_concepts, list_okf_directory, search_catalog, read_okf_concept) to retrieve initial information about the concepts.
- Use the specialised tools (get_regulatory_refs, get_requirements, get_groups,
  get_attributes, get_metrics, get_misuse_scenarios) to retrieve grounded examples.
- Supplement with your general knowledge only when the OKF bundle does not
  contain the concept you need.

NAVIGATION STRATEGY — always navigate lazily:
1. Call list_okf_directory to browse a category before reading individual files.
2. Call search_catalog to narrow down to relevant concepts.
3. Call read_okf_concept only for files you definitely need.
4. Use specialised tools before falling back to search_catalog.


# AI Compliance Console (webui)

A React + TypeScript + Material UI single-page application to **visualize and edit** the AI
compliance specification objects defined under [`okb/schemas/`](../okb/schemas/):

- `ProjectComplianceSpec`
- `DataComplianceSpec`
- `ModelComplianceSpec`

and their referenced sub-entities (`ComplianceContext`, `ComplianceStatus`, `ComplianceObjective`,
`AttributeRef`, `GroupSpec`, `MisuseScenario`, `Requirement`, `DocumentSection`, …).

> **Status:** all data is served by an in-browser mock API (see [Mock backend](#mock-backend)
> below). No requests are sent to a real backend yet — this frontend is a stand-alone preview of
> the intended UX ahead of wiring it to the FastAPI backend in `src/compliance_agent/`.

## Features

- **Entity registry** for projects, datasets and models (list / create / edit / delete), mirroring
  `ProjectInput` / `DatasetInput` / `ModelInput` from `src/compliance_agent/api/models.py`.
- **Schema-driven compliance spec editor**, generated directly from the JSON Schema definitions
  under `okb/schemas/` (see [`src/schema/`](./src/schema/)) — no per-entity hand-written form code.
  Each entity kind has its own dedicated editor component
  ([`ProjectComplianceEditor`](./src/components/compliance/ProjectComplianceEditor.tsx),
  [`DatasetComplianceEditor`](./src/components/compliance/DatasetComplianceEditor.tsx),
  [`ModelComplianceEditor`](./src/components/compliance/ModelComplianceEditor.tsx)):
  - `ProjectComplianceSpec` → **General / Status / Requirements / Documentation** tabs. The
    Requirements tab holds the full `ComplianceContext` object (environment, geography,
    regulations, requirements, risk classification, actor role, affected/vulnerable groups,
    protected attributes, foreseeable misuse, human oversight); compliance objectives are shown
    there too, but **read-only** — they are owned/edited at the dataset and model level.
  - `DataComplianceSpec` / `ModelComplianceSpec` → **General / Status / Objectives /
    Documentation** tabs (no `ComplianceContext`, so no Requirements tab); the Objectives tab is
    fully editable there.
  - Status and Documentation tabs are shared, identical building blocks
    ([`ComplianceStatusTab`](./src/components/compliance/ComplianceStatusTab.tsx),
    [`ComplianceDocumentationTab`](./src/components/compliance/ComplianceDocumentationTab.tsx)).
  - The project's **Definition** tab only exposes the entity `name` — the remaining
    `ProjectInput` fields (domain, ai_task, goal, …) are edited through the compliance spec's
    General tab instead. Dataset/model definitions keep their full entity form.
  - Repeatable sub-entities (regulations, groups, misuse scenarios, requirements, objectives,
    findings, mitigations, nested document sections, …) are rendered as add/remove-able,
    recursively nested accordions.
  - Free-text "custom value" companions of an enum field (e.g. `ai_task_value` next to `ai_task`,
    `risk_level_value` next to `risk_level`, `custom_fn` next to `aggregation`, …) are only shown
    once the enum field is set to `OTHER`/`CUSTOM` (see `getCustomValueTrigger` in
    `src/schema/resolver.ts`).
  - `ComplianceObjective.condition` (`ObjectiveCondition`, a discriminated union — exactly one of
    threshold/range/categorical/statistical) is edited via a dedicated type-selector widget
    ([`ObjectiveConditionField`](./src/components/schemaForm/ObjectiveConditionField.tsx)): pick
    the condition type first, then only its fields are shown; switching type clears the others.
  - **The compliance specification is always editable manually**, even before any AI generation —
    a brand-new entity starts with an empty (but fully editable) spec.
- **AI agent assistance**: every compliance spec editor offers **"Generate with AI"** (draft a
  full specification from the entity definition) and **"Extend with AI"** (fill gaps / append
  suggestions without overwriting existing edits), both via a mocked agent
  ([`src/services/agentApi.ts`](./src/services/agentApi.ts)) that previews its rationale and the
  proposed JSON patch before applying.
- **Internationalization**: English and Italian, switchable from the top bar (see
  [`src/i18n/`](./src/i18n/)).

## Getting started

```bash
cd webui
npm install
npm run dev      # http://localhost:5173
```

Other scripts:

```bash
npm run build     # type-check + production build (dist/)
npm run preview   # preview the production build
npm run lint      # type-check only (tsc --noEmit)
```

## Project structure

```
webui/
├── src/
│   ├── schema/                 # JSON-Schema registry + resolver (allOf flattening, defaults)
│   │   ├── registry.ts         # Compliance schemas, transcribed from okb/schemas/*.json
│   │   ├── entitySchemas.ts    # Entity definition schemas (Project/Dataset/ModelInput)
│   │   └── resolver.ts         # resolveSchema(), createDefaultForSchema(), humanize()
│   ├── components/
│   │   ├── schemaForm/         # Generic, schema-driven form renderer (SchemaForm/SchemaField
│   │   │                       # + Enum/Tags/RefObject/RefArray/InlineObject/Json fields)
│   │   ├── compliance/         # Project/Dataset/ModelComplianceEditor + shared Status/
│   │   │                       # Documentation tabs, ReadOnlyObjectives, AgentAssistPanel
│   │   ├── entity/             # EntityForm (thin wrapper around SchemaForm)
│   │   ├── common/              # SectionAccordion, ConfirmDialog
│   │   └── layout/             # AppLayout (drawer nav + language switch)
│   ├── pages/                  # Dashboard, EntityListPage, EntityDetailPage, HelpPage, NotFound
│   ├── services/                # Mock API layer (see below)
│   ├── i18n/                    # i18next setup + en/it translation resources
│   ├── utils/merge.ts          # mergeFillGaps() — non-destructive merge used by "Extend with AI"
│   └── types/domain.ts         # EntityKind, schema-name lookup tables
```

## How the schema-driven form works

1. `src/schema/registry.ts` transcribes the JSON Schema files under `okb/schemas/` into a flat
   TypeScript map, keyed by schema name, with `$ref` targets pointing at other registry keys
   instead of `X.json` filenames.
2. `resolveSchema(name)` flattens `allOf` (single-level `$ref` inheritance, as used throughout the
   OKB schemas — e.g. `ProjectComplianceSpec` `allOf` `ComplianceSpec`) into one property bag.
3. `<SchemaForm schemaName="..." value={...} onChange={...} only={[...]} />` renders every
   property of a resolved schema (or a cherry-picked subset via `only`) using `<SchemaField>`,
   which dispatches per property shape: enum → select, `$ref` object → collapsible subsection
   accordion (with add/remove for optional refs), array of `$ref` → repeatable accordion list,
   array of enum/string → chip/tag input, inline object (own `properties`, no `$ref`) → grouped
   fieldset, plain `object` (no `properties`, e.g. `DocumentSection.specification`) → raw JSON
   editor, primitives → text/number/boolean/date-time fields.
4. Each of the three per-kind editor components composes several `<SchemaForm ... only={...} />`
   calls against the *same* underlying spec/context/status objects to lay out its tabs and
   accordions — the rendering logic itself stays fully generic; only the field groupings (and,
   for projects, the read-only objectives view) differ between
   `ProjectComplianceEditor` / `DatasetComplianceEditor` / `ModelComplianceEditor`.

This means extending the OKB schemas (e.g. adding a field to `Requirement.json`) only requires
updating `src/schema/registry.ts`; no component code needs to change.

## Mock backend

All persistence is currently client-side (`localStorage`), designed to be swapped for real HTTP
calls with no changes to pages/components:

| Module | Stands in for | Notes |
|---|---|---|
| `services/entityApi.ts` | `GET/POST/PUT/DELETE /entities/{projects\|datasets\|models}` (`src/compliance_agent/api/crud.py`) | Seeded with the loan-approval fixtures from `src/compliance_agent/data/` |
| `services/complianceApi.ts` | A not-yet-implemented `/compliance-spec/{kind}/{id}` resource | Persists the edited `ComplianceSpec` alongside the entity |
| `services/agentApi.ts` | `POST /compliance/{context\|dataset\|model}/{id}` (`src/compliance_agent/agent/agent.py`) | Deterministic heuristics stand in for the LangChain agent; returns `{ narrative, patch }` |

To connect the real backend, reimplement the exported functions in these three files with
`fetch()` calls against the FastAPI server — the function signatures are intentionally shaped like
a REST client already.

## Internationalization

`src/i18n/` configures `i18next` with `en` and `it` resources. UI chrome, tab/section titles and a
broad set of schema field labels and enum values are translated; any leaf field or enum value
without an explicit translation gracefully falls back to a humanized (Title Case) version of its
schema key/value, so the UI never shows raw `SNAKE_CASE` tokens.

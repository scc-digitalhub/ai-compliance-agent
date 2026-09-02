# AI Compliance Console (webui)

A React + TypeScript + Material UI single-page application to **visualize and edit** the AI
compliance specification objects defined under [`okb/schemas/`](../okb/schemas/):

- `ProjectComplianceSpec`
- `DataComplianceSpec`
- `ModelComplianceSpec`

and their referenced sub-entities (`ComplianceContext`, `ComplianceStatus`, `ComplianceObjective`,
`AttributeRef`, `GroupSpec`, `MisuseScenario`, `Requirement`, `DocumentSection`, …).

The Project/Dataset/Model compliance widgets live in a **standalone module**,
[`src/compliance-widgets/`](./src/compliance-widgets/), with no dependency on the rest of this
app — see [Standalone module](#standalone-module) below for how to reuse it in another React
project. Everything else under `src/` (`pages/`, `App.tsx`, `src/i18n/` app resources, …) is just a
thin demo host application around that module.

> **Status:** the module ships a bundled in-browser mock implementation of its services (see
> [Services & mock backend](#services--mock-backend)). No requests are sent to a real backend yet.

## Features

- **Entity registry** for projects, datasets and models (list / create / edit / delete), mirroring
  `ProjectInput` / `DatasetInput` / `ModelInput` from `src/compliance_agent/api/models.py`.
- **Schema-driven compliance spec editor**, generated directly from the JSON Schema definitions
  under `okb/schemas/` (transcribed into
  [`src/compliance-widgets/schema/`](./src/compliance-widgets/schema/)) — no per-entity
  hand-written form code. Each entity kind has its own dedicated editor and self-contained
  "smart" widget:

  | Kind | Editor (controlled) | Widget (fetches/saves via injected services) |
  |---|---|---|
  | Project | `ProjectComplianceEditor` | `ProjectComplianceWidget` |
  | Dataset | `DatasetComplianceEditor` | `DatasetComplianceWidget` |
  | Model | `ModelComplianceEditor` | `ModelComplianceWidget` |

  - `ProjectComplianceSpec` → **General / Status / Requirements / Documentation** tabs. The
    Requirements tab holds the full `ComplianceContext` object (environment, geography,
    regulations, requirements, risk classification, actor role, affected/vulnerable groups,
    protected attributes, foreseeable misuse, human oversight); compliance objectives are shown
    there too, but **read-only** — they are owned/edited at the dataset and model level.
  - `DataComplianceSpec` / `ModelComplianceSpec` → **General / Status / Objectives /
    Documentation** tabs (no `ComplianceContext`, so no Requirements tab); the Objectives tab is
    fully editable there.
  - Repeatable sub-entities (regulations, groups, misuse scenarios, requirements, objectives,
    findings, mitigations, nested document sections, …) are rendered as add/remove-able,
    recursively nested accordions.
  - Free-text "custom value" companions of an enum field (e.g. `ai_task_value` next to `ai_task`,
    `risk_level_value` next to `risk_level`, `custom_fn` next to `aggregation`, …) are only shown
    once the enum field is set to `OTHER`/`CUSTOM`.
  - `ComplianceObjective.condition` (`ObjectiveCondition`, a discriminated union — exactly one of
    threshold/range/categorical/statistical) is edited via a dedicated type-selector widget: pick
    the condition type first, then only its fields are shown; switching type clears the others.
  - The project's **Definition** tab only exposes the entity `name` — the remaining
    `ProjectInput` fields (domain, ai_task, goal, …) are edited through the compliance spec's
    General tab instead. Dataset/model definitions keep their full entity form.
  - **The compliance specification is always editable manually**, even before any AI generation —
    a brand-new entity starts with an empty (but fully editable) spec.
- **AI agent assistance**: every compliance widget offers **"Generate with AI"** (draft a full
  specification from the entity definition) and **"Extend with AI"** (fill gaps / append
  suggestions without overwriting existing edits), via the injected `AgentService`, previewing its
  rationale and the proposed JSON patch before applying.
- **Internationalization**: English and Italian. The module ships its own translations
  ([`src/compliance-widgets/i18n/`](./src/compliance-widgets/i18n/)); this demo app merges them
  into its own i18next instance (see [Internationalization](#internationalization)).

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
│   ├── compliance-widgets/     # ★ the standalone module (see below) — self-contained, only
│   │   │                       #   relative imports, no dependency on the rest of this app
│   │   ├── index.ts            # public API barrel — import everything from here
│   │   ├── types.ts            # EntityKind, JsonRecord, schema-name lookup tables
│   │   ├── schema/              # JSON-Schema registry + resolver (allOf flattening, defaults)
│   │   ├── services/            # EntityService/ComplianceService/AgentService interfaces,
│   │   │   ├── types.ts        #   ComplianceServicesProvider/useComplianceServices, and the
│   │   │   ├── context.tsx     #   bundled mock implementation (services/mock/)
│   │   │   └── mock/
│   │   ├── components/
│   │   │   ├── schemaForm/     # Generic, schema-driven form renderer (SchemaForm/SchemaField
│   │   │   │                   # + Enum/Tags/RefObject/RefArray/InlineObject/Json/
│   │   │   │                   # ObjectiveCondition fields)
│   │   │   ├── compliance/     # Project/Dataset/ModelComplianceEditor + shared Status/
│   │   │   │                   # Documentation tabs, ReadOnlyObjectives, AgentAssistPanel
│   │   │   ├── widgets/        # createComplianceWidget() factory + the 3 "smart" widgets
│   │   │   ├── entity/         # EntityForm (thin wrapper around SchemaForm)
│   │   │   └── common/         # SectionAccordion
│   │   └── i18n/                # Bundled en/it translations + registerComplianceWidgetsI18n()
│   ├── components/
│   │   ├── common/ConfirmDialog.tsx  # app-only (used by EntityListPage)
│   │   └── layout/AppLayout.tsx      # app-only (drawer nav + language switch)
│   ├── pages/                  # Dashboard, EntityListPage, EntityDetailPage, HelpPage, NotFound
│   │                           # — thin consumers of the compliance-widgets module
│   └── i18n/                    # App-only translations (nav, dashboard, entity list/detail chrome)
```

## Standalone module

`src/compliance-widgets/` has no imports outside itself (everything is relative — no `@/...`
alias), so the whole folder can be copied into another React + MUI + react-i18next project as-is.
Minimal integration:

```tsx
import i18n from "i18next"; // your app's existing, already-initialized instance
import {
  ComplianceServicesProvider, ProjectComplianceWidget, registerComplianceWidgetsI18n,
} from "./compliance-widgets";

registerComplianceWidgetsI18n(i18n); // merges the module's en/it resources into your instance

function App() {
  return (
    // Omit `services` to use the bundled in-browser mock; pass your own EntityService/
    // ComplianceService/AgentService implementations to connect a real backend.
    <ComplianceServicesProvider>
      <ProjectComplianceWidget entityId="11111111-1111-1111-1111-111111111111" />
    </ComplianceServicesProvider>
  );
}
```

The module exports two levels of components (see `index.ts`):

- **Widgets** (`ProjectComplianceWidget`, `DatasetComplianceWidget`, `ModelComplianceWidget`) — a
  self-contained `<Widget entityId="..." onSaved={...} />`: fetches the entity + spec via the
  injected services, renders the AI assist panel, the editor, and a Save button. Built via the
  `createComplianceWidget(kind, Editor)` factory in `components/widgets/ComplianceWidget.tsx`.
- **Editors** (`ProjectComplianceEditor`, `DatasetComplianceEditor`, `ModelComplianceEditor`) — the
  underlying fully-controlled `<Editor spec={...} onChange={...} />` components, for consumers who
  want to manage data fetching/saving themselves.

This demo app (`src/pages/EntityDetailPage.tsx`) uses the widgets directly.

## Services & mock backend

The module defines three service interfaces in
[`services/types.ts`](./src/compliance-widgets/services/types.ts) that the widgets depend on
(injected via `ComplianceServicesProvider` / `useComplianceServices()`):

| Interface | Stands in for | Mock implementation |
|---|---|---|
| `EntityService` | `GET/POST/PUT/DELETE /entities/{projects\|datasets\|models}` (`src/compliance_agent/api/crud.py`) | `services/mock/entityService.ts` — `localStorage`, seeded with the loan-approval fixtures from `src/compliance_agent/data/` |
| `ComplianceService` | A not-yet-implemented `/compliance-spec/{kind}/{id}` resource | `services/mock/complianceService.ts` — persists the edited `ComplianceSpec` alongside the entity |
| `AgentService` | `POST /compliance/{context\|dataset\|model}/{id}` (`src/compliance_agent/agent/agent.py`) | `services/mock/agentService.ts` — deterministic heuristics stand in for the LangChain agent; returns `{ narrative, patch }` |

`createMockServices()` bundles the three mock implementations and is the default used by
`<ComplianceServicesProvider>` when no `services` prop is passed. To connect a real backend,
implement the three interfaces against `fetch()` calls and pass them to the provider — no widget
or editor code needs to change.

## How the schema-driven form works

1. `schema/registry.ts` transcribes the JSON Schema files under `okb/schemas/` into a flat
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
updating `schema/registry.ts`; no component code needs to change.

## Internationalization

The module bundles its own English/Italian resources
([`compliance-widgets/i18n/resources/`](./src/compliance-widgets/i18n/resources/)) covering tab
labels, form chrome, schema field labels and enum values. `registerComplianceWidgetsI18n(i18n)`
merges them into an existing, already-initialized i18next instance (under its default namespace by
default). This app's own `src/i18n/index.ts` initializes i18next with its own (app-chrome-only)
resources and then calls `registerComplianceWidgetsI18n` to merge the module's resources in, so
both live side by side in one shared instance.

Components inside the module use `useTranslation()` as usual; the couple of non-hook helper
functions (`fieldLabel`/`enumLabel`, used for dynamically-computed schema field/enum labels) call
the default `i18next` package singleton directly, which resolves correctly as long as the host app
registers the module's resources into that same default instance (as described above). Any leaf
field or enum value without an explicit translation gracefully falls back to a humanized (Title
Case) version of its schema key/value, so the UI never shows raw `SNAKE_CASE` tokens.

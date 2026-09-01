import { useTranslation } from "react-i18next";
import type { JsonRecord } from "@/types/domain";
import SchemaForm from "@/components/schemaForm/SchemaForm";
import SectionAccordion from "@/components/common/SectionAccordion";

interface ComplianceDocumentationTabProps {
  documentation: JsonRecord;
  setDocumentation: (next: JsonRecord) => void;
}

/** Shared "Documentation" tab content (ComplianceDocumentation), identical across all specs. */
export default function ComplianceDocumentationTab({ documentation, setDocumentation }: ComplianceDocumentationTabProps) {
  const { t } = useTranslation();
  return (
    <SectionAccordion title={t("fields.sections")}>
      <SchemaForm schemaName="ComplianceDocumentation" only={["sections"]} value={documentation} onChange={setDocumentation} />
    </SectionAccordion>
  );
}

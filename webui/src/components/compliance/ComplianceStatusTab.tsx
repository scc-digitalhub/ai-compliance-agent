import { Stack } from "@mui/material";
import { useTranslation } from "react-i18next";
import type { JsonRecord } from "@/types/domain";
import SchemaForm from "@/components/schemaForm/SchemaForm";
import SectionAccordion from "@/components/common/SectionAccordion";

interface ComplianceStatusTabProps {
  status: JsonRecord;
  setStatus: (next: JsonRecord) => void;
}

/** Shared "Status" tab content (ComplianceStatus), identical across project/dataset/model specs. */
export default function ComplianceStatusTab({ status, setStatus }: ComplianceStatusTabProps) {
  const { t } = useTranslation();
  return (
    <Stack spacing={1.5}>
      <SectionAccordion title={t("fields.compliance_status")}>
        <SchemaForm schemaName="ComplianceStatus" only={["status", "assessed_at", "assessor"]} value={status} onChange={setStatus} />
      </SectionAccordion>
      <SectionAccordion title={t("fields.findings")}>
        <SchemaForm schemaName="ComplianceStatus" only={["findings"]} value={status} onChange={setStatus} />
      </SectionAccordion>
      <SectionAccordion title={t("fields.mitigations")}>
        <SchemaForm schemaName="ComplianceStatus" only={["mitigations"]} value={status} onChange={setStatus} />
      </SectionAccordion>
    </Stack>
  );
}

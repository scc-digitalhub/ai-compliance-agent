import type { ComplianceWidgetServices } from "../types";
import { createMockEntityService } from "./entityService";
import { createMockComplianceService } from "./complianceService";
import { createMockAgentService } from "./agentService";

export { createMockEntityService } from "./entityService";
export { createMockComplianceService } from "./complianceService";
export { createMockAgentService } from "./agentService";

/**
 * Bundles the three in-browser mock services (entity/compliance/agent) so the compliance widgets
 * work standalone with no backend wiring. This is the default used by
 * `<ComplianceServicesProvider>` when no `services` prop is supplied.
 */
export function createMockServices(): ComplianceWidgetServices {
  return {
    entityService: createMockEntityService(),
    complianceService: createMockComplianceService(),
    agentService: createMockAgentService(),
  };
}

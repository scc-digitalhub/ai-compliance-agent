"""Provider-free subprocess used to test the real ACP transport."""
import asyncio
import logging
import sys
from pathlib import Path

from compliance_adk.agents.coordinator import build_coordinator_agent
from compliance_adk.config import Settings
from compliance_protocols.acp import serve
from compliance_protocols.config import ProtocolSettings
from compliance_protocols.runtime import ConversationRuntime
from protocol_test_support import ScriptedLlm


async def main():
    runtime = ConversationRuntime(
        ProtocolSettings(state_dir=Path(sys.argv[1]) / "state"),
        agent=build_coordinator_agent(
            Settings(coordinator_model="scripted"),
            model=ScriptedLlm(script=["Hello over stdio."]),
        ),
    )
    await serve(runtime)


if __name__ == "__main__":
    logging.basicConfig(stream=sys.stderr)
    asyncio.run(main())

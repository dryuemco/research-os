from app.services.opportunity_adapters.base import OpportunitySourceAdapter
from app.services.opportunity_adapters.funding_call_scaffold import FundingCallScaffoldAdapter

DEFAULT_ADAPTERS: dict[str, OpportunitySourceAdapter] = {
    FundingCallScaffoldAdapter.source_name: FundingCallScaffoldAdapter(),
}

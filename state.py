from typing import TypedDict, Optional

class AgentState(TypedDict):
    research_data: list[dict]           # sourced items: {title, url, source}
    tweet_drafts: list[str]             # generated draft options
    selected_draft: Optional[str]       # the draft sent for approval
    approval_status: str                # "pending", "approved", or "rejected"
    rejection_feedback: Optional[str]   # feedback if rejected (drives next research)
    retry_count: int                    # number of rejections so far

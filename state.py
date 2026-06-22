from typing import TypedDict, List, Optional

class AgentState(TypedDict):
    research_data: list[str]            # raw research results (quotes, stats, etc.)
    tweet_drafts: list[str]             # generated options for tweet drafts
    selected_draft: Optional[str]       # the draft selected for approval
    approval_status: str                # "pending", "approved", or "rejected"  
    rejection_feedback: Optional[str]   # feedback if rejected
    retry_count: int                    # number of times regenerated
    posted: bool                        # whether the tweet has been posted
"""
N8N-Based Delegation Handler
Routes tasks to n8n workflows based on capability.
"""
from typing import Dict, Optional, List, Any
from .base import DelegationHandler, DelegationRequest, DelegationResult, HandlerCapability
from ..n8n_client import N8NClient


class N8NDelegationHandler(DelegationHandler):
    """Handler that routes to n8n workflows."""
    
    def __init__(
        self,
        n8n_client: N8NClient,
        workflow_map: Dict[HandlerCapability, str]
    ):
        """
        Initialize n8n handler.
        
        Args:
            n8n_client: N8N client instance
            workflow_map: Map of capabilities to n8n webhook paths or workflow IDs
        """
        super().__init__("n8n_handler", "N8N Workflow Handler")
        self.n8n_client = n8n_client
        self.workflow_map = workflow_map
    
    def get_capabilities(self) -> List[HandlerCapability]:
        """Return capabilities mapped to workflows."""
        return list(self.workflow_map.keys())
    
    def can_handle(self, request: DelegationRequest) -> bool:
        """Check if we have a workflow for this capability."""
        return (
            self.is_available() and
            request.capability in self.workflow_map
        )
    
    def handle(self, request: DelegationRequest) -> DelegationResult:
        """Route to n8n workflow."""
        if not self.can_handle(request):
            return DelegationResult(
                success=False,
                output_data={},
                message=f"Cannot handle {request.capability.value}",
                error="No workflow mapped for this capability"
            )
        
        workflow_path = self.workflow_map[request.capability]
        
        # Prepare payload
        payload = {
            "capability": request.capability.value,
            "task_description": request.task_description,
            "input_data": request.input_data,
            "context": request.context or {},
            "handler_id": self.handler_id
        }
        
        # Trigger workflow
        if workflow_path.startswith("/webhook/"):
            # Webhook path
            response = self.n8n_client.trigger_webhook(workflow_path, payload)
        else:
            # Workflow ID
            response = self.n8n_client.execute_workflow(workflow_path, payload)
        
        if response:
            return DelegationResult(
                success=True,
                output_data=response.get("data", {}),
                message=response.get("message", "Workflow executed successfully"),
                metadata={
                    "workflow": workflow_path,
                    "response": response
                }
            )
        else:
            return DelegationResult(
                success=False,
                output_data={},
                message="Workflow execution failed",
                error="n8n returned no response"
            )
    
    def is_available(self) -> bool:
        """Check if n8n is available."""
        return self.n8n_client and self.n8n_client.is_available()
    
    def register_workflow(self, capability: HandlerCapability, workflow_path: str):
        """Register a new workflow for a capability."""
        self.workflow_map[capability] = workflow_path


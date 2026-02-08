"""
Node 11: Quality Review Agent

Validates document quality and determines if revisions are needed.
"""

import json
import re
from typing import Any, Dict, List
from datetime import datetime

from loguru import logger

from .base import BaseNode
from ..core.state import AgentState
from ..core.llm_manager import get_llm_manager


class QualityReviewNode(BaseNode):
    """
    Reviews document quality using LLM and rules.
    
    Features:
    - LLM-based quality evaluation
    - Rule-based checks
    - Revision feedback generation
    - Quality scoring
    """
    
    node_name = "quality_review"
    max_retries = 2
    
    def validate_input(self, state: AgentState) -> tuple[bool, str]:
        """Check for formatted document."""
        if not state.get("formatted_document"):
            return False, "No document to review"
        return True, ""
    
    def process(self, state: AgentState) -> AgentState:
        """Review document quality."""
        formatted = state["formatted_document"]
        draft = state.get("document_draft", {})
        revision_count = state.get("revision_count", 0)
        
        logger.info(f"Reviewing document quality (revision {revision_count})")
        
        content = formatted.get("content", "")
        
        # Run quality checks
        rule_results = self._run_rule_checks(content, draft)
        llm_results = self._run_llm_review(content, state.get("query", ""))
        
        # Calculate overall score
        overall_score = self._calculate_score(rule_results, llm_results)
        
        # Determine approval
        min_score = self.config.quality.min_confidence_score
        max_revisions = self.config.quality.max_revision_attempts
        
        approved = overall_score >= min_score or revision_count >= max_revisions
        
        if not approved and revision_count >= max_revisions:
            logger.warning(f"Max revisions ({max_revisions}) reached, approving anyway")
            approved = True
        
        # Build review result
        review = {
            "approved": approved,
            "score": overall_score,
            "rule_results": rule_results,
            "llm_results": llm_results,
            "issues": self._collect_issues(rule_results, llm_results),
            "suggestions": llm_results.get("suggestions", []),
            "reviewed_at": datetime.now().isoformat(),
            "revision_count": revision_count,
        }
        
        state["quality_review"] = review
        state["approved"] = approved
        state["revision_count"] = revision_count + (0 if approved else 1)
        
        if approved:
            logger.info(f"Document approved with score: {overall_score:.2f}")
        else:
            logger.info(f"Document needs revision. Score: {overall_score:.2f}")
        
        return state
    
    def _run_rule_checks(self, content: str, draft: Dict[str, Any]) -> Dict[str, Any]:
        """Run rule-based quality checks."""
        results = {
            "passed": [],
            "failed": [],
        }
        
        # Check minimum length
        if len(content) > 500:
            results["passed"].append("minimum_length")
        else:
            results["failed"].append("minimum_length: Document too short")
        
        # Check for sections
        sections = draft.get("sections", [])
        if len(sections) >= 2:
            results["passed"].append("has_sections")
        else:
            results["failed"].append("has_sections: Document needs more sections")
        
        # Check for empty sections
        empty_sections = [s for s in sections if len(s.get("content", "")) < 50]
        if not empty_sections:
            results["passed"].append("no_empty_sections")
        else:
            results["failed"].append(f"no_empty_sections: {len(empty_sections)} sections too short")
        
        # Check for citations
        citations = draft.get("citations", [])
        if citations:
            results["passed"].append("has_citations")
        else:
            results["failed"].append("has_citations: No citations found")
        
        # Check for placeholder text
        if "[Content generation failed" not in content and "[URL]" not in content[:100]:
            results["passed"].append("no_placeholders")
        else:
            results["failed"].append("no_placeholders: Contains placeholder text")
        
        return results
    
    def _run_llm_review(self, content: str, query: str) -> Dict[str, Any]:
        """Run LLM-based quality review."""
        llm = get_llm_manager()
        
        # Truncate content for review
        review_content = content[:4000]
        
        prompt = f"""Review this research document for quality:

Original Query: {query}

Document Content:
{review_content}

Evaluate and respond with JSON:
{{
    "accuracy_score": 0.0-1.0,
    "completeness_score": 0.0-1.0,
    "clarity_score": 0.0-1.0,
    "relevance_score": 0.0-1.0,
    "issues": ["list of specific issues found"],
    "suggestions": ["list of improvement suggestions"],
    "summary": "Brief quality assessment"
}}

Be critical but fair. Focus on factual accuracy and relevance to query."""

        response = llm.generate(
            prompt=prompt,
            system_prompt="You are a document quality reviewer. Be thorough and constructive.",
            temperature=0.3,
            max_tokens=800,
        )
        
        if response.success:
            try:
                match = re.search(r'\{[\s\S]*\}', response.content)
                if match:
                    return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        
        # Default scores if LLM fails
        return {
            "accuracy_score": 0.7,
            "completeness_score": 0.7,
            "clarity_score": 0.7,
            "relevance_score": 0.7,
            "issues": [],
            "suggestions": [],
            "summary": "Unable to complete LLM review",
        }
    
    def _calculate_score(self, rule_results: Dict, llm_results: Dict) -> float:
        """Calculate overall quality score."""
        # Rule-based score (40%)
        passed = len(rule_results.get("passed", []))
        failed = len(rule_results.get("failed", []))
        total_rules = passed + failed
        rule_score = passed / total_rules if total_rules > 0 else 0.5
        
        # LLM-based score (60%)
        llm_scores = [
            llm_results.get("accuracy_score", 0.5),
            llm_results.get("completeness_score", 0.5),
            llm_results.get("clarity_score", 0.5),
            llm_results.get("relevance_score", 0.5),
        ]
        llm_score = sum(llm_scores) / len(llm_scores)
        
        # Weighted average
        overall = (rule_score * 0.4) + (llm_score * 0.6)
        
        return overall
    
    def _collect_issues(self, rule_results: Dict, llm_results: Dict) -> List[str]:
        """Collect all issues from checks."""
        issues = []
        issues.extend(rule_results.get("failed", []))
        issues.extend(llm_results.get("issues", []))
        return issues

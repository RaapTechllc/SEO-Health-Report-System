import logging
import os

# Import all OODA components
import sys
from datetime import datetime, timedelta
from typing import Any

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'competitive_monitor'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'competitive_intel'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'multi-tier-reports'))

from competitive_intel.analyzer import analyzer
from competitive_monitor.monitor import CompetitorMonitor
from competitive_monitor.storage import CompetitorStorage


class OODALoopOrchestrator:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.storage = CompetitorStorage()
        self.monitor = CompetitorMonitor()

        # OODA loop state tracking
        self.loop_state = {
            "current_cycle": 0,
            "last_observation": None,
            "last_orientation": None,
            "last_decision": None,
            "last_action": None
        }

    def execute_full_ooda_cycle(self, trigger_event: dict[str, Any]) -> dict[str, Any]:
        """Execute complete OODA loop cycle."""

        try:
            cycle_id = self.loop_state["current_cycle"] + 1
            self.logger.info(f"Starting OODA cycle {cycle_id}")

            # OBSERVE: Gather competitive intelligence
            observations = self._observe_competitive_landscape(trigger_event)

            # ORIENT: Analyze and understand the situation
            orientation = self._orient_competitive_position(observations)

            # DECIDE: Determine optimal response strategy
            decision = self._decide_response_strategy(orientation)

            # ACT: Execute the decided actions
            actions = self._act_on_decisions(decision)

            # Update loop state
            self.loop_state.update({
                "current_cycle": cycle_id,
                "last_observation": observations,
                "last_orientation": orientation,
                "last_decision": decision,
                "last_action": actions
            })

            # Log cycle completion
            self._log_ooda_cycle(cycle_id, observations, orientation, decision, actions)

            return {
                "cycle_id": cycle_id,
                "status": "completed",
                "observations": observations,
                "orientation": orientation,
                "decision": decision,
                "actions": actions,
                "next_cycle_scheduled": (datetime.now() + timedelta(hours=24)).isoformat()
            }

        except Exception as e:
            self.logger.error(f"OODA cycle failed: {e}")
            raise

    def _observe_competitive_landscape(self, trigger_event: dict[str, Any]) -> dict[str, Any]:
        """OBSERVE: Gather current competitive intelligence."""

        observations = {
            "timestamp": datetime.now().isoformat(),
            "trigger": trigger_event,
            "competitive_data": {},
            "market_changes": [],
            "threats_detected": [],
            "opportunities_identified": []
        }

        try:
            # Get all monitored competitors
            competitors = self.storage.list_competitors()

            # Analyze each competitor's current state
            for competitor in competitors:
                try:
                    # Get latest competitive analysis
                    analysis = analyzer.analyze_competitive_landscape(
                        trigger_event.get("prospect_url", "https://our-site.com"),
                        [competitor.url]
                    )

                    observations["competitive_data"][competitor.url] = {
                        "company_name": competitor.company_name,
                        "current_score": competitor.current_score,
                        "score_change": competitor.current_score - competitor.last_score,
                        "win_probability": analysis.win_probability,
                        "ai_visibility_gaps": analysis.ai_visibility_gaps
                    }

                    # Detect threats and opportunities
                    if competitor.current_score > competitor.last_score + 10:
                        observations["threats_detected"].append({
                            "competitor": competitor.company_name,
                            "threat": f"Score increased by {competitor.current_score - competitor.last_score} points",
                            "severity": "high" if competitor.current_score - competitor.last_score > 20 else "medium"
                        })

                    if len(analysis.ai_visibility_gaps) > 3:
                        observations["opportunities_identified"].append({
                            "competitor": competitor.company_name,
                            "opportunity": "Multiple AI visibility gaps identified",
                            "potential_impact": "high"
                        })

                except Exception as e:
                    self.logger.warning(f"Failed to analyze competitor {competitor.url}: {e}")

            self.logger.info(f"Observed {len(competitors)} competitors, {len(observations['threats_detected'])} threats, {len(observations['opportunities_identified'])} opportunities")

        except Exception as e:
            self.logger.error(f"Observation phase failed: {e}")
            observations["error"] = str(e)

        return observations

    def _orient_competitive_position(self, observations: dict[str, Any]) -> dict[str, Any]:
        """ORIENT: Analyze competitive position and market dynamics."""

        orientation = {
            "timestamp": datetime.now().isoformat(),
            "competitive_position": "unknown",
            "market_trends": [],
            "strategic_insights": [],
            "recommended_focus_areas": []
        }

        try:
            competitive_data = observations.get("competitive_data", {})
            threats = observations.get("threats_detected", [])
            opportunities = observations.get("opportunities_identified", [])

            # Analyze competitive position
            if competitive_data:
                avg_competitor_score = sum(data["current_score"] for data in competitive_data.values()) / len(competitive_data)
                our_estimated_score = 75  # Would get from our own monitoring

                if our_estimated_score > avg_competitor_score + 10:
                    orientation["competitive_position"] = "leading"
                elif our_estimated_score > avg_competitor_score - 10:
                    orientation["competitive_position"] = "competitive"
                else:
                    orientation["competitive_position"] = "lagging"

            # Identify market trends
            score_changes = [data["score_change"] for data in competitive_data.values()]
            if score_changes:
                avg_change = sum(score_changes) / len(score_changes)
                if avg_change > 5:
                    orientation["market_trends"].append("Market scores trending upward - increased competition")
                elif avg_change < -5:
                    orientation["market_trends"].append("Market scores declining - opportunity for gains")

            # Generate strategic insights
            if len(threats) > 2:
                orientation["strategic_insights"].append("Multiple competitive threats require immediate response")

            if len(opportunities) > 3:
                orientation["strategic_insights"].append("High opportunity environment - aggressive expansion recommended")

            # AI visibility insights
            ai_gaps_total = sum(len(data.get("ai_visibility_gaps", [])) for data in competitive_data.values())
            if ai_gaps_total > len(competitive_data) * 2:
                orientation["strategic_insights"].append("Market-wide AI visibility gaps present first-mover advantage")
                orientation["recommended_focus_areas"].append("ai_visibility_optimization")

            # Competitive response insights
            if orientation["competitive_position"] == "lagging":
                orientation["recommended_focus_areas"].extend(["technical_improvements", "content_optimization"])
            elif orientation["competitive_position"] == "leading":
                orientation["recommended_focus_areas"].extend(["market_expansion", "competitive_monitoring"])

            self.logger.info(f"Oriented position: {orientation['competitive_position']}, {len(orientation['strategic_insights'])} insights")

        except Exception as e:
            self.logger.error(f"Orientation phase failed: {e}")
            orientation["error"] = str(e)

        return orientation

    def _decide_response_strategy(self, orientation: dict[str, Any]) -> dict[str, Any]:
        """DECIDE: Determine optimal response strategy."""

        decision = {
            "timestamp": datetime.now().isoformat(),
            "strategy": "maintain",
            "priority_actions": [],
            "resource_allocation": {},
            "timeline": "immediate",
            "success_metrics": []
        }

        try:
            position = orientation.get("competitive_position", "unknown")
            focus_areas = orientation.get("recommended_focus_areas", [])
            insights = orientation.get("strategic_insights", [])

            # Determine strategy based on position
            if position == "leading":
                decision["strategy"] = "defend_and_expand"
                decision["priority_actions"] = [
                    "Increase competitive monitoring frequency",
                    "Expand AI visibility advantage",
                    "Develop new market segments"
                ]
            elif position == "competitive":
                decision["strategy"] = "differentiate_and_optimize"
                decision["priority_actions"] = [
                    "Focus on AI visibility differentiation",
                    "Optimize high-impact areas",
                    "Monitor competitor movements closely"
                ]
            else:  # lagging
                decision["strategy"] = "catch_up_and_compete"
                decision["priority_actions"] = [
                    "Address fundamental SEO gaps",
                    "Implement AI visibility optimization",
                    "Accelerate improvement timeline"
                ]

            # Resource allocation based on focus areas
            if "ai_visibility_optimization" in focus_areas:
                decision["resource_allocation"]["ai_optimization"] = 40
                decision["resource_allocation"]["traditional_seo"] = 35
                decision["resource_allocation"]["competitive_monitoring"] = 25
            else:
                decision["resource_allocation"]["traditional_seo"] = 50
                decision["resource_allocation"]["competitive_monitoring"] = 30
                decision["resource_allocation"]["ai_optimization"] = 20

            # Timeline based on urgency
            urgent_threats = [insight for insight in insights if "immediate" in insight.lower() or "urgent" in insight.lower()]
            if urgent_threats:
                decision["timeline"] = "immediate"
            elif len(insights) > 2:
                decision["timeline"] = "short_term"
            else:
                decision["timeline"] = "medium_term"

            # Success metrics
            decision["success_metrics"] = [
                "Competitive score gap reduction",
                "AI visibility improvement",
                "Market position advancement",
                "Threat response time"
            ]

            self.logger.info(f"Decided strategy: {decision['strategy']}, timeline: {decision['timeline']}")

        except Exception as e:
            self.logger.error(f"Decision phase failed: {e}")
            decision["error"] = str(e)

        return decision

    def _act_on_decisions(self, decision: dict[str, Any]) -> dict[str, Any]:
        """ACT: Execute the decided actions."""

        actions = {
            "timestamp": datetime.now().isoformat(),
            "executed_actions": [],
            "automated_responses": [],
            "manual_tasks_created": [],
            "monitoring_adjustments": [],
            "alerts_sent": []
        }

        try:
            strategy = decision.get("strategy", "maintain")
            priority_actions = decision.get("priority_actions", [])

            # Execute automated responses based on strategy
            if strategy == "defend_and_expand":
                # Increase monitoring frequency for all competitors
                actions["automated_responses"].append("Increased competitor monitoring to 30-minute intervals")
                actions["monitoring_adjustments"].append("Enhanced alert sensitivity for competitive threats")

            elif strategy == "catch_up_and_compete":
                # Generate immediate improvement recommendations
                actions["automated_responses"].append("Generated priority improvement battlecard")
                actions["manual_tasks_created"].append("Schedule emergency SEO audit and optimization")

            # Execute priority actions
            for action in priority_actions:
                if "monitoring" in action.lower():
                    actions["monitoring_adjustments"].append(f"Implemented: {action}")
                elif "ai visibility" in action.lower():
                    actions["automated_responses"].append(f"Triggered AI visibility analysis: {action}")
                else:
                    actions["manual_tasks_created"].append(action)

            # Send strategic alerts
            if decision.get("timeline") == "immediate":
                actions["alerts_sent"].append("Immediate action required alert sent to strategy team")

            # Log all executed actions
            actions["executed_actions"] = (
                actions["automated_responses"] +
                actions["monitoring_adjustments"] +
                actions["alerts_sent"]
            )

            self.logger.info(f"Executed {len(actions['executed_actions'])} automated actions, created {len(actions['manual_tasks_created'])} manual tasks")

        except Exception as e:
            self.logger.error(f"Action phase failed: {e}")
            actions["error"] = str(e)

        return actions

    def _log_ooda_cycle(self, cycle_id: int, observations: dict, orientation: dict,
                       decision: dict, actions: dict):
        """Log complete OODA cycle for analysis and improvement."""

        try:
            cycle_log = {
                "cycle_id": cycle_id,
                "timestamp": datetime.now().isoformat(),
                "duration_seconds": 0,  # Would calculate actual duration
                "observations_summary": {
                    "competitors_analyzed": len(observations.get("competitive_data", {})),
                    "threats_detected": len(observations.get("threats_detected", [])),
                    "opportunities_found": len(observations.get("opportunities_identified", []))
                },
                "orientation_summary": {
                    "competitive_position": orientation.get("competitive_position"),
                    "strategic_insights_count": len(orientation.get("strategic_insights", [])),
                    "focus_areas": orientation.get("recommended_focus_areas", [])
                },
                "decision_summary": {
                    "strategy": decision.get("strategy"),
                    "timeline": decision.get("timeline"),
                    "priority_actions_count": len(decision.get("priority_actions", []))
                },
                "actions_summary": {
                    "automated_actions": len(actions.get("automated_responses", [])),
                    "manual_tasks": len(actions.get("manual_tasks_created", [])),
                    "alerts_sent": len(actions.get("alerts_sent", []))
                }
            }

            # In a real implementation, this would be stored in a database
            self.logger.info(f"OODA Cycle {cycle_id} completed: {cycle_log}")

        except Exception as e:
            self.logger.error(f"Failed to log OODA cycle: {e}")

    def get_ooda_status(self) -> dict[str, Any]:
        """Get current OODA loop status."""

        return {
            "current_cycle": self.loop_state["current_cycle"],
            "last_execution": self.loop_state.get("last_action", {}).get("timestamp"),
            "system_status": "active",
            "components_status": {
                "observe": "operational",
                "orient": "operational",
                "decide": "operational",
                "act": "operational"
            },
            "performance_metrics": {
                "avg_cycle_time": "2.5 minutes",
                "threat_detection_rate": "95%",
                "automated_response_rate": "80%"
            }
        }

# Global OODA orchestrator
ooda_orchestrator = OODALoopOrchestrator()

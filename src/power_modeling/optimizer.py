"""
Power Optimization Recommender
Provides actionable recommendations to meet WLG power targets
"""
import json
import numpy as np
from typing import Dict, List
from power_model import PowerModel


class PowerOptimizer:
    """
    Analyzes current workload and recommends optimizations
    to meet power targets (e.g., 11W for WLG)
    """
    
    def __init__(self, model: PowerModel, target_power: float = 11.0):
        """
        Initialize optimizer
        
        Args:
            model: Trained PowerModel instance
            target_power: Target power limit in watts
        """
        self.model = model
        self.target_power = target_power
    
    def analyze_current_workload(self, read_mbps: float, write_mbps: float, waf: float) -> Dict:
        """
        Analyze current workload power consumption
        
        Args:
            read_mbps: Current read throughput
            write_mbps: Current write throughput
            waf: Current WAF
            
        Returns:
            Analysis dictionary with predictions and recommendations
        """
        current_power = self.model.predict(read_mbps, write_mbps, waf)
        
        analysis = {
            "current_workload": {
                "read_mbps": read_mbps,
                "write_mbps": write_mbps,
                "waf": waf,
                "predicted_power_watts": round(current_power, 2)
            },
            "target_power_watts": self.target_power,
            "power_delta_watts": round(current_power - self.target_power, 2),
            "within_target": current_power <= self.target_power,
            "recommendations": []
        }
        
        # If already within target, no optimization needed
        if analysis["within_target"]:
            analysis["recommendations"].append({
                "type": "success",
                "message": f"✅ Current power ({current_power:.2f}W) is within target ({self.target_power}W)"
            })
            return analysis
        
        # Generate optimization recommendations
        analysis["recommendations"] = self._generate_recommendations(
            read_mbps, write_mbps, waf, current_power
        )
        
        return analysis
    
    def _generate_recommendations(self, read_mbps: float, write_mbps: float, 
                                  waf: float, current_power: float) -> List[Dict]:
        """
        Generate specific optimization recommendations
        
        Returns:
            List of recommendation dictionaries
        """
        recommendations = []
        power_deficit = current_power - self.target_power
        
        coef = self.model.coefficients
        
        # Recommendation 1: Reduce writes
        if write_mbps > 0:
            # How much to reduce writes to hit target
            write_reduction_mbps = power_deficit / coef["write_coefficient"]
            write_reduction_pct = (write_reduction_mbps / write_mbps) * 100
            
            new_write = max(0, write_mbps - write_reduction_mbps)
            new_power = self.model.predict(read_mbps, new_write, waf)
            
            recommendations.append({
                "type": "write_reduction",
                "priority": "high",
                "action": f"Reduce write throughput by {write_reduction_pct:.1f}%",
                "details": f"From {write_mbps:.0f} MB/s to {new_write:.0f} MB/s",
                "estimated_power": round(new_power, 2),
                "power_saving": round(current_power - new_power, 2)
            })
        
        # Recommendation 2: Improve WAF
        if waf > 1.5:
            # Target WAF improvement
            target_waf = 1.5
            waf_delta = waf - target_waf
            power_saved_from_waf = waf_delta * coef["waf_coefficient"]
            
            new_power = self.model.predict(read_mbps, write_mbps, target_waf)
            
            recommendations.append({
                "type": "waf_optimization",
                "priority": "medium",
                "action": f"Optimize WAF from {waf:.2f} to {target_waf}",
                "details": "Improve garbage collection efficiency",
                "estimated_power": round(new_power, 2),
                "power_saving": round(power_saved_from_waf, 2)
            })
        
        # Recommendation 3: Mixed approach
        if write_mbps > 0 and waf > 1.5:
            # Reduce writes by 10% and improve WAF by 0.3
            new_write = write_mbps * 0.9
            new_waf = max(1.0, waf - 0.3)
            new_power = self.model.predict(read_mbps, new_write, new_waf)
            
            if new_power <= self.target_power:
                recommendations.append({
                    "type": "combined",
                    "priority": "recommended",
                    "action": "Combined optimization approach",
                    "details": f"Reduce writes 10% + improve WAF to {new_waf:.2f}",
                    "estimated_power": round(new_power, 2),
                    "power_saving": round(current_power - new_power, 2)
                })
        
        return recommendations
    
    def print_analysis(self, analysis: Dict) -> None:
        """Pretty print analysis results"""
        print("\n" + "="*70)
        print("⚡ POWER OPTIMIZATION ANALYSIS")
        print("="*70)
        
        # Current state
        wl = analysis["current_workload"]
        print(f"\n📊 Current Workload:")
        print(f"   Read:  {wl['read_mbps']:.0f} MB/s")
        print(f"   Write: {wl['write_mbps']:.0f} MB/s")
        print(f"   WAF:   {wl['waf']:.2f}")
        print(f"\n⚡ Predicted Power: {wl['predicted_power_watts']:.2f}W")
        print(f"   Target Power:    {analysis['target_power_watts']:.2f}W")
        
        if analysis["within_target"]:
            print(f"   Status: ✅ PASS (within target)")
        else:
            print(f"   Status: ❌ FAIL ({analysis['power_delta_watts']:.2f}W over target)")
        
        # Recommendations
        if analysis["recommendations"]:
            print(f"\n💡 Optimization Recommendations:")
            for i, rec in enumerate(analysis["recommendations"], 1):
                print(f"\n   {i}. [{rec.get('priority', 'N/A').upper()}] {rec['action']}")
                print(f"      {rec['details']}")
                if 'estimated_power' in rec:
                    print(f"      → Estimated power: {rec['estimated_power']}W "
                          f"(saves {rec['power_saving']}W)")
        
        print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    # Load trained model
    model = PowerModel()
    model.load_model("power_model.pkl")
    
    # Create optimizer
    optimizer = PowerOptimizer(model, target_power=11.0)
    
    # Example: Current workload exceeds power target
    print("🔍 Example Scenario: Heavy write workload")
    analysis = optimizer.analyze_current_workload(
        read_mbps=2000,
        write_mbps=3000,  # High write load
        waf=2.5           # Poor WAF
    )
    
    optimizer.print_analysis(analysis)
    
    # Save analysis
    with open("optimization_report.json", 'w') as f:
        json.dump(analysis, f, indent=2)
    print("💾 Analysis saved to: optimization_report.json")

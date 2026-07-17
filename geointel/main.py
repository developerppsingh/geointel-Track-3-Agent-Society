"""
GeoIntel CLI
Usage:
  python main.py simulate --conflict "Iran vs Israel"
  python main.py simulate --conflict "Iran vs Israel" --verbose
  python main.py simulate --conflict "Iran vs Israel" --search
  python main.py simulate --conflict "Iran vs Israel" --verbose --search
  python main.py baseline --conflict "Iran vs Israel"
  python main.py query --country "Russia"
  python main.py query --pattern "overstretch"
  python main.py index
"""
import argparse
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def cmd_simulate(args):
    from config import DASHSCOPE_API_KEY
    if not DASHSCOPE_API_KEY:
        print("ERROR: DASHSCOPE_API_KEY not set.", file=sys.stderr)
        sys.exit(1)

    from simulate.engine import SimulationEngine
    print(f"\nSimulating: {args.conflict}\n")
    engine = SimulationEngine(verbose=args.verbose, enable_search=args.search, horizon=args.horizon)
    result = engine.run(args.conflict)
    _print_report(result, verbose=args.verbose)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"\nFull result saved to {args.output}")


def cmd_baseline(args):
    from config import DASHSCOPE_API_KEY
    if not DASHSCOPE_API_KEY:
        print("ERROR: DASHSCOPE_API_KEY not set.", file=sys.stderr)
        sys.exit(1)

    from agents.baseline import BaselineAgent
    agent = BaselineAgent()
    print(f"Running baseline for: {args.conflict}")
    result = agent.analyze(args.conflict)
    print(json.dumps(result, indent=2))


def cmd_query(args):
    from kb_loader import KnowledgeBase
    kb = KnowledgeBase()
    if args.country:
        results = kb.search_country(args.country)
        print(json.dumps(results, indent=2) if results else f"No country matching '{args.country}' found.")
    elif args.pattern:
        results = kb.search_patterns(args.pattern)
        print(json.dumps(results, indent=2) if results else f"No patterns matching '{args.pattern}' found.")
    else:
        print("Specify --country or --pattern")


def cmd_index(args):
    from kb_loader import KnowledgeBase
    kb = KnowledgeBase()
    s = kb.summary()
    print(f"\nKnowledge Base Index")
    print(f"  Countries:              {s['countries']}")
    print(f"  Conflicts:              {s['conflicts']}")
    print(f"  Patterns:               {s['patterns']}")
    print(f"  Demographics:           {s['demographics']}")
    print(f"  Religious/Cultural:     {s['religious_cultural']}")
    print(f"\nCountries: {', '.join(c.get('name','') for c in kb.countries)}")
    print(f"\nConflicts: {', '.join(c.get('name','') for c in kb.conflicts)}")
    print(f"\nPatterns: {', '.join(p.get('name','') for p in kb.patterns)}")
    print(f"\nReligious/Cultural: {', '.join(r.get('name','') for r in kb.religious_cultural)}")


def _print_report(result: dict, verbose: bool = False):
    from rich.console import Console
    from rich.table   import Table
    from rich.panel   import Panel
    from rich         import box
    console = Console()

    def pct(v):
        try:
            return f"{float(v)*100:.0f}%"
        except Exception:
            return str(v)

    conflict = result.get("conflict", "")
    console.print()
    console.rule(f"[bold yellow]CONFLICT SIMULATION: {conflict}[/bold yellow]")

    # Show web search status
    metrics = result.get("metrics", {})
    if metrics.get("web_search_enabled"):
        console.print(f"\n[dim]Web search enabled — all AI calls grounded in real-time results for '{conflict}'[/dim]")

    if verbose:
        dec = result.get("decomposition", {})
        if dec:
            console.print("\n[bold cyan]Task Decomposition[/bold cyan]")
            for key in ("historian_question", "strategist_question", "economist_question"):
                if key in dec:
                    label = key.replace("_question", "").title()
                    console.print(f"  [dim]{label}:[/dim] {dec[key]}")

    if verbose:
        console.print("\n[bold cyan]Round 1 — Independent Assessments[/bold cyan]")
        t = Table(box=box.SIMPLE, show_header=True)
        t.add_column("Agent", style="cyan", min_width=16)
        t.add_column("Prediction", min_width=35)
        t.add_column("Confidence", justify="center", min_width=10)
        t.add_column("Timeline", min_width=18)
        for agent, r in result.get("round1", {}).items():
            t.add_row(agent, str(r.get("prediction", ""))[:55], pct(r.get("confidence")), str(r.get("timeline", ""))[:25])
        console.print(t)

    disagreements = result.get("disagreements", [])
    if disagreements:
        console.print(f"\n[bold red]Disagreements Detected: {len(disagreements)}[/bold red]")
        for i, d in enumerate(disagreements, 1):
            a_str = " vs. ".join(d.get("agents", []))
            console.print(f"\n  [bold yellow]{i}. {d.get('topic', '')}[/bold yellow]")
            console.print(f"     Agents: {a_str}")
            console.print(f"     Stakes: {d.get('stakes', '')}")
            console.print()
            # Show both positions clearly
            agents = d.get("agents", [])
            pos1 = d.get("agent1_position", "")
            pos2 = d.get("agent2_position", "")
            if len(agents) >= 2:
                console.print(f"     [cyan]{agents[0]}:[/cyan]")
                console.print(f"       {pos1[:120]}")
                console.print()
                console.print(f"     [magenta]{agents[1]}:[/magenta]")
                console.print(f"       {pos2[:120]}")
            else:
                console.print(f"     Position 1: {pos1[:120]}")
                console.print(f"     Position 2: {pos2[:120]}")

        # Show how each agent responded in Round 2
        round2 = result.get("round2", {})
        if round2:
            console.print(f"\n[bold cyan]Round 2 — Cross-Examination Responses[/bold cyan]")
            for agent_name, r2 in round2.items():
                changed = r2.get("position_changed", False)
                if changed:
                    icon = "[yellow]REVISED[/yellow]"
                else:
                    icon = "[green]HELD FIRM[/green]"
                console.print(f"\n  [{icon}]  [bold]{agent_name}[/bold]")
                rebuttal = r2.get("rebuttal", "")
                change_reason = r2.get("change_reason", "")
                revised_pred = r2.get("revised_prediction", "")
                if rebuttal:
                    console.print(f"     Rebuttal: {rebuttal[:200]}")
                if change_reason:
                    console.print(f"     Reason: {change_reason[:200]}")
                if revised_pred:
                    console.print(f"     Revised prediction: {revised_pred[:150]}")
                console.print(f"     Confidence: {pct(r2.get('confidence', 0))}")
    else:
        console.print("\n[green]No significant disagreements — strong consensus across agents.[/green]")

    if verbose:
        console.print("\n[bold cyan]Round 2 — Cross-Examination Results[/bold cyan]")
        for agent, r in result.get("round2", {}).items():
            changed = r.get("position_changed", False)
            icon = "[yellow]↻[/yellow]" if changed else "[green]✓[/green]"
            console.print(f"  {icon} {agent}: {'REVISED position' if changed else 'held position'}")
            if changed:
                console.print(f"     Reason: {r.get('change_reason', '')[:80]}")

    final = result.get("final", {})
    console.print()
    console.rule("[bold green]FINAL FORECAST[/bold green]")
    panel_text = (
        f"[bold]{final.get('outcome', 'No outcome generated')}[/bold]\n\n"
        f"Probability: [cyan]{pct(final.get('probability'))}[/cyan]   "
        f"Confidence: [cyan]{pct(final.get('confidence'))}[/cyan]\n"
        f"Timeline: {final.get('timeline', 'Unknown')}\n"
        f"Global Impact: {final.get('global_impact', '')[:120]}"
    )
    console.print(Panel(panel_text, title="Outcome", border_style="green"))

    pb = final.get("probability_breakdown", {})
    if pb:
        console.print("\n[cyan]Probability Breakdown:[/cyan]")
        for scenario, prob in pb.items():
            try:
                bar = "█" * int(float(prob) * 30) + "░" * (30 - int(float(prob) * 30))
                console.print(f"  {str(scenario)[:35]:<35} [{bar}] {pct(prob)}")
            except Exception:
                console.print(f"  {scenario}: {prob}")

    factors = final.get("key_factors", [])
    if factors:
        console.print("\n[cyan]Key Factors:[/cyan]")
        for f in factors[:8]:
            if isinstance(f, dict):
                wc = {"high": "red", "medium": "yellow", "low": "dim"}.get(f.get("weight", ""), "white")
                console.print(f"  [{wc}]●[/{wc}] {f.get('factor', '')[:70]} [dim]({f.get('source_agent', '')})[/dim]")
            else:
                console.print(f"  ● {str(f)[:70]}")

    metrics = result.get("metrics", {})
    console.print()
    console.rule("[bold blue]BASELINE vs. AGENT SOCIETY[/bold blue]")
    cmp = Table(box=box.ROUNDED, show_header=True, border_style="blue")
    cmp.add_column("Metric", style="cyan", min_width=28)
    cmp.add_column("Single Agent\n(no knowledge base)", justify="center", min_width=20)
    cmp.add_column("Agent Society\n(3 agents + debate)", justify="center", min_width=20)
    cmp.add_column("Delta", justify="center", min_width=10)

    bf = metrics.get("baseline_factors", 0)
    sf = metrics.get("society_factors", 0)
    bc = float(metrics.get("baseline_confidence", 0))
    sc = float(metrics.get("society_confidence", 0))

    cmp.add_row("Key factors identified", str(bf), str(sf), f"[green]+{sf-bf}[/green]" if sf > bf else str(sf-bf))
    cmp.add_row("Analytical dimensions", "1", "3", "[green]+2[/green]")
    cmp.add_row("Disagreements resolved", "0", str(metrics.get("disagreements_detected", 0)), "N/A")
    cmp.add_row("Positions revised via debate", "0", str(metrics.get("positions_changed", 0)), "N/A")
    cmp.add_row("Confidence", pct(bc), pct(sc), f"[green]+{(sc-bc)*100:.0f}pp[/green]" if sc > bc else f"{(sc-bc)*100:.0f}pp")
    cmp.add_row("Knowledge base used", "[red]No[/red]", "[green]Yes[/green]", "—")
    if metrics.get("web_search_enabled"):
        cmp.add_row("Web search", "—", "[green]Enabled (Qwen native)[/green]", "live")
    horizon = metrics.get("horizon", "long")
    if horizon != "long":
        horizon_labels = {"short": "0-30 days", "medium": "1-6 months"}
        cmp.add_row("Prediction horizon", "long", f"[green]{horizon_labels.get(horizon, horizon)}[/green]", "focused")
    console.print(cmp)
    console.print()


def main():
    parser = argparse.ArgumentParser(description="GeoIntel — Multi-Agent Geopolitical Intelligence")
    sub = parser.add_subparsers(dest="command")

    p_sim = sub.add_parser("simulate", help="Run full multi-agent simulation")
    p_sim.add_argument("--conflict", required=True, help='e.g. "Iran vs Israel 2026"')
    p_sim.add_argument("--verbose",  action="store_true", help="Show full debate transcript")
    p_sim.add_argument("--output",   help="Save full JSON result to file")
    p_sim.add_argument("--search",   action="store_true", help="Enable Qwen web search for real-time grounding")
    p_sim.add_argument("--horizon",  choices=["short", "medium", "long"], default="long", help="Prediction horizon: short (0-30 days), medium (1-6 months), long (6+ months)")

    p_base = sub.add_parser("baseline", help="Run single-agent baseline only")
    p_base.add_argument("--conflict", required=True)

    p_q = sub.add_parser("query", help="Query the knowledge base")
    p_q.add_argument("--country")
    p_q.add_argument("--pattern")

    sub.add_parser("index", help="List knowledge base contents")

    args = parser.parse_args()
    if args.command == "simulate":       cmd_simulate(args)
    elif args.command == "baseline":     cmd_baseline(args)
    elif args.command == "query":        cmd_query(args)
    elif args.command == "index":        cmd_index(args)
    else:                                parser.print_help()


if __name__ == "__main__":
    main()

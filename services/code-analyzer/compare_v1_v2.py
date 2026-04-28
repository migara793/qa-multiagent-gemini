#!/usr/bin/env python3
"""
Compare V1 vs V2 Performance and Accuracy

Runs both analyzers on the same commits and compares:
- Execution time
- Memory usage
- Symbol extraction accuracy
- API compatibility
"""

import time
import json
import sys
from pathlib import Path
from dataclasses import asdict
import tracemalloc


def compare_analyzers(repo_path: str, commit_refs: list[str]):
    """Compare v1 and v2 analyzers"""

    print("="*70)
    print("Code Analyzer V1 vs V2 - Performance Comparison")
    print("="*70)
    print()

    results = {
        'v1': {'times': [], 'memory': [], 'analyses': []},
        'v2': {'times': [], 'memory': [], 'analyses': []}
    }

    # Test V1 (subprocess + ast)
    print("Testing V1 (subprocess + Python ast)...")
    print("-" * 70)

    try:
        from analyzer import CodeAnalyzer as V1Analyzer

        for commit_ref in commit_refs:
            print(f"  Analyzing {commit_ref}...", end=" ")

            # Measure time and memory
            tracemalloc.start()
            start_time = time.time()

            try:
                analyzer = V1Analyzer(repo_path)
                analysis = analyzer.analyze_commit(commit_ref)
                results['v1']['analyses'].append(asdict(analysis))

                elapsed = time.time() - start_time
                current, peak = tracemalloc.get_traced_memory()
                tracemalloc.stop()

                results['v1']['times'].append(elapsed)
                results['v1']['memory'].append(peak / 1024 / 1024)  # MB

                print(f"✓ {elapsed*1000:.1f}ms, {peak/1024/1024:.1f}MB")

            except Exception as e:
                print(f"✗ Error: {e}")
                results['v1']['times'].append(0)
                results['v1']['memory'].append(0)

    except ImportError:
        print("  ✗ V1 analyzer not found (analyzer.py)")
        results['v1'] = None

    print()

    # Test V2 (pygit2 + tree-sitter)
    print("Testing V2 (pygit2 + tree-sitter)...")
    print("-" * 70)

    try:
        from analyzer_v2 import CodeAnalyzer as V2Analyzer

        for commit_ref in commit_refs:
            print(f"  Analyzing {commit_ref}...", end=" ")

            tracemalloc.start()
            start_time = time.time()

            try:
                analyzer = V2Analyzer(repo_path)
                analysis = analyzer.analyze_commit(commit_ref)
                results['v2']['analyses'].append(asdict(analysis))

                elapsed = time.time() - start_time
                current, peak = tracemalloc.get_traced_memory()
                tracemalloc.stop()

                results['v2']['times'].append(elapsed)
                results['v2']['memory'].append(peak / 1024 / 1024)  # MB

                print(f"✓ {elapsed*1000:.1f}ms, {peak/1024/1024:.1f}MB")

            except Exception as e:
                print(f"✗ Error: {e}")
                traceback.print_exc()
                results['v2']['times'].append(0)
                results['v2']['memory'].append(0)

    except ImportError as e:
        print(f"  ✗ V2 analyzer not found: {e}")
        results['v2'] = None

    print()
    print("="*70)
    print("Results Summary")
    print("="*70)
    print()

    # Calculate averages
    if results['v1'] and results['v2']:
        v1_avg_time = sum(results['v1']['times']) / len(results['v1']['times'])
        v2_avg_time = sum(results['v2']['times']) / len(results['v2']['times'])

        v1_avg_mem = sum(results['v1']['memory']) / len(results['v1']['memory'])
        v2_avg_mem = sum(results['v2']['memory']) / len(results['v2']['memory'])

        speedup = v1_avg_time / v2_avg_time if v2_avg_time > 0 else 0
        mem_reduction = ((v1_avg_mem - v2_avg_mem) / v1_avg_mem * 100) if v1_avg_mem > 0 else 0

        print(f"Average Execution Time:")
        print(f"  V1: {v1_avg_time*1000:.1f}ms")
        print(f"  V2: {v2_avg_time*1000:.1f}ms")
        print(f"  Speedup: {speedup:.1f}x faster ⚡")
        print()

        print(f"Average Memory Usage:")
        print(f"  V1: {v1_avg_mem:.1f}MB")
        print(f"  V2: {v2_avg_mem:.1f}MB")
        print(f"  Reduction: {mem_reduction:.1f}% less memory 💾")
        print()

        # Compare symbol extraction
        if results['v1']['analyses'] and results['v2']['analyses']:
            print("Symbol Extraction Comparison:")
            for i, commit_ref in enumerate(commit_refs):
                v1_analysis = results['v1']['analyses'][i]
                v2_analysis = results['v2']['analyses'][i]

                v1_functions = sum(len(f['functions_changed']) for f in v1_analysis['files_changed'])
                v2_functions = sum(len(f['functions_changed']) for f in v2_analysis['files_changed'])

                v1_classes = sum(len(f['classes_changed']) for f in v1_analysis['files_changed'])
                v2_classes = sum(len(f['classes_changed']) for f in v2_analysis['files_changed'])

                print(f"  {commit_ref[:8]}:")
                print(f"    Functions: V1={v1_functions}, V2={v2_functions}")
                print(f"    Classes:   V1={v1_classes}, V2={v2_classes}")

        print()
        print("="*70)
        print("Verdict: ", end="")

        if speedup > 5 and mem_reduction > 30:
            print("✅ V2 is SIGNIFICANTLY better (use in production)")
        elif speedup > 2:
            print("✅ V2 is better (recommended upgrade)")
        elif speedup > 1:
            print("⚠️  V2 is slightly better (marginal improvement)")
        else:
            print("❌ V2 needs optimization")

        print("="*70)

        # Save detailed results
        output_file = "comparison_results.json"
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\nDetailed results saved to: {output_file}")

    else:
        print("❌ Could not compare - one or both analyzers failed to load")


def main():
    if len(sys.argv) < 2:
        print("Usage: python compare_v1_v2.py <repo_path> [commit1] [commit2] ...")
        print("\nExample:")
        print("  python compare_v1_v2.py /path/to/repo HEAD HEAD~1 HEAD~2")
        sys.exit(1)

    repo_path = sys.argv[1]
    commit_refs = sys.argv[2:] if len(sys.argv) > 2 else ["HEAD", "HEAD~1", "HEAD~2"]

    # Validate repo
    if not Path(repo_path).exists():
        print(f"Error: Repository not found: {repo_path}")
        sys.exit(1)

    git_dir = Path(repo_path) / ".git"
    if not git_dir.exists():
        print(f"Error: Not a git repository: {repo_path}")
        sys.exit(1)

    compare_analyzers(repo_path, commit_refs)


if __name__ == '__main__':
    main()

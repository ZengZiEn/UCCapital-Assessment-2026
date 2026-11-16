"""
題目一主程式入口 (main.py)
完整展示：
1. 雙演算法求解器 (Bitmask+MRV 與 Dinic 最大流) 求解初始排班與耗時比較
2. 枚舉範例全部 18 組可行班表並進行魯棒性 (Robustness) 評分排序
3. 建立 O(1) 預計算突發應變查找表，完整印出所有「某員工臨時某天不能上」之調度結果
"""

import time
from .models import ScheduleConfig
from .solvers import BitmaskMRVSolver, MaxFlowDinicSolver
from .contingency import RobustScheduleSelector, ContingencyTable


def run_demonstration() -> str:
    """執行完整題目一展示流程並回傳格式化報告字串。"""
    lines = []
    lines.append("=" * 80)
    lines.append("UC Capital 面試考題 — 題目一：員工排班與突發狀況動態應變系統")
    lines.append("=" * 80)

    config = ScheduleConfig.create_default_uc_example()
    lines.append("\n【一、輸入員工與可用工作日設定】")
    for emp in config.employees:
        days_str = ", ".join(d.label for d in emp.available_days)
        lines.append(
            f"  - 員工 {emp.name}: 可上班日 = [{days_str}] "
            f"(5-bit Mask = 0b{emp.availability_mask:05b})"
        )
    lines.append(f"  - 每位員工每週上限: {config.max_days_per_employee} 天")

    # 1. 雙引擎求解器展示
    lines.append("\n【二、雙核心演算法初始排班求解】")
    t0 = time.perf_counter()
    mrv_solver = BitmaskMRVSolver(config)
    mrv_schedule = mrv_solver.solve_one()
    t_mrv = (time.perf_counter() - t0) * 1e6

    t1 = time.perf_counter()
    dinic_solver = MaxFlowDinicSolver(config)
    dinic_schedule = dinic_solver.solve()
    t_dinic = (time.perf_counter() - t1) * 1e6

    assert mrv_schedule is not None and dinic_schedule is not None
    lines.append(
        f"  1. [Bitmask + MRV 啟發式回溯法] 耗時: {t_mrv:.2f} us | "
        f"展開節點數: {mrv_solver.last_nodes_explored}"
    )
    lines.append(f"     -> 班表結果: {mrv_schedule.format_compact()}")
    lines.append(
        f"     -> 員工工時: {mrv_schedule.get_workload_summary(config)}"
    )

    lines.append(f"  2. [Dinic 網路最大流演算法]     耗時: {t_dinic:.2f} us")
    lines.append(f"     -> 班表結果: {dinic_schedule.format_compact()}")
    lines.append(
        f"     -> 員工工時: {dinic_schedule.get_workload_summary(config)}"
    )

    # 2. 全解枚舉與魯棒性分析
    lines.append("\n【三、全解空間枚舉與突發容錯魯棒性 (Robustness) 排行】")
    selector = RobustScheduleSelector(config)
    reports = selector.evaluate_all_schedules()
    lines.append(f"  * 總共枚舉出 {len(reports)} 組完全合法的初始班表。")
    lines.append("  * 以下列出韌性最高的前 5 組推薦班表（遭遇臨時請假時，平均變動天數最少）：")
    for idx, rep in enumerate(reports[:5], start=1):
        lines.append(
            f"    Top {idx}: [{rep.schedule.format_compact()}] | "
            f"請假可修復率: {rep.recoverable_count}/{rep.total_active_assignments} (100%) | "
            f"1-Hop直接代班: {rep.one_hop_count}次, 2-Hop換班: {rep.two_hop_count}次 | "
            f"平均變動: {rep.avg_perturbation_when_scheduled:.2f} 天"
        )

    best_schedule = reports[0].schedule
    lines.append(f"\n  => 系統選定最佳基準班表 (Baseline): [{best_schedule.format_compact()}]")

    # 3. 預計算 O(1) 突發應變查找表完整展示
    lines.append("\n【四、突發狀況：『某員工臨時說某一天不能上了』完整應變查找表 (O(1) Lookup)】")
    lut = ContingencyTable(config, best_schedule)
    lines.append(
        f"  {'請假事件':<14} | {'原班表是否排班':<14} | {'應變類型':<32} | {'調度動作與新班表'}"
    )
    lines.append("  " + "-" * 105)
    for res in lut.all_entries:
        event_str = f"{res.absent_employee} 禁上 {res.absent_day.label}"
        scheduled_str = "是 (需調度)" if res.was_scheduled else "否 (無影響)"
        assert res.repaired_schedule is not None
        if not res.was_scheduled:
            detail_str = f"維持原班表 [{res.repaired_schedule.format_compact()}]"
        else:
            steps_str = "; ".join(res.action_steps)
            detail_str = f"調整({steps_str}) => 新班表 [{res.repaired_schedule.format_compact()}]"
        lines.append(
            f"  {event_str:<14} | {scheduled_str:<14} | {res.repair_type:<32} | {detail_str}"
        )

    lines.append("\n" + "=" * 80)
    return "\n".join(lines)


if __name__ == "__main__":
    print(run_demonstration())


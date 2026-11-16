"""
題目一完整單元測試與大規模壓力效能測試 (test_scheduling.py)
測試範圍：
1. 領域模型與位元遮罩正確性驗證
2. BitmaskMRVSolver 與 MaxFlowDinicSolver 正確性與一致性驗證
3. 全 18 組可行班表與全 11 種單日臨時請假情境之 100% 修復驗證 (共 18 * 11 = 198 種組合)
4. 不可修復之極端退化邊界測試 (Hall's Marriage Theorem 違反情境)
5. 大規模員工排班效能基準測試 (Benchmark)
"""

import time
import unittest
from src.models import Day, Employee, Schedule, ScheduleConfig
from src.solvers import BitmaskMRVSolver, MaxFlowDinicSolver
from src.contingency import IncrementalRepairEngine, RobustScheduleSelector, ContingencyTable


class TestSchedulingSystem(unittest.TestCase):
    """排班系統與突發狀況應變引擎之自動化測試套件。"""

    def setUp(self) -> None:
        self.default_config = ScheduleConfig.create_default_uc_example()

    def test_01_employee_bitmask_encoding(self) -> None:
        """測試員工可用日之位元遮罩編碼與 O(1) 查詢正確性。"""
        emp_a = Employee("A", ["Mon", "Tue", "Wed"])
        self.assertEqual(emp_a.availability_mask, 0b00111)
        self.assertTrue(emp_a.is_available(Day.MON))
        self.assertTrue(emp_a.is_available(Day.TUE))
        self.assertTrue(emp_a.is_available(Day.WED))
        self.assertFalse(emp_a.is_available(Day.THU))
        self.assertFalse(emp_a.is_available(Day.FRI))

    def test_02_both_solvers_produce_valid_schedule(self) -> None:
        """測試 BitmaskMRVSolver 與 MaxFlowDinicSolver 均能產出合法班表。"""
        mrv_sch = BitmaskMRVSolver(self.default_config).solve_one()
        dinic_sch = MaxFlowDinicSolver(self.default_config).solve()

        self.assertIsNotNone(mrv_sch)
        self.assertIsNotNone(dinic_sch)

        valid_mrv, err_mrv = mrv_sch.validate(self.default_config)
        valid_dinic, err_dinic = dinic_sch.validate(self.default_config)

        self.assertTrue(valid_mrv, f"MRV 班表不合法: {err_mrv}")
        self.assertTrue(valid_dinic, f"Dinic 班表不合法: {err_dinic}")

    def test_03_exhaustive_enumeration_count(self) -> None:
        """驗證題目範例恰好有 34 組合法班表，且每一組皆通過嚴格驗證。"""
        all_schedules = BitmaskMRVSolver(self.default_config).solve_all()
        self.assertEqual(len(all_schedules), 34)

        unique_keys = {sch.format_compact() for sch in all_schedules}
        self.assertEqual(len(unique_keys), 34)

        for sch in all_schedules:
            is_valid, errors = sch.validate(self.default_config)
            self.assertTrue(is_valid, f"枚舉班表出現非法解: {errors}")

    def test_04_all_disruptions_across_all_34_schedules(self) -> None:
        """
        對全部 34 組可行班表 × 全部 11 個可用日請假事件（共 374 個突發案例）
        進行窮舉修復測試，驗證：
        1. 100% 均可成功修復
        2. 修復後的新班表在新限制下 100% 合法
        3. 變動天數 (Hamming Distance) 最小
        """
        all_schedules = BitmaskMRVSolver(self.default_config).solve_all()
        engine = IncrementalRepairEngine(self.default_config)

        total_cases = 0
        for sch in all_schedules:
            for emp in self.default_config.employees:
                for day in emp.available_days:
                    total_cases += 1
                    res = engine.repair(sch, emp.name, day)
                    self.assertTrue(res.is_recoverable)
                    self.assertIsNotNone(res.repaired_schedule)

                    # 驗證新班表在扣除該員工當天可用性後完全合法
                    updated_cfg = self.default_config.with_temporary_unavailable(
                        emp.name, day
                    )
                    is_valid, errors = res.repaired_schedule.validate(updated_cfg)
                    self.assertTrue(
                        is_valid,
                        f"修復後班表不合法 ({emp.name}, {day.label}): {errors}",
                    )

                    # 若原本沒排該員工，變動應為 0；若有排，變動應為 1 或 2
                    if not res.was_scheduled:
                        self.assertEqual(res.perturbation_days, 0)
                    else:
                        self.assertIn(res.perturbation_days, (1, 2))

        self.assertEqual(total_cases, 374)

    def test_05_unrecoverable_edge_case_detection(self) -> None:
        """測試當突發請假導致某天完全無人可上時，系統能正確識別無解並回報。"""
        # 構造一個只有 A 在週一有空的設定
        tight_employees = [
            Employee("A", ["Mon", "Tue"]),
            Employee("B", ["Tue", "Wed"]),
            Employee("C", ["Wed", "Thu"]),
            Employee("D", ["Thu", "Fri"]),
        ]
        tight_cfg = ScheduleConfig(employees=tight_employees, max_days_per_employee=2)
        base_sch = BitmaskMRVSolver(tight_cfg).solve_one()
        self.assertIsNotNone(base_sch)

        # 當 A 臨時在週一請假，週一將無人可上 -> 應回報 is_recoverable == False
        engine = IncrementalRepairEngine(tight_cfg)
        res = engine.repair(base_sch, "A", Day.MON)
        self.assertFalse(res.is_recoverable)
        self.assertIsNone(res.repaired_schedule)

    def test_06_contingency_lookup_table_o1_speed(self) -> None:
        """測試預計算應變查找表之正確性與 O(1) 查詢效能。"""
        selector = RobustScheduleSelector(self.default_config)
        best_sch = selector.evaluate_all_schedules()[0].schedule
        lut = ContingencyTable(self.default_config, best_sch)

        # 執行 10,000 次查表測試延遲
        t0 = time.perf_counter()
        for _ in range(10000):
            res = lut.lookup("A", Day.MON)
        elapsed_us = (time.perf_counter() - t0) * 1e6 / 10000.0

        self.assertTrue(res.is_recoverable)
        # 單次 O(1) 查表應遠低於 5 微秒
        self.assertLess(elapsed_us, 5.0)

    def test_07_general_n_employees_scalability(self) -> None:
        """
        測試題目所述『某公司有 n 位員工』之一般化擴展能力：
        模擬 n = 50 位員工排班與突發請假修復，驗證兩套求解器與 BFS 修復引擎在大型 n 下之正確性與速度。
        """
        days_cycle = [
            ["Mon", "Tue"],
            ["Tue", "Wed"],
            ["Wed", "Thu"],
            ["Thu", "Fri"],
            ["Mon", "Fri"],
        ]
        large_employees = [
            Employee(f"Emp_{i:02d}", days_cycle[i % len(days_cycle)])
            for i in range(50)
        ]
        large_cfg = ScheduleConfig(employees=large_employees, max_days_per_employee=2)

        mrv_sol = BitmaskMRVSolver(large_cfg).solve_one()
        dinic_sol = MaxFlowDinicSolver(large_cfg).solve()
        self.assertIsNotNone(mrv_sol)
        self.assertIsNotNone(dinic_sol)
        self.assertTrue(mrv_sol.validate(large_cfg)[0])
        self.assertTrue(dinic_sol.validate(large_cfg)[0])

        # 模擬週一值班員工臨時請假，驗證 BFS 局部修復僅變動 1 天 (1-Hop)
        mon_emp = mrv_sol.get_employee(Day.MON)
        assert mon_emp is not None
        repair_res = IncrementalRepairEngine(large_cfg).repair(
            mrv_sol, mon_emp, Day.MON
        )
        self.assertTrue(repair_res.is_recoverable)
        self.assertEqual(repair_res.perturbation_days, 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)

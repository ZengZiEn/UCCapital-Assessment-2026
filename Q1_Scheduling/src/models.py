"""
領域模型層 (models.py)
定義星期列舉、員工可用性位元遮罩模型、排班規則設定，以及班表實體與合法性驗證器。
"""

from dataclasses import dataclass, field
from enum import IntEnum
from typing import Dict, Iterable, List, Optional, Set, Tuple


class Day(IntEnum):
    """
    一週上班日列舉 (Mon ~ Fri)。
    繼承自 IntEnum，可直接作為陣列索引 (0 ~ 4) 或用於位元遮罩運算 (1 << day)。
    """
    MON = 0
    TUE = 1
    WED = 2
    THU = 3
    FRI = 4

    @property
    def label(self) -> str:
        """回傳題目標準英文縮寫名稱 (Mon, Tue, Wed, Thu, Fri)。"""
        labels = ("Mon", "Tue", "Wed", "Thu", "Fri")
        return labels[int(self)]

    @classmethod
    def from_str(cls, text: str) -> "Day":
        """由字串（不分大小寫，如 'Mon', 'tue'）轉換為 Day 列舉。"""
        mapping = {
            "mon": cls.MON,
            "tue": cls.TUE,
            "wed": cls.WED,
            "thu": cls.THU,
            "fri": cls.FRI,
        }
        key = text.strip().lower()[:3]
        if key not in mapping:
            raise ValueError(f"無法識別的星期名稱: {text!r}")
        return mapping[key]


@dataclass(frozen=True)
class Employee:
    """
    員工實體模型。
    在初始化時自動將可上班日預編譯為位元遮罩 (availability_mask)，
    使可用性查詢可在 O(1) 位元運算內完成。
    """
    name: str
    available_days: Tuple[Day, ...]
    availability_mask: int = field(init=False)

    def __init__(self, name: str, available_days: Iterable[Day | str]) -> None:
        parsed_days: List[Day] = []
        for d in available_days:
            day_enum = Day.from_str(d) if isinstance(d, str) else Day(d)
            if day_enum not in parsed_days:
                parsed_days.append(day_enum)
        parsed_days.sort()

        object.__setattr__(self, "name", name)
        object.__setattr__(self, "available_days", tuple(parsed_days))

        mask = 0
        for d in parsed_days:
            mask |= (1 << int(d))
        object.__setattr__(self, "availability_mask", mask)

    def is_available(self, day: Day) -> bool:
        """以 O(1) 位元運算判斷該員工在指定日期是否有空。"""
        return bool((self.availability_mask >> int(day)) & 1)

    def without_day(self, unavailable_day: Day) -> "Employee":
        """
        回傳移除某一天可用性後的新 Employee 實體（不可變設計，用於模擬臨時請假）。
        """
        filtered = [d for d in self.available_days if d != unavailable_day]
        return Employee(name=self.name, available_days=filtered)


@dataclass(frozen=True)
class ScheduleConfig:
    """
    排班問題之規則與環境設定。
    預設為一週五天 (Mon ~ Fri)，且每人每週最多上班 2 天。
    """
    employees: Tuple[Employee, ...]
    required_days: Tuple[Day, ...] = (Day.MON, Day.TUE, Day.WED, Day.THU, Day.FRI)
    max_days_per_employee: int = 2

    def __init__(
        self,
        employees: Iterable[Employee],
        required_days: Iterable[Day] = (Day.MON, Day.TUE, Day.WED, Day.THU, Day.FRI),
        max_days_per_employee: int = 2,
    ) -> None:
        emp_tuple = tuple(employees)
        if not emp_tuple:
            raise ValueError("員工清單不可為空")
        if max_days_per_employee <= 0:
            raise ValueError("每位員工最大上班天數必須大於 0")

        object.__setattr__(self, "employees", emp_tuple)
        object.__setattr__(self, "required_days", tuple(sorted(set(required_days))))
        object.__setattr__(self, "max_days_per_employee", max_days_per_employee)

    @property
    def employee_map(self) -> Dict[str, Employee]:
        """以員工姓名為鍵的快速查找字典。"""
        return {emp.name: emp for emp in self.employees}

    def with_temporary_unavailable(self, emp_name: str, day: Day) -> "ScheduleConfig":
        """
        產生當某位員工臨時在某天不能上班時的新排班設定。
        """
        new_employees: List[Employee] = []
        found = False
        for emp in self.employees:
            if emp.name == emp_name:
                found = True
                new_employees.append(emp.without_day(day))
            else:
                new_employees.append(emp)
        if not found:
            raise KeyError(f"找不到員工: {emp_name!r}")
        return ScheduleConfig(
            employees=new_employees,
            required_days=self.required_days,
            max_days_per_employee=self.max_days_per_employee,
        )

    @classmethod
    def create_default_uc_example(cls) -> "ScheduleConfig":
        """
        建立 UC Capital 考題投影片第 2 頁之標準範例設定：
        A：Mon, Tue, Wed
        B：Mon, Thu, Fri
        C：Tue, Wed, Thu
        D：Tue, Fri
        """
        employees = [
            Employee("A", ["Mon", "Tue", "Wed"]),
            Employee("B", ["Mon", "Thu", "Fri"]),
            Employee("C", ["Tue", "Wed", "Thu"]),
            Employee("D", ["Tue", "Fri"]),
        ]
        return cls(employees=employees, max_days_per_employee=2)


@dataclass(frozen=True)
class Schedule:
    """
    排班結果班表實體。
    儲存每個工作日指派的員工姓名，並提供合法性驗證與差異比較方法。
    """
    assignments: Dict[Day, str]

    def get_employee(self, day: Day) -> Optional[str]:
        """取得指定工作日的排班員工姓名。"""
        return self.assignments.get(day)

    def get_employee_workdays(self, emp_name: str) -> List[Day]:
        """取得指定員工在此班表中被排班的所有日期。"""
        return sorted([d for d, name in self.assignments.items() if name == emp_name])

    def get_workload_summary(self, config: Optional[ScheduleConfig] = None) -> Dict[str, int]:
        """統計每位員工被排班的總天數。"""
        counts: Dict[str, int] = {}
        if config is not None:
            for emp in config.employees:
                counts[emp.name] = 0
        for _, emp_name in self.assignments.items():
            counts[emp_name] = counts.get(emp_name, 0) + 1
        return counts

    def validate(self, config: ScheduleConfig) -> Tuple[bool, List[str]]:
        """
        嚴格驗證班表是否滿足所有硬性限制：
        1. Mon ~ Fri 每天都必須有 1 人上班。
        2. 排班員工必須在當天有空。
        3. 每位員工一週排班天數不得超過 max_days_per_employee (2 天)。
        """
        errors: List[str] = []
        emp_map = config.employee_map

        # 規則 1：檢查每天是否都有排班
        for day in config.required_days:
            if day not in self.assignments or not self.assignments[day]:
                errors.append(f"規則違反：{day.label} 沒有安排任何員工上班")
                continue

            emp_name = self.assignments[day]
            if emp_name not in emp_map:
                errors.append(f"規則違反：{day.label} 指派了不存在的員工 {emp_name!r}")
                continue

            # 規則 2：檢查該員工當天是否有空
            if not emp_map[emp_name].is_available(day):
                errors.append(f"規則違反：員工 {emp_name} 在 {day.label} 沒空，卻被排班")

        # 規則 3：檢查每位員工排班天數上限
        workload = self.get_workload_summary(config)
        for emp_name, count in workload.items():
            if count > config.max_days_per_employee:
                errors.append(
                    f"規則違反：員工 {emp_name} 一週排班 {count} 天，"
                    f"超過上限 {config.max_days_per_employee} 天"
                )

        return (len(errors) == 0, errors)

    def hamming_distance(self, other: "Schedule") -> int:
        """
        計算兩個班表之間指派人員不同的天數（漢明距離）。
        用於評估突發狀況重新排班時的「最小變動幅度 (Minimal Perturbation)」。
        """
        all_days: Set[Day] = set(self.assignments.keys()) | set(other.assignments.keys())
        return sum(
            1 for d in all_days if self.assignments.get(d) != other.assignments.get(d)
        )

    def diff_descriptions(self, other: "Schedule") -> List[str]:
        """回傳從 self 班表調整為 other 班表的具體變動說明清單。"""
        diffs: List[str] = []
        for d in sorted(set(self.assignments.keys()) | set(other.assignments.keys())):
            old_emp = self.assignments.get(d, "無")
            new_emp = other.assignments.get(d, "無")
            if old_emp != new_emp:
                diffs.append(f"{d.label}: {old_emp} -> {new_emp}")
        return diffs

    def format_compact(self) -> str:
        """格式化為單行易讀字串，例如：Mon:A | Tue:D | Wed:C | Thu:B | Fri:B"""
        parts = [f"{d.label}:{self.assignments[d]}" for d in sorted(self.assignments.keys())]
        return " | ".join(parts)


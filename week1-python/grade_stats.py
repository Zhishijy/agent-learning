"""成绩统计器 —— 演示类型注解、dataclass、边界表、计算与展示分离。"""

from dataclasses import dataclass
from statistics import mean


# ---------- 领域模型 ----------

@dataclass(frozen=True)  # frozen=True: 不可变对象，更安全，可做字典key
class StudentReport:
    name: str
    average: float
    grade: str
    needs_makeup: bool


# ---------- 纯逻辑层（不打印任何东西，方便测试和复用） ----------

def average(nums: list[float]) -> float:
    """计算平均分。空列表是非法输入，直接抛异常而不是返回0。"""
    if not nums:
        raise ValueError("成绩列表不能为空")
    return sum(nums) / len(nums)


# 边界表：(下限, 等级)，从高到低排列
# 新增规则（如A+）只需改这张表，不用动判断逻辑
_GRADE_BOUNDARIES: list[tuple[float, str]] = [
    (90, "A"),
    (80, "B"),
    (70, "C"),
    (60, "D"),
    (0,  "F"),
]


def letter_grade(score: float) -> str:
    """按平均分定等级。"""
    if not 0 <= score <= 100:
        raise ValueError(f"分数超出合法范围 0-100: {score}")
    for lower, grade in _GRADE_BOUNDARIES:
        if score >= lower:
            return grade
    return "F"  # 防御性兜底，正常逻辑走不到这里


def build_report(name: str, scores: list[float]) -> StudentReport:
    """把原始数据加工成一个学生的报告。"""
    avg = average(scores)
    return StudentReport(
        name=name,
        average=avg,                       # 内部保留完整精度
        grade=letter_grade(avg),
        needs_makeup=any(s < 60 for s in scores),  # any: 任一科不及格
    )


def class_average(reports: list[StudentReport]) -> float:
    if not reports:
        raise ValueError("学生报告列表为空")
    return mean(r.average for r in reports)


def find_extremes(
    reports: list[StudentReport],
) -> tuple[StudentReport, StudentReport]:
    """返回 (最高分学生, 最低分学生)。"""
    if not reports:
        raise ValueError("学生报告列表为空")
    top = max(reports, key=lambda r: r.average)
    bottom = min(reports, key=lambda r: r.average)
    return top, bottom


# ---------- 展示层（round只出现在这里） ----------

def print_reports(reports: list[StudentReport]) -> None:
    print(f"{'姓名':<6}{'均分':>6}  {'等级':<4}{'备注'}")
    print("-" * 28)
    for r in reports:
        note = "需补考" if r.needs_makeup else ""
        print(f"{r.name:<6}{r.average:>6.1f}  {r.grade:<4}{note}")

    print("-" * 28)
    print(f"班级总平均分：{class_average(reports):.1f}")
    top, bottom = find_extremes(reports)
    print(f"最高：{top.name}({top.average:.1f})  "
          f"最低：{bottom.name}({bottom.average:.1f})")


def main() -> None:
    raw_scores: dict[str, list[float]] = {
        "张三": [88, 76, 92],
        "李四": [59, 61, 70],
        "王五": [95, 91, 89],
    }
    reports = [build_report(name, scores)
               for name, scores in raw_scores.items()]
    print_reports(reports)


if __name__ == "__main__":
    main()

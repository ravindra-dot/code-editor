"""Optional Docker check for libraries preinstalled in the runner image."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from run_code import execute_code


PROGRAMS = [
    ("python", "import numpy as np; print(int(np.array([2, 3]).sum()))", "5"),
    ("python", "import pandas as pd; print(int(pd.Series([2, 3]).sum()))", "5"),
    ("python", "from PIL import Image; print(Image.new('RGB', (1, 1)).size)", "(1, 1)"),
    ("python", "import sympy; print(sympy.factor('x**2 - 1'))", "(x - 1)*(x + 1)"),
    ("python", "import matplotlib; print(matplotlib.__version__)", "3.10.3"),
    (
        "cpp",
        "#include <Eigen/Dense>\n#include <nlohmann/json.hpp>\n"
        "#include <iostream>\nint main() { Eigen::Vector2i v(2, 3); "
        "nlohmann::json j = {{\"sum\", v.sum()}}; std::cout << j[\"sum\"]; }",
        "5",
    ),
]


for language, code, expected in PROGRAMS:
    actual = execute_code(language, code, "")
    if actual != expected:
        raise AssertionError(f"{language} library check: expected {expected!r}, got {actual!r}")
    print(f"{language}: {expected} OK")

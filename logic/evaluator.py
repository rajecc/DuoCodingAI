from typing import List, Dict, Any

def run_python_code(code: str, test_cases_str: str) -> Dict[str, Any]:
    """
    Выполняет код и проверяет его ассертами. 
    Возвращает словарь с результатами.
    """
    exec_context = {}
    try:
        exec(code, exec_context)
    except Exception as e:
        return {
            "status": "error", 
            "message": f"{type(e).__name__}: {e}", 
            "passed": 0, 
            "total": 0,
            "results": []
        }
    test_lines = [line.strip() for line in test_cases_str.split('\n') if line.strip().startswith('assert')]
    passed = 0
    results = []

    for i, test in enumerate(test_lines, 1):
        try:
            exec(test, exec_context)
            passed += 1
            results.append({"name": f"Тест {i}", "passed": True})
        except AssertionError:
            results.append({"name": f"Тест {i}", "passed": False, "error": "AssertionError"})
        except Exception as e:
            results.append({"name": f"Тест {i}", "passed": False, "error": type(e).__name__})

    return {
        "status": "success",
        "passed": passed,
        "total": len(test_lines),
        "results": results
    }
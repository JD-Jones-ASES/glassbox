"""Golden traces for the multi-frame spine: function calls, returns, depth, recursion, default
arguments, and the implicit None when a function falls off its end.
"""

from glassbox_tracer.trace import trace

FIND_MAX = (
    "def find_max(nums):\n"
    "    best = nums[0]\n"
    "    for n in nums:\n"
    "        if n > best:\n"
    "            best = n\n"
    "    return best\n"
    "\n"
    "answer = find_max([3, 9, 4])\n"
)


def test_call_event_binds_arguments_and_return_carries_value():
    steps = trace(FIND_MAX)
    calls = [s for s in steps if s["event"] == "call"]
    returns = [s for s in steps if s["event"] == "return"]
    assert len(calls) == 1
    assert calls[0]["frame"] == "find_max" and calls[0]["depth"] == 1
    assert calls[0]["state"] == {"nums": [3, 9, 4]}  # parameters bound at the call
    assert len(returns) == 1 and returns[0]["return_value"] == 9


def test_assignment_lands_after_the_call_expands():
    steps = trace(FIND_MAX)
    last = steps[-1]
    assert last["event"] == "line" and "frame" not in last  # back at module level (depth 0)
    assert last["state"]["answer"] == 9
    ret_idx = next(i for i, s in enumerate(steps) if s["event"] == "return")
    assert ret_idx < len(steps) - 1  # def -> call -> compute -> return -> assignment lands


def test_module_lines_carry_no_frame_but_function_lines_do():
    steps = trace(FIND_MAX)
    fn_lines = [s for s in steps if s["event"] == "line" and s.get("frame") == "find_max"]
    assert fn_lines and all(s["depth"] == 1 for s in fn_lines)
    module_lines = [s for s in steps if s["event"] == "line" and "frame" not in s]
    assert len(module_lines) == 2  # the def line and the assignment line


RECUR = (
    "def fact(n):\n"
    "    if n <= 1:\n"
    "        return 1\n"
    "    return n * fact(n - 1)\n"
    "\n"
    "result = fact(3)\n"
)


def test_recursion_nests_depth_and_unwinds_values():
    steps = trace(RECUR)
    assert max(s.get("depth", 0) for s in steps) == 3  # fact(3)->fact(2)->fact(1)
    returns = [s["return_value"] for s in steps if s["event"] == "return"]
    assert returns == [1, 2, 6]  # innermost first, outermost (3! = 6) last
    assert steps[-1]["state"]["result"] == 6


DEFAULTS = (
    'def greet(name, greeting="Hi"):\n'
    '    return greeting + ", " + name\n'
    "\n"
    'a = greet("Sam")\n'
    'b = greet("Sam", "Hello")\n'
)


def test_default_argument_is_bound_at_the_call():
    steps = trace(DEFAULTS)
    calls = [s for s in steps if s["event"] == "call"]
    assert calls[0]["state"] == {"name": "Sam", "greeting": "Hi"}     # default used
    assert calls[1]["state"] == {"name": "Sam", "greeting": "Hello"}  # default overridden
    returns = [s["return_value"] for s in steps if s["event"] == "return"]
    assert returns == ["Hi, Sam", "Hello, Sam"]


NONE_RET = (
    "def first_positive(xs):\n"
    "    for x in xs:\n"
    "        if x > 0:\n"
    "            return x\n"
    "\n"
    "r = first_positive([-1, -2])\n"
)


def test_falling_off_the_end_returns_none():
    steps = trace(NONE_RET)
    returns = [s for s in steps if s["event"] == "return"]
    assert returns[-1]["return_value"] is None
    assert steps[-1]["state"]["r"] is None


RETURN_SET = (
    "def make():\n"
    "    return {2, 1}\n"
    "\n"
    "s = make()\n"
)


def test_return_value_coercion_reason_is_captured():
    # A non-JSON-native return value renders as a placeholder AND records WHY (previously the return
    # value's coercion flags were dropped on the floor).
    steps = trace(RETURN_SET)
    ret = [s for s in steps if s["event"] == "return"][0]
    assert ret["return_value"]["__unserializable__"] is True
    assert ret["return_value"]["__repr__"] == "{1, 2}"  # deterministic, sorted
    assert ret["value_flags"]["return_value"] == "repr-coerced"


def test_function_traces_are_deterministic():
    assert trace(FIND_MAX) == trace(FIND_MAX)
    assert trace(RECUR) == trace(RECUR)
    assert trace(RETURN_SET) == trace(RETURN_SET)

"""Pre-saved results for the demo samples (the Python / Java / C / C++ / Clean buttons).

Pressing a sample button, or pressing Roast on unchanged sample code, shows these
results instantly instead of calling the model, so a live demo never waits or
fails. They are written by hand, marked "Demo example" in the UI, and any edit to
the code makes the app go back to the real model.
"""
from __future__ import annotations

import labtools as L
import samples
from prompts import LEVELS, Bug, RoastResult

GENTLE, SARCASTIC, BRUTAL = LEVELS


def find_sample(code: str) -> str | None:
    """Name of the sample this exact code is, or None."""
    text = (code or "").strip()
    for name, sample in samples.SAMPLES.items():
        if text == sample.strip():
            return name
    return None


# --------------------------------------------------------------------------
# Roasts: bugs, fix and score are shared; the roast text changes with the level
# --------------------------------------------------------------------------
_BASE = {
    "Python": dict(
        language="Python",
        score=3,
        bugs=[
            Bug(line=3, issue="range(len(numbers) + 1) runs one step past the end, so numbers[i] raises IndexError on the last pass.",
                fix="Loop over the list itself: for n in numbers."),
            Bug(line=2, issue="biggest starts at 0, so a list of only negative numbers wrongly returns 0 instead of -2.",
                fix="Start from the first element: biggest = numbers[0]."),
            Bug(line=0, issue="An empty list is not handled and would crash or return a meaningless value.",
                fix="Raise a clear ValueError when the list is empty."),
        ],
        fixed_code=(
            "def find_max(numbers):\n"
            "    if not numbers:\n"
            '        raise ValueError("numbers must not be empty")\n'
            "    biggest = numbers[0]\n"
            "    for n in numbers[1:]:\n"
            "        if n > biggest:\n"
            "            biggest = n\n"
            "    return biggest\n"
            "\n"
            'if __name__ == "__main__":\n'
            "    print(find_max([-5, -2, -9]))\n"
        ),
    ),
    "Java": dict(
        language="Java",
        score=3,
        bugs=[
            Bug(line=8, issue="Removing from a list inside a for-each loop modifies it while it is being iterated, which throws ConcurrentModificationException.",
                fix="Use nums.removeIf(n -> n % 2 == 0) or build a new list of the numbers to keep."),
            Bug(line=8, issue="nums.remove(n) with an Integer calls remove(Object), which is easy to confuse with remove(int index).",
                fix="Avoid manual removal; removeIf states the intent and cannot mix up the two overloads."),
            Bug(line=12, issue="name is null, so name.length() throws NullPointerException.",
                fix="Check for null first, for example name == null ? 0 : name.length()."),
        ],
        fixed_code=(
            "import java.util.*;\n"
            "\n"
            "public class Main {\n"
            "    static List<Integer> removeEvens(List<Integer> nums) {\n"
            "        List<Integer> kept = new ArrayList<>(nums);\n"
            "        kept.removeIf(n -> n % 2 == 0);\n"
            "        return kept;\n"
            "    }\n"
            "\n"
            "    static int safeLength(String s) {\n"
            "        return s == null ? 0 : s.length();\n"
            "    }\n"
            "\n"
            "    public static void main(String[] args) {\n"
            "        List<Integer> nums = Arrays.asList(1, 2, 3, 4, 5, 6);\n"
            "        System.out.println(removeEvens(nums));\n"
            "        System.out.println(safeLength(null));\n"
            "    }\n"
            "}\n"
        ),
    ),
    "C": dict(
        language="C",
        score=2,
        bugs=[
            Bug(line=7, issue="gets() cannot limit its input, so any name longer than 7 characters overflows name[8]. It was removed from the C standard for this reason.",
                fix="Use fgets(name, sizeof name, stdin) and strip the newline."),
            Bug(line=9, issue="malloc(4 * sizeof(int)) holds indexes 0 to 3, so scores[4] writes past the end of the block.",
                fix="Allocate 5 ints, or write to scores[3]."),
            Bug(line=8, issue="The result of malloc is never checked, and the memory is never freed.",
                fix="Return an error if malloc gives NULL, and call free(scores) before returning."),
        ],
        fixed_code=(
            "#include <stdio.h>\n"
            "#include <stdlib.h>\n"
            "#include <string.h>\n"
            "\n"
            "void trim_newline(char *s) {\n"
            '    s[strcspn(s, "\\n")] = \'\\0\';\n'
            "}\n"
            "\n"
            "#ifndef TESTING\n"
            "int main(void) {\n"
            "    char name[8];\n"
            '    printf("Name: ");\n'
            "    if (fgets(name, sizeof name, stdin) == NULL) return 1;\n"
            "    trim_newline(name);\n"
            "    int *scores = malloc(5 * sizeof(int));\n"
            "    if (scores == NULL) return 1;\n"
            "    scores[4] = 100;\n"
            '    printf("Hi %s\\n", name);\n'
            "    free(scores);\n"
            "    return 0;\n"
            "}\n"
            "#endif\n"
        ),
    ),
    "C++": dict(
        language="C++",
        score=3,
        bugs=[
            Bug(line=5, issue="total is never initialised, so the sum starts from garbage and the result is undefined.",
                fix="Initialise it: int total = 0;"),
            Bug(line=12, issue="data.size() - 3 is 0 here, so the program divides by zero.",
                fix="Check that the divisor is not 0 before dividing."),
            Bug(line=4, issue="The vector is passed by value, so the whole thing is copied on every call.",
                fix="Take it by const reference: const std::vector<int>& v."),
        ],
        fixed_code=(
            "#include <iostream>\n"
            "#include <vector>\n"
            "\n"
            "int sum(const std::vector<int>& v) {\n"
            "    int total = 0;\n"
            "    for (int x : v) total += x;\n"
            "    return total;\n"
            "}\n"
            "\n"
            "#ifndef TESTING\n"
            "int main() {\n"
            "    std::vector<int> data = {1, 2, 3};\n"
            "    size_t divisor = data.size() - 3;\n"
            "    if (divisor == 0) {\n"
            '        std::cerr << "divisor is zero\\n";\n'
            "        return 1;\n"
            "    }\n"
            "    std::cout << sum(data) / divisor << std::endl;\n"
            "}\n"
            "#endif\n"
        ),
    ),
    "Clean": dict(
        language="Python",
        score=9,
        bugs=[],
        fixed_code=samples.SAMPLES["Clean"],
    ),
}

_TEXT = {
    "Python": {
        GENTLE: "Nice start! The idea is right: walk the list and remember the biggest value. Two small slips are hiding in it, though. The loop goes one step too far, and starting from 0 means a list of negatives gives the wrong answer. Both are quick fixes, and you will spot them faster every time.",
        SARCASTIC: "A loop that runs one step past the end of the list and a 'biggest' that starts at zero. So this finds the maximum of any list as long as it is not empty, not negative and not actually used. Bold design.",
        BRUTAL: "This function crashes on every input. The loop reads past the end of the list, and even if it did not, it would call 0 the biggest of a list of negatives. It is wrong twice in six lines, which takes real commitment.",
    },
    "Java": {
        GENTLE: "Good use of a list and a for-each loop. Two things to learn from here: Java does not allow changing a list while you loop over it, and a variable set to null cannot have its length asked for. removeIf and a null check solve both nicely.",
        SARCASTIC: "Removing items from a list while looping over it, then asking a null for its length. You managed a ConcurrentModificationException and a NullPointerException in thirteen lines. That is almost efficient.",
        BRUTAL: "This program is a crash with a main method. The loop dies as soon as it removes something, and if it survived, the next line would blow up on a null you created yourself on purpose.",
    },
    "C": {
        GENTLE: "You have the right pieces here: reading a name, allocating memory, printing a greeting. The details need care, though. gets() cannot protect your buffer, and the array you allocated is one slot too small for the write that follows. Swapping in fgets and sizing the block correctly will make this solid.",
        SARCASTIC: "gets() into an 8 byte buffer, then a write one slot past a 4 int allocation, then no free. It is a masterclass in the three most famous ways to corrupt memory, all before the program says hello.",
        BRUTAL: "This is a buffer overflow, a heap overflow and a memory leak sharing a main function. Any attacker with a long name owns your program, and you did not even free the memory they would have owned.",
    },
    "C++": {
        GENTLE: "Good instinct to put the summing in its own function! The total just needs a starting value, and passing the vector by reference will save a lot of copying. The last line also divides by zero, so a quick check before dividing will keep it safe.",
        SARCASTIC: "An uninitialised total, a vector copied by value, and a division by exactly zero at the end. The only thing this program reliably computes is how many ways it can go wrong.",
        BRUTAL: "The sum starts from whatever garbage was in memory, then the result is divided by zero. This is not undefined behaviour waiting to happen, it is undefined behaviour with a schedule.",
    },
    "Clean": {
        GENTLE: "This is lovely. Clear name, helpful docstring, type hints, and a tidy way of ignoring case and punctuation. There is very little to improve here, so keep writing code this way.",
        SARCASTIC: "I came here to roast and found a clean palindrome check with type hints and a docstring. Disappointing, really. Fine, it is good. Do not let it go to your head.",
        BRUTAL: "I have nothing nasty to say, which is annoying. It is short, readable, correct and documented. If you wrote this on purpose, well done. If it was luck, do not tell anyone.",
    },
}


def demo_roast(name: str, level: str) -> RoastResult:
    base = _BASE[name]
    text = _TEXT[name].get(level) or _TEXT[name][SARCASTIC]
    return RoastResult(
        language=base["language"], roast=text, bugs=list(base["bugs"]),
        fixed_code=base["fixed_code"], score=base["score"],
    )


# --------------------------------------------------------------------------
# Lab tools
# --------------------------------------------------------------------------
def _metrics(scores, comments):
    return [L.Metric(name=n, score=s, comment=c) for n, s, c in zip(L.REPORT_METRICS, scores, comments)]


_LAB = {
    "Python": {
        "oop": L.OOPResult(
            summary="The function is split into a small family of finder classes. An abstract Finder fixes the interface, and each concrete class decides what 'best' means.",
            classes=[
                L.ClassInfo(name="Finder", kind="abstract class", responsibility="Declares find(numbers) that every finder must provide.", relationships=""),
                L.ClassInfo(name="MaxFinder", kind="class", responsibility="Returns the largest number.", relationships="extends Finder"),
                L.ClassInfo(name="MinFinder", kind="class", responsibility="Returns the smallest number.", relationships="extends Finder"),
            ],
            concepts=[
                L.ConceptUse(concept="Abstraction", where="Finder", why="Callers only need find(); they do not care how the answer is found."),
                L.ConceptUse(concept="Inheritance", where="MaxFinder, MinFinder", why="Both reuse the Finder contract and the shared empty-list rule."),
                L.ConceptUse(concept="Polymorphism", where="find()", why="The same call gives the maximum or the minimum depending on the object."),
            ],
            diagram="        Finder (abstract)\n        + find(numbers)\n          ^           ^\n          |           |\n   MaxFinder      MinFinder\n   + find()       + find()",
            refactored_code=(
                "from abc import ABC, abstractmethod\n\n\n"
                "class Finder(ABC):\n"
                "    def find(self, numbers):\n"
                "        if not numbers:\n"
                '            raise ValueError("numbers must not be empty")\n'
                "        return self._pick(numbers)\n\n"
                "    @abstractmethod\n"
                "    def _pick(self, numbers):\n"
                "        ...\n\n\n"
                "class MaxFinder(Finder):\n"
                "    def _pick(self, numbers):\n"
                "        return max(numbers)\n\n\n"
                "class MinFinder(Finder):\n"
                "    def _pick(self, numbers):\n"
                "        return min(numbers)\n\n\n"
                "for finder in (MaxFinder(), MinFinder()):\n"
                "    print(finder.find([-5, -2, -9]))\n"
            ),
            notes="The off-by-one loop and the 0 starting value are gone. For a function this small, classes are mostly a design exercise.",
        ),
        "tests": L.UnitTestsResult(
            framework="unittest (standard library)",
            test_code=(
                "import unittest\n"
                "from solution import find_max\n\n\n"
                "class FindMaxTests(unittest.TestCase):\n"
                "    def test_positive_numbers(self):\n"
                "        self.assertEqual(find_max([3, 9, 4]), 9)\n\n"
                "    def test_all_negative(self):\n"
                "        self.assertEqual(find_max([-5, -2, -9]), -2)\n\n"
                "    def test_single_item(self):\n"
                "        self.assertEqual(find_max([7]), 7)\n\n"
                "    def test_empty_list_raises(self):\n"
                "        with self.assertRaises(ValueError):\n"
                "            find_max([])\n\n\n"
                'if __name__ == "__main__":\n'
                "    unittest.main()\n"
            ),
            how_to_run="Save the fixed code as solution.py\nSave the tests as test_solution.py in the same folder\npython -m unittest -v test_solution",
            covers=["Normal list of positive numbers", "A list of only negative numbers (the old 0 bug)", "A list with a single item", "An empty list raises ValueError"],
        ),
        "bigo": L.ComplexityResult(
            overall_time="O(n)", overall_space="O(1)",
            summary="One pass over the list with a couple of variables, so time grows in a straight line with the list and memory stays constant.",
            functions=[L.FunctionComplexity(name="find_max", time="O(n)", space="O(1)",
                                            reason="Each element is compared once; only 'biggest' is stored.",
                                            improvement="Already optimal: every element must be looked at at least once.")],
        ),
        "report": L.ReportCard(
            metrics=_metrics([6, 7, 5, 2, 2, 6], [
                "Short and easy to follow.", "find_max and biggest are clear names.", "One small function, but the logic is wrong.",
                "No empty-list handling, and the loop crashes.", "No classes; not needed at this size.", "Single pass is fine; the extra iteration is a bug."]),
            verdict="A good idea with two real bugs; easy to rescue.",
            priorities=["Fix the loop bound so it never reads past the end.", "Start from numbers[0] instead of 0.", "Raise a clear error for an empty list."],
        ),
    },
    "Java": {
        "oop": L.OOPResult(
            summary="Filtering is pulled behind a NumberFilter interface, so new rules can be added without touching Main.",
            classes=[
                L.ClassInfo(name="NumberFilter", kind="interface", responsibility="Describes apply(list) that returns the numbers to keep.", relationships=""),
                L.ClassInfo(name="RemoveEvens", kind="class", responsibility="Keeps only the odd numbers, without changing the input list.", relationships="implements NumberFilter"),
                L.ClassInfo(name="Main", kind="class", responsibility="Wires a filter to the data and prints the result.", relationships="uses NumberFilter"),
            ],
            concepts=[
                L.ConceptUse(concept="Abstraction", where="NumberFilter", why="Main depends on the interface, not on one rule."),
                L.ConceptUse(concept="Polymorphism", where="filter.apply()", why="Swap in RemoveOdds later and Main needs no change."),
                L.ConceptUse(concept="Encapsulation", where="RemoveEvens", why="The removal logic is hidden and never mutates the caller's list."),
            ],
            diagram="  <<interface>> NumberFilter\n  + apply(nums): List<Integer>\n            ^\n            .\n        RemoveEvens\n  + apply(nums)\n\n  Main --uses--> NumberFilter",
            refactored_code=(
                "import java.util.*;\n\n"
                "interface NumberFilter {\n"
                "    List<Integer> apply(List<Integer> nums);\n"
                "}\n\n"
                "class RemoveEvens implements NumberFilter {\n"
                "    @Override\n"
                "    public List<Integer> apply(List<Integer> nums) {\n"
                "        List<Integer> kept = new ArrayList<>(nums);\n"
                "        kept.removeIf(n -> n % 2 == 0);\n"
                "        return kept;\n"
                "    }\n"
                "}\n\n"
                "public class Main {\n"
                "    public static void main(String[] args) {\n"
                "        NumberFilter filter = new RemoveEvens();\n"
                "        System.out.println(filter.apply(Arrays.asList(1, 2, 3, 4, 5, 6)));\n"
                "        String name = null;\n"
                "        System.out.println(name == null ? 0 : name.length());\n"
                "    }\n"
                "}\n"
            ),
            notes="Both crashes are fixed along the way: no removal during iteration, and a null check before length().",
        ),
        "tests": L.UnitTestsResult(
            framework="Plain Java TestRunner (no libraries)",
            test_code=(
                "import java.util.*;\n\n"
                "public class TestRunner {\n"
                "    static int failed = 0;\n\n"
                "    static void check(String name, boolean ok) {\n"
                '        System.out.println((ok ? "PASS " : "FAIL ") + name);\n'
                "        if (!ok) failed++;\n"
                "    }\n\n"
                "    public static void main(String[] args) {\n"
                '        check("removes evens", Main.removeEvens(Arrays.asList(1, 2, 3, 4, 5, 6)).equals(Arrays.asList(1, 3, 5)));\n'
                '        check("all odd stays", Main.removeEvens(Arrays.asList(1, 3)).equals(Arrays.asList(1, 3)));\n'
                '        check("empty list", Main.removeEvens(new ArrayList<>()).isEmpty());\n'
                '        check("null length is 0", Main.safeLength(null) == 0);\n'
                '        check("normal length", Main.safeLength("abc") == 3);\n'
                "        System.exit(failed == 0 ? 0 : 1);\n"
                "    }\n"
                "}\n"
            ),
            how_to_run="Save the fixed code as Main.java\nSave the tests as TestRunner.java in the same folder\njavac Main.java TestRunner.java\njava TestRunner",
            covers=["Even numbers are removed", "A list with no even numbers is unchanged", "An empty list is fine", "safeLength handles null and normal strings"],
        ),
        "bigo": L.ComplexityResult(
            overall_time="O(n)", overall_space="O(n)",
            summary="Copying the list and removing evens each touch every element once. Nothing is nested.",
            functions=[
                L.FunctionComplexity(name="removeEvens", time="O(n)", space="O(n)", reason="Copies the list, then removeIf scans it once.", improvement="Stream the list and collect odds in one pass if you want to avoid the copy."),
                L.FunctionComplexity(name="safeLength", time="O(1)", space="O(1)", reason="One null check and a length call.", improvement=""),
            ],
        ),
        "report": L.ReportCard(
            metrics=_metrics([6, 6, 4, 2, 3, 5], [
                "Short, but everything lives in main.", "nums and name are okay; n and name could say more.", "No helper methods or classes.",
                "No null check and a crash on removal.", "Only one class; interfaces would help.", "ArrayList removal is O(n) each time, so the loop is O(n^2) if it worked."]),
            verdict="Two classic Java crashes in a small program; both are easy to fix.",
            priorities=["Replace the loop with removeIf.", "Guard against null before calling length().", "Move the logic into small methods you can test."],
        ),
    },
    "C": {
        "oop": L.OOPResult(
            summary="C has no classes, so the design uses a struct with functions that act as its methods, and the buffer details are hidden behind them.",
            classes=[
                L.ClassInfo(name="Visitor", kind="struct", responsibility="Holds the name and the score block together.", relationships=""),
                L.ClassInfo(name="visitor_create / visitor_destroy", kind="functions", responsibility="Allocate and free the struct, so cleanup cannot be forgotten.", relationships="operate on Visitor"),
            ],
            concepts=[
                L.ConceptUse(concept="Encapsulation", where="Visitor + its functions", why="Callers never touch the buffers or malloc directly."),
                L.ConceptUse(concept="Abstraction", where="visitor_create / visitor_destroy", why="One call creates a safe object; one call cleans it up."),
            ],
            diagram="  struct Visitor\n  - char name[8]\n  - int *scores\n\n  visitor_create(name) -> Visitor*\n  visitor_destroy(v)",
            refactored_code=(
                "#include <stdio.h>\n#include <stdlib.h>\n#include <string.h>\n\n"
                "typedef struct {\n    char name[8];\n    int *scores;\n} Visitor;\n\n"
                "Visitor *visitor_create(const char *name) {\n"
                "    Visitor *v = malloc(sizeof *v);\n"
                "    if (v == NULL) return NULL;\n"
                "    strncpy(v->name, name, sizeof v->name - 1);\n"
                "    v->name[sizeof v->name - 1] = '\\0';\n"
                "    v->scores = malloc(5 * sizeof(int));\n"
                "    if (v->scores == NULL) { free(v); return NULL; }\n"
                "    return v;\n"
                "}\n\n"
                "void visitor_destroy(Visitor *v) {\n"
                "    if (v == NULL) return;\n"
                "    free(v->scores);\n"
                "    free(v);\n"
                "}\n\n"
                "int main(void) {\n"
                "    char input[8];\n"
                '    printf("Name: ");\n'
                "    if (fgets(input, sizeof input, stdin) == NULL) return 1;\n"
                '    input[strcspn(input, "\\n")] = \'\\0\';\n'
                "    Visitor *v = visitor_create(input);\n"
                "    if (v == NULL) return 1;\n"
                "    v->scores[4] = 100;\n"
                '    printf("Hi %s\\n", v->name);\n'
                "    visitor_destroy(v);\n"
                "    return 0;\n"
                "}\n"
            ),
            notes="This is object-style C, not true OOP. All three memory bugs are fixed: bounded input, a block big enough for index 4, and a matching free.",
        ),
        "tests": L.UnitTestsResult(
            framework="assert.h (standard library)",
            test_code=(
                "#define TESTING\n"
                "#include <assert.h>\n"
                '#include "solution.c"\n\n'
                "int main(void) {\n"
                '    char a[] = "bob\\n";\n'
                "    trim_newline(a);\n"
                '    assert(strcmp(a, "bob") == 0);\n\n'
                '    char b[] = "alice";\n'
                "    trim_newline(b);\n"
                '    assert(strcmp(b, "alice") == 0);\n\n'
                '    char c[] = "\\n";\n'
                "    trim_newline(c);\n"
                "    assert(c[0] == '\\0');\n\n"
                '    puts("all tests passed");\n'
                "    return 0;\n"
                "}\n"
            ),
            how_to_run="Save the fixed code as solution.c\nSave the tests as test_solution.c in the same folder\ngcc test_solution.c -o test_solution\n./test_solution",
            covers=["A trailing newline is removed", "A string without a newline is unchanged", "A line with only a newline becomes empty"],
        ),
        "bigo": L.ComplexityResult(
            overall_time="O(1)", overall_space="O(1)",
            summary="Reads at most 7 characters and makes one small allocation, so time and space do not depend on any input size.",
            functions=[
                L.FunctionComplexity(name="main", time="O(1)", space="O(1)", reason="The buffer is fixed at 8 characters and the block is 5 ints.", improvement=""),
                L.FunctionComplexity(name="trim_newline", time="O(k)", space="O(1)", reason="strcspn scans the string once (k is at most 7 here).", improvement=""),
            ],
        ),
        "report": L.ReportCard(
            metrics=_metrics([6, 5, 4, 1, 2, 7], [
                "Short and readable.", "name and scores are fine; main does everything.", "Everything is in main.",
                "gets() overflow, unchecked malloc and no free.", "Not applicable in C beyond a struct.", "Constant work; nothing to optimise."]),
            verdict="Three memory-safety bugs in eleven lines. Small to fix, serious if left.",
            priorities=["Replace gets() with fgets.", "Allocate enough memory and check malloc.", "Always free what you allocate."],
        ),
    },
    "C++": {
        "oop": L.OOPResult(
            summary="Summing becomes a small class with a private vector, so the data and the rule for summing and dividing live together.",
            classes=[
                L.ClassInfo(name="Stats", kind="class", responsibility="Owns the numbers and offers sum() and average().", relationships=""),
            ],
            concepts=[
                L.ConceptUse(concept="Encapsulation", where="Stats::data_", why="The vector is private; outside code can only add numbers or ask for results."),
                L.ConceptUse(concept="Abstraction", where="Stats::average()", why="The zero-size check lives inside, so callers cannot forget it."),
            ],
            diagram="  class Stats\n  - data_ : vector<int>\n  + add(int)\n  + sum() const : int\n  + average() const : double",
            refactored_code=(
                "#include <iostream>\n#include <vector>\n\n"
                "class Stats {\n"
                "public:\n"
                "    explicit Stats(std::vector<int> data) : data_(std::move(data)) {}\n"
                "    int sum() const {\n"
                "        int total = 0;\n"
                "        for (int x : data_) total += x;\n"
                "        return total;\n"
                "    }\n"
                "    double average() const {\n"
                "        if (data_.empty()) return 0.0;\n"
                "        return static_cast<double>(sum()) / data_.size();\n"
                "    }\n"
                "private:\n"
                "    std::vector<int> data_;\n"
                "};\n\n"
                "int main() {\n"
                "    Stats s({1, 2, 3});\n"
                "    std::cout << s.sum() << \" \" << s.average() << std::endl;\n"
                "}\n"
            ),
            notes="The refactor replaces the divide-by-(size-3) with a safe average, so behaviour changes on purpose: the original always divided by zero.",
        ),
        "tests": L.UnitTestsResult(
            framework="assert.h (standard library)",
            test_code=(
                "#define TESTING\n"
                "#include <cassert>\n"
                '#include "solution.cpp"\n\n'
                "int main() {\n"
                "    assert(sum({1, 2, 3}) == 6);\n"
                "    assert(sum({}) == 0);\n"
                "    assert(sum({-1, 1}) == 0);\n"
                "    assert(sum({5}) == 5);\n"
                '    std::cout << "all tests passed" << std::endl;\n'
                "    return 0;\n"
                "}\n"
            ),
            how_to_run="Save the fixed code as solution.cpp\nSave the tests as test_solution.cpp in the same folder\ng++ test_solution.cpp -o test_solution\n./test_solution",
            covers=["A normal list", "An empty vector sums to 0 (checks the initialised total)", "Positive and negative numbers cancel", "A single element"],
        ),
        "bigo": L.ComplexityResult(
            overall_time="O(n)", overall_space="O(1)",
            summary="Summing visits each element once; the fixed version no longer copies the vector.",
            functions=[L.FunctionComplexity(name="sum", time="O(n)", space="O(1)",
                                            reason="One pass over the vector. The original copy made it O(n) extra space; passing by const reference removes that.",
                                            improvement="std::accumulate says the same thing in one line.")],
        ),
        "report": L.ReportCard(
            metrics=_metrics([6, 6, 5, 2, 3, 4], [
                "Compact and easy to scan.", "sum, total and data are clear.", "A helper function plus main is a fine shape.",
                "Uninitialised variable and a division by zero.", "Plain functions only; a small class could own the data.", "Vector copied by value on each call."]),
            verdict="Good structure with three well-known C++ traps; the fixes are short.",
            priorities=["Initialise total to 0.", "Pass the vector by const reference.", "Check the divisor before dividing."],
        ),
    },
    "Clean": {
        "oop": L.OOPResult(
            summary="The function is wrapped in a small checker class so the normalising rule can be reused and extended.",
            classes=[L.ClassInfo(name="PalindromeChecker", kind="class", responsibility="Normalises text and tells whether it reads the same both ways.", relationships="")],
            concepts=[L.ConceptUse(concept="Encapsulation", where="PalindromeChecker._normalise", why="The cleaning rule is private and can change without breaking callers.")],
            diagram="  class PalindromeChecker\n  - _normalise(text) : list[str]\n  + check(text) : bool",
            refactored_code=(
                "class PalindromeChecker:\n"
                "    def _normalise(self, text: str) -> list:\n"
                "        return [ch.lower() for ch in text if ch.isalnum()]\n\n"
                "    def check(self, text: str) -> bool:\n"
                '        """True if text reads the same forwards and backwards, ignoring case and punctuation."""\n'
                "        cleaned = self._normalise(text)\n"
                "        return cleaned == cleaned[::-1]\n\n\n"
                'print(PalindromeChecker().check("A man, a plan, a canal: Panama"))\n'
            ),
            notes="The original is already clean; the class is only worth it if you plan more text checks.",
        ),
        "tests": L.UnitTestsResult(
            framework="unittest (standard library)",
            test_code=(
                "import unittest\n"
                "from solution import is_palindrome\n\n\n"
                "class PalindromeTests(unittest.TestCase):\n"
                "    def test_simple(self):\n"
                '        self.assertTrue(is_palindrome("level"))\n\n'
                "    def test_ignores_case_and_punctuation(self):\n"
                '        self.assertTrue(is_palindrome("A man, a plan, a canal: Panama"))\n\n'
                "    def test_not_palindrome(self):\n"
                '        self.assertFalse(is_palindrome("roast"))\n\n'
                "    def test_empty_string(self):\n"
                '        self.assertTrue(is_palindrome(""))\n\n\n'
                'if __name__ == "__main__":\n'
                "    unittest.main()\n"
            ),
            how_to_run="Save the code as solution.py\nSave the tests as test_solution.py in the same folder\npython -m unittest -v test_solution",
            covers=["A plain palindrome", "Case and punctuation are ignored", "A word that is not a palindrome", "The empty string"],
        ),
        "bigo": L.ComplexityResult(
            overall_time="O(n)", overall_space="O(n)",
            summary="Building the cleaned list and reversing it each touch every character once.",
            functions=[L.FunctionComplexity(name="is_palindrome", time="O(n)", space="O(n)",
                                            reason="The cleaned list and its reversed copy are both n long.",
                                            improvement="Two pointers moving inward would use O(1) extra space.")],
        ),
        "report": L.ReportCard(
            metrics=_metrics([9, 9, 8, 7, 5, 8], [
                "Very easy to read.", "Name and variable are exact.", "Small, focused function.",
                "Non-string input would raise an error; fine for typed code.", "No class, and none is needed.", "Linear time; extra memory is acceptable."]),
            verdict="Clean, documented and correct. Nothing serious to fix.",
            priorities=["Optionally add tests.", "Optionally use two pointers to save memory.", "Keep the docstring style everywhere."],
        ),
    },
}


# --------------------------------------------------------------------------
# Interview mode (viva questions)
# --------------------------------------------------------------------------
def _q(question, level, why, answer, follow=""):
    return L.InterviewQuestion(question=question, level=level, why_asked=why, model_answer=answer, follow_up=follow)


_TIPS = [
    "Answer in one clear sentence first, then add detail.",
    "Point at the exact line or variable you are talking about.",
    "If you are unsure, say what you would test or check.",
]

_INTERVIEW = {
    "Python": L.InterviewResult(
        intro="A small function that should return the largest number in a list.",
        questions=[
            _q("What does find_max do, and what does it return?", "Basic", "Checks that you understand your own function.",
               "It walks through the list, remembers the biggest value seen so far in the variable biggest, and returns it at the end."),
            _q("Why does the loop in find_max crash?", "Basic", "Tests whether you can spot an off-by-one error.",
               "The loop uses range(len(numbers) + 1), so on the last pass the index equals the length and numbers[i] raises an IndexError. The range should stop at len(numbers), or better, loop over the list directly.",
               "How would you rewrite the loop so this mistake cannot happen?"),
            _q("What does find_max return for [-5, -2, -9], and why is that wrong?", "Intermediate", "Looks for the hidden logic bug behind the crash.",
               "It would return 0, because biggest starts at 0 and no negative number is bigger than that. The correct answer is -2, so biggest should start from numbers[0].",
               "What other starting value could cause the same kind of bug?"),
            _q("How should the function behave for an empty list?", "Intermediate", "Tests edge-case thinking.",
               "There is no maximum of nothing, so the clearest choice is to raise a ValueError with a helpful message. Returning 0 or None silently would hide the mistake from the caller.",
               "When might returning None be better than raising an error?"),
            _q("What is the time and space complexity of the fixed version?", "Advanced", "Checks that you can analyse your own code.",
               "Time is O(n) because every element is compared once, and space is O(1) because only the variable biggest is stored. It cannot be faster than O(n), since every element must be looked at.",
               "How does that compare with sorting the list first?"),
            _q("Why not just use Python's built-in max()?", "Advanced", "Tests judgement about when to reinvent things.",
               "In real code I would use max(), which is tested and fast. Writing it by hand is useful for learning loops and edge cases, and I would say so honestly in the project.",
               "How would you test your own version against max()?"),
        ], tips=_TIPS),
    "Java": L.InterviewResult(
        intro="A Java program that removes even numbers from a list and then reads the length of a null string.",
        questions=[
            _q("What is the program trying to do with the nums list?", "Basic", "Checks you understand the goal of the loop.",
               "It loops over the numbers 1 to 6 and tries to remove the even ones, so only 1, 3 and 5 should remain."),
            _q("Why does nums.remove(n) inside the for-each loop fail?", "Basic", "Tests knowledge of iteration rules.",
               "The for-each loop uses an iterator, and changing the list while it iterates makes the iterator detect the change and throw a ConcurrentModificationException. A safe way is nums.removeIf(n -> n % 2 == 0).",
               "What if you needed to remove inside a classic for loop?"),
            _q("Why is remove(n) with an Integer risky?", "Intermediate", "Tests understanding of method overloading.",
               "List has remove(int index) and remove(Object o). With a primitive int it removes by position, with an Integer object it removes by value, and it is easy to call the wrong one without noticing.",
               "How would you force the by-value version?"),
            _q("What happens at name.length() and why?", "Intermediate", "Looks for null handling knowledge.",
               "name was set to null, so calling length() on it throws a NullPointerException. I would check name == null first, or use Optional or an empty string as a default.",
               "What does Objects.requireNonNull do?"),
            _q("What is the complexity of removing from an ArrayList in a loop?", "Advanced", "Pushes beyond the obvious bug into performance.",
               "Each remove shifts every later element, so removing k items from n costs O(n * k), up to O(n squared). removeIf does it in one pass, which is O(n).",
               "Would a LinkedList change the answer?"),
            _q("How could you structure this so it is easy to test?", "Advanced", "Checks design thinking.",
               "Move the logic into small static methods such as removeEvens(List) and safeLength(String), so a test can call them directly without running main.",
               "What would you assert in the first test?"),
        ], tips=_TIPS),
    "C": L.InterviewResult(
        intro="A C program that reads a name, allocates a score array and prints a greeting, with three memory-safety bugs.",
        questions=[
            _q("What does the program do from start to finish?", "Basic", "Checks you can walk through your own code.",
               "It declares an 8 character buffer, reads a name, allocates memory for scores, writes a value into it and prints a greeting."),
            _q("Why is gets(name) dangerous?", "Basic", "Classic C security question.",
               "gets cannot be told how much to read, so a name longer than 7 characters plus the terminator overflows the 8 byte buffer and overwrites memory next to it. It was removed from the C standard, and fgets with sizeof name is the safe replacement.",
               "What does fgets leave at the end of the string that gets did not?"),
            _q("What is wrong with malloc(4 * sizeof(int)) followed by scores[4] = 100?", "Intermediate", "Tests array indexing and heap knowledge.",
               "Four ints give valid indexes 0 to 3, so scores[4] writes one element past the block, which is a heap buffer overflow. The block needs 5 ints, or the write must go to index 3.",
               "What tool could catch this automatically?"),
            _q("Why should you check the return value of malloc?", "Intermediate", "Looks for defensive programming.",
               "malloc returns NULL if it cannot allocate, and writing through NULL crashes the program. A check lets you exit cleanly with an error instead.",
               "What does the program leak if it exits early?"),
            _q("What is a memory leak and where does it happen here?", "Advanced", "Tests resource management understanding.",
               "A leak is memory that was allocated and never freed. scores is never passed to free, so the block stays allocated until the process ends. Every allocation needs a matching free.",
               "How does Valgrind show this?"),
            _q("How would you make this program safer overall?", "Advanced", "Open design and security question.",
               "Use fgets, size the allocation correctly, check malloc, free the memory, and move the logic into small functions that can be tested. Compiling with -Wall -Wextra and running AddressSanitizer would catch the rest.",
               "What does AddressSanitizer actually do?"),
        ], tips=_TIPS),
    "C++": L.InterviewResult(
        intro="A C++ program that sums a vector and then divides the sum by data.size() - 3.",
        questions=[
            _q("What does the sum function do?", "Basic", "Checks you understand your own function.",
               "It loops over the vector with an index and adds every element into total, which it then returns."),
            _q("Why is int total; a problem?", "Basic", "Tests knowledge of uninitialised variables.",
               "A local int is not set to zero automatically, so it starts with whatever garbage was in memory. Reading it is undefined behaviour, and the fix is int total = 0.",
               "Which compiler flag would warn you about this?"),
            _q("What is the cost of taking the vector by value?", "Intermediate", "Tests understanding of copies.",
               "Every call copies the whole vector, which costs O(n) time and memory. Passing const std::vector<int>& avoids the copy and also promises not to change it.",
               "When would passing by value actually be right?"),
            _q("What happens at sum(data) / (data.size() - 3)?", "Intermediate", "Spots the runtime crash.",
               "data has 3 elements, so size() - 3 is 0 and the division by zero is undefined behaviour. data.size() is unsigned, so even a smaller size would wrap around to a huge number.",
               "Why does unsigned arithmetic make this worse?"),
            _q("How would you simplify the loop in sum?", "Advanced", "Tests modern C++ knowledge.",
               "A range-based for loop, for (int x : v) total += x, or std::accumulate(v.begin(), v.end(), 0). Both are shorter and cannot go out of bounds.",
               "What type would you pass as accumulate's initial value for large numbers?"),
            _q("How would you test this program?", "Advanced", "Checks design for testability.",
               "Keep sum as a separate function and move main behind a guard such as #ifndef TESTING, so a test file can include the code and use assert on cases like an empty vector and a normal list.",
               "What edge cases would you add?"),
        ], tips=_TIPS),
    "Clean": L.InterviewResult(
        intro="A short Python function that checks whether a piece of text is a palindrome.",
        questions=[
            _q("What does is_palindrome do?", "Basic", "Checks you understand the function.",
               "It removes everything that is not a letter or digit, lowercases the rest and checks whether the result reads the same forwards and backwards."),
            _q("Why does it clean the text first?", "Basic", "Tests understanding of the requirements.",
               "Phrases like 'A man, a plan, a canal: Panama' only read the same once case, spaces and punctuation are ignored. Cleaning first makes the comparison simple."),
            _q("What does cleaned[::-1] do?", "Intermediate", "Tests Python slicing knowledge.",
               "It creates a reversed copy of the list using a slice with step -1, so comparing it with the original tells us whether it is a palindrome."),
            _q("What is the time and space complexity?", "Intermediate", "Checks complexity analysis.",
               "Time is O(n), since building the list and reversing it each touch every character once. Space is O(n) for the cleaned list and its reversed copy.",
               "How would you reduce the space?"),
            _q("How could you do it with O(1) extra space?", "Advanced", "Tests algorithm design.",
               "Use two pointers, one from each end, skipping non-alphanumeric characters and comparing the rest as they move inwards, without building new lists.",
               "What are the edge cases for the pointers?"),
            _q("What would you test?", "Advanced", "Checks test design.",
               "A simple palindrome, a phrase with mixed case and punctuation, a non-palindrome, the empty string and a single character.",
               "Would you test non-string input?"),
        ], tips=_TIPS),
}
for _name, _data in _INTERVIEW.items():
    _LAB[_name]["interview"] = _data


def demo_lab(name: str, kind: str):
    return _LAB.get(name, {}).get(kind)

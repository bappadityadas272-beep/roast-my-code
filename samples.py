"""Demo snippets for the sample buttons: one buggy program per language and a
clean one. None of these are the few-shot examples used in prompts.py."""

SAMPLES = {
    "Python": (
        "def find_max(numbers):\n"
        "    biggest = 0\n"
        "    for i in range(len(numbers) + 1):\n"
        "        if numbers[i] > biggest:\n"
        "            biggest = numbers[i]\n"
        "    return biggest\n"
        "\n"
        "print(find_max([-5, -2, -9]))\n"
    ),
    "Java": (
        "import java.util.*;\n"
        "\n"
        "public class Main {\n"
        "    public static void main(String[] args) {\n"
        "        List<Integer> nums = new ArrayList<>(Arrays.asList(1, 2, 3, 4, 5, 6));\n"
        "        for (Integer n : nums) {\n"
        "            if (n % 2 == 0) {\n"
        "                nums.remove(n);\n"
        "            }\n"
        "        }\n"
        "        System.out.println(nums);\n"
        "        String name = null;\n"
        "        System.out.println(name.length());\n"
        "    }\n"
        "}\n"
    ),
    "C": (
        "#include <stdio.h>\n"
        "#include <stdlib.h>\n"
        "\n"
        "int main() {\n"
        "    char name[8];\n"
        '    printf("Name: ");\n'
        "    gets(name);\n"
        "    int *scores = malloc(4 * sizeof(int));\n"
        "    scores[4] = 100;\n"
        '    printf("Hi %s\\n", name);\n'
        "    return 0;\n"
        "}\n"
    ),
    "C++": (
        "#include <iostream>\n"
        "#include <vector>\n"
        "\n"
        "int sum(std::vector<int> v) {\n"
        "    int total;\n"
        "    for (size_t i = 0; i < v.size(); i++) total += v[i];\n"
        "    return total;\n"
        "}\n"
        "\n"
        "int main() {\n"
        "    std::vector<int> data = {1, 2, 3};\n"
        "    std::cout << sum(data) / (data.size() - 3) << std::endl;\n"
        "}\n"
    ),
    "Clean": (
        "def is_palindrome(text: str) -> bool:\n"
        '    """Return True if text reads the same forwards and backwards,\n'
        '    ignoring case and punctuation."""\n'
        "    cleaned = [ch.lower() for ch in text if ch.isalnum()]\n"
        "    return cleaned == cleaned[::-1]\n"
    ),
}
